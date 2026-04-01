import mne
raw = mne.io.read_raw_fif(r"C:\Users\Utilisateur\Documents\CRNL\app_eeg\Analysis\data_preproc\002_preproc.fif", preload=True)
print("first_samp:", raw.first_samp)
print("orig_time:", raw.annotations.orig_time)
if len(raw.annotations) > 0:
    print("first annot onset:", raw.annotations[0]['onset'])
