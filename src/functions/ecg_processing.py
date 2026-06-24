# -*- coding: utf-8 -*-
import os
import re
from collections import defaultdict

import mne
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline

############################################
# CONFIGURATION
############################################

SITU_MAP = {
    65: 'Music',
    66: 'Noise',
    67: 'Rest after Music',
    68: 'Rest after noise',
    69: 'Interact music',
    70: 'Interact noise'
}
KEEP_IDS = list(SITU_MAP.keys())
ECG_SFREQ = 100.0  # fréquence à laquelle on resample le RAW plus bas

############################################
# PARSEUR NOM SUJET (robuste aux espaces)
############################################

def parse_subject(name: str):
    base = os.path.splitext(name)[0]
    base = re.sub(r'\s+', '', base)  # enlève espaces parasites

    # Témoins: 3 lettres + 0-3 chiffres
    m_alpha = re.match(r'^([A-Za-z]{3})(\d{0,3})(?:_|$)', base)
    if m_alpha:
        prefix = m_alpha.group(1).upper()
        digits = m_alpha.group(2) or ''
        return {'type': 'alpha', 'prefix': prefix, 'subject_id': f"{prefix}{digits}", 'session': None, 'base': base}

    # Numériques: 3 chiffres, session optionnelle
    m_num = re.match(r'^(\d{3})(?:_(\d))?(?:_|$)', base)
    if m_num:
        code, sess = m_num.group(1), m_num.group(2)
        return {'type': 'numeric', 'code': code, 'subject_id': code, 'session': sess, 'base': base}

    # Fallback
    parts = base.split('_')
    code = parts[0]
    sess = parts[1] if len(parts) > 1 and parts[1].isdigit() else None
    return {'type': 'unknown', 'subject_id': code, 'session': sess, 'base': base}

############################################
# CHARGEMENT STIMDICT DIRECTEMENT DEPUIS FIF
############################################

def extract_translate_dict_from_fif(raw):
    """
    Extrait le dictionnaire de traduction (event_id) contenu dans le fichier FIF.
    MNE sauvegarde parfois event_id dans raw.event_id ou on l'obtient des annotations.
    """
    if hasattr(raw, 'event_id') and raw.event_id is not None and len(raw.event_id) > 0:
        return raw.event_id
    
    # Tentative d'extraire depuis les annotations
    try:
        _, td = mne.events_from_annotations(raw, verbose=False)
        return td
    except Exception:
        pass
    
    print("[ERROR] Impossible de trouver l'event_id dans le fichier FIF.")
    return None

############################################
# EVENTS: TROUVE, REMAP, NETTOIE
############################################

def remove_consecutive_noise_first(new_events, subname):
    """
    Pour CR004_1 et CR005_2 :
    - si deux 'Noise' (66) se suivent, supprime le premier de la paire.
    - Fallbacks si aucune paire détectée :
        * CR004_1 : supprime le tout premier event
        * CR005_2 : supprime l'event n°12 (index 11)
    """
    if subname not in ('CR004_1', 'CR005_2'):
        return new_events

    ids = new_events[:, 2]
    to_drop = []
    for i in range(len(ids) - 1):
        if ids[i] == 66 and ids[i + 1] == 66:
            to_drop.append(i)

    if to_drop:
        print(f"⚠️ {subname}: suppression des premiers 'Noise' dans {len(to_drop)} paire(s) → indices {to_drop}")
        return np.delete(new_events, to_drop, axis=0)

    if subname == 'CR004_1' and new_events.shape[0] > 0:
        print("⚠️ CR004_1: fallback → suppression du tout premier event.")
        return np.delete(new_events, 0, axis=0)

    if subname == 'CR005_2' and new_events.shape[0] > 11:
        print("⚠️ CR005_2: fallback → suppression de l'event n°12 (index 11).")
        return np.delete(new_events, 11, axis=0)

    return new_events

def get_epochs_events(raw: mne.io.BaseRaw, translate_dict: dict, SubName: str):
    # Les fichiers FIF peuvent avoir leurs événements dans les annotations MNE, ou dans un canal STI 014
    # On essaye l'approche de l'ancien code d'abord, sinon `events_from_annotations`
    
    events = None
    try:
        events = mne.find_events(raw, stim_channel='STI 014', verbose=False)
    except Exception:
        pass
        
    if events is None or len(events) == 0:
        try:
            events, _ = mne.events_from_annotations(raw, verbose=False)
        except Exception:
            pass

    if events is None or len(events) == 0:
        print("[ERROR] Aucun événement trouvé dans le fichier.")
        return None

    if translate_dict is None:
        return None

    # remap rc(label) -> ids numériques
    inv = {}
    for k, v in translate_dict.items():
        digits = ''.join(ch for ch in str(k) if ch.isdigit())
        if digits:
            inv[v] = int(digits)

    new_events = events.copy()
    for i, (_, _, rc) in enumerate(events):
        if rc in inv:
            new_events[i, 2] = inv[rc]

    # nettoyage spécifique demandé
    new_events = remove_consecutive_noise_first(new_events, SubName)

    # garder uniquement nos conditions
    rel = new_events[np.isin(new_events[:, 2], KEEP_IDS)]
    return rel if len(rel) > 0 else None

############################################
# ARTEFACTS & INTERPOLATION (par subject, event_id, rep)
############################################

def detect_artifacts(df: pd.DataFrame):
    df = df.copy()
    df['is_artifact'] = False
    cond = (df['rr_interval_sec'] > 2.0) | (df['rr_interval_sec'] < 0.35)
    df.loc[cond, 'is_artifact'] = True

    def mark_std(g):
        m, s = g['rr_interval_sec'].mean(), g['rr_interval_sec'].std()
        if pd.notnull(s) and s > 0:
            out = (g['rr_interval_sec'] < m - 3*s) | (g['rr_interval_sec'] > m + 3*s)
            g.loc[out, 'is_artifact'] = True
        return g

    return df.groupby(['subject', 'event_id', 'rep'], sort=False, group_keys=False).apply(mark_std)

def interpolate_artifacts(df: pd.DataFrame):
    df = df.copy()
    def interp_grp(g):
        non_art = g.index[~g['is_artifact']]
        art = g.index[g['is_artifact']]
        if len(non_art) > 2 and len(art) > 0:
            for col in ['rr_interval_sec', 'heart_rate_bpm', 'r_peak_sample', 'r_peak_time_sec']:
                spline = UnivariateSpline(non_art, g.loc[non_art, col], s=0, k=2)
                g.loc[art, col] = spline(art)
        return g
    return df.groupby(['subject', 'event_id', 'rep'], sort=False, group_keys=False).apply(interp_grp)

############################################
# RESAMPLING 1 Hz (0..59 s / répétition, ordre préservé)
############################################

def resample_corrected_1hz(input_csv, output_csv):
    df = pd.read_csv(input_csv)
    if df.empty:
        pd.DataFrame().to_csv(output_csv, index=False); print("[INFO] Vide.")
        return

    # Garanties colonnes
    if 'Situation' not in df.columns and 'event_id' in df.columns:
        df['Situation'] = df['event_id'].map(SITU_MAP)
    if 'rep' not in df.columns:
        df = df.sort_index()
        df['rep'] = df.groupby(['subject','event_id'], sort=False)['r_peak_sample'] \
                      .apply(lambda s: (s.diff().fillna(np.inf) <= 0).cumsum() - 1).values
    if 'r_peak_time_sec' not in df.columns and 'r_peak_sample' in df.columns:
        df['r_peak_time_sec'] = df['r_peak_sample'] / ECG_SFREQ

    secs = np.arange(60, dtype=float)

    def _make_strict(x, y):
        if len(x) == 0:
            return x, y
        order = np.argsort(x, kind='mergesort')
        x, y = x[order], y[order]
        uniq_x, agg_y = [x[0]], [y[0]]
        for xi, yi in zip(x[1:], y[1:]):
            if np.isclose(xi, uniq_x[-1]):
                agg_y[-1] = (agg_y[-1] + yi) / 2.0
            else:
                uniq_x.append(xi); agg_y.append(yi)
        return np.asarray(uniq_x, float), np.asarray(agg_y, float)

    def _lin_extrap(x, xp, fp):
        if len(xp) == 0:
            return np.full_like(x, np.nan, dtype=float)
        if len(xp) == 1:
            return np.full_like(x, fp[0], dtype=float)
        y = np.interp(x, xp, fp)
        mL = (fp[1] - fp[0]) / (xp[1] - xp[0]) if xp[1] != xp[0] else 0.0
        left = x < xp[0]
        if left.any():
            y[left] = fp[0] + mL * (x[left] - xp[0])
        mR = (fp[-1] - fp[-2]) / (xp[-1] - xp[-2]) if xp[-1] != xp[-2] else 0.0
        right = x > xp[-1]
        if right.any():
            y[right] = fp[-1] + mR * (x[right] - xp[-1])
        return y

    out_rows = []
    for (subj, eid, rep), g in df.groupby(['subject','event_id','rep'], sort=False):
        g = g.sort_values('r_peak_time_sec', kind='mergesort')
        t = g['r_peak_time_sec'].to_numpy(dtype=float)
        hr = g['heart_rate_bpm'].to_numpy(dtype=float)
        rr = g['rr_interval_sec'].to_numpy(dtype=float)
        situ = g['Situation'].iloc[0] if 'Situation' in g.columns else str(eid)

        mask = np.isfinite(t) & np.isfinite(hr) & np.isfinite(rr)
        t, hr, rr = t[mask], hr[mask], rr[mask]
        t, hr = _make_strict(t, hr)
        t, rr = _make_strict(t, rr)

        if len(t) > 0:
            t = np.clip(t, 0.0, 59.999)

        hr_s = _lin_extrap(secs, t, hr)
        rr_s = _lin_extrap(secs, t, rr)

        for s in range(60):
            out_rows.append({
                'subject': subj,
                'event_id': eid,
                'Situation': situ,
                'rep': rep,
                'sec': s,
                'heart_rate_bpm': float(hr_s[s]),
                'rr_interval_sec': float(rr_s[s]),
            })

    resamp = pd.DataFrame(out_rows)
    resamp.to_csv(output_csv, index=False)
    print(f"[OK] Resampled ECG (1Hz, interpolation linéaire globale) saved to {output_csv}")


############################################
# MAIN PIPELINE
############################################

def process_file(fif_path: str):
    print(f"\n=== Traitement de {fif_path} ===")
    
    # 1. Vérifications de base
    if not os.path.exists(fif_path):
        print(f"[ERROR] Le fichier {fif_path} n'existe pas.")
        return
        
    output_dir = os.path.dirname(os.path.abspath(__file__))
    subj = os.path.basename(fif_path)
    base_name = os.path.splitext(subj)[0]
    base_clean = re.sub(r'\s+', '', base_name)
    
    # Utilisation du parseur pour SubName
    info = parse_subject(base_clean)
    SubName = info.get('subject_id') or base_clean
    if info.get('session'):
        SubName += f"_{info['session']}"

    # 2. Chargement du fichier
    try:
        raw = mne.io.read_raw_fif(fif_path, preload=True, verbose=False)
    except Exception as e:
        print(f"[ERROR] Échec de la lecture du fichier FIF: {e}")
        return

    raw.resample(ECG_SFREQ, verbose=False)

    # 3. Extraction translation dictionary et events
    td = extract_translate_dict_from_fif(raw)
    if td is None:
        print("[INFO] translate_dict est vide. Essayez de vérifier les événements ou le nom de ficher.")
    
    evs = get_epochs_events(raw, td, SubName)
    if evs is None:
        print("[INFO] Aucun event pertinent trouvé, on arrête le traitement pour ce fichier.")
        return

    # 4. Comptage rep et calcul ECG
    rep_count = defaultdict(int)
    dfs = []
    
    for start, _, eid in evs:
        rep = rep_count[eid]
        rep_count[eid] += 1

        tmin = start / raw.info['sfreq']
        tmax = tmin + 60.0

        seg = raw.copy().crop(tmin=tmin, tmax=tmax)

        picks = mne.pick_types(seg.info, ecg=True)
        if len(picks) == 0:
            print("[WARN] Aucun canal ECG détecté, essai avec nom 'ECG'")
            try:
                _ = seg.get_data(picks='ECG')
                ch_ecg = 'ECG'
            except Exception:
                print("[ERROR] Pas de canal ECG dans ce segment → segment ignoré")
                continue
        else:
            ch_ecg = seg.info['ch_names'][picks[0]]

        seg.filter(1., 49., picks=[ch_ecg], verbose=False)
        ecgev, _, _ = mne.preprocessing.find_ecg_events(seg, ch_name=ch_ecg, verbose=False)
        if len(ecgev) < 2:
            continue

        r_samp_rel = ecgev[:, 0] - seg.first_samp
        r_times_rel = r_samp_rel / seg.info['sfreq']
        rr = np.diff(ecgev[:, 0]) / seg.info['sfreq']
        hr = 60.0 / rr

        df = pd.DataFrame({
            'subject': SubName,
            'event_id': eid,
            'Situation': SITU_MAP.get(eid, str(eid)),
            'rep': rep,
            'r_peak_sample': r_samp_rel[1:],
            'r_peak_time_sec': r_times_rel[1:],
            'rr_interval_sec': rr,
            'heart_rate_bpm': hr
        })
        dfs.append(df)

    if not dfs:
        print("[INFO] Rien à sauvegarder (aucune métrique ECG extraite).")
        return

    # 5. Concaténer et sauvegarder les Raw Metrics
    df_subj = pd.concat(dfs, ignore_index=True)
    df_subj.dropna(subset=['rr_interval_sec'], inplace=True)
    
    out_metrics = os.path.join(output_dir, f"{base_name}_all_ECG_metrics.csv")
    df_subj.to_csv(out_metrics, index=False)
    print(f"[OK] Sauvegardé Raw Metrics : {out_metrics}")

    # 6. Artefacts et Interpolation (Corrected)
    c = detect_artifacts(df_subj)
    c = interpolate_artifacts(c)
    out_corrected = os.path.join(output_dir, f"{base_name}_ECG_corrected.csv")
    c.to_csv(out_corrected, index=False)
    print(f"[OK] Corrected ECG saved to {out_corrected}")

    # 7. Moyennes et Écart-Types (Averaged)
    agg = (
        c
        .groupby(['Situation', 'subject'])
        .agg(
            rr_interval_sec_mean=('rr_interval_sec', 'mean'),
            rr_interval_sec_std =('rr_interval_sec', 'std'),
            heart_rate_bpm_mean =('heart_rate_bpm', 'mean')
        )
        .reset_index()
    )
    out_averaged = os.path.join(output_dir, f"{base_name}_averaged_ECG_data.csv")
    agg.to_csv(out_averaged, index=False)
    print(f"[OK] Averaged ECG data saved to {out_averaged}")

    # 8. Resampling 1 Hz
    out_resampled = os.path.join(output_dir, f"{base_name}_ECG_resampled.csv")
    resample_corrected_1hz(out_corrected, out_resampled)
    
    print("\n=== Extraction et Traitement terminés avec succès ===")


if __name__ == '__main__':
    # Entrée utilisateur : chemin du fichier .fif
    # L'utilisateur met le chemin en input, les fichiers seront sauvés à la racine de ce fichier python
    file_path = input("Veuillez entrer le chemin complet du fichier .fif à traiter :\n> ").strip()
    
    # Enlève les guillemets éventuels autour du chemin
    if file_path.startswith('"') and file_path.endswith('"'):
        file_path = file_path[1:-1]
    elif file_path.startswith("'") and file_path.endswith("'"):
        file_path = file_path[1:-1]
        
    process_file(file_path)
