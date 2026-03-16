
# EEG Configuration

# Mapping of channel types
MAPPING_TYPE = {'DI75': 'misc', 'DI77': 'misc', 'DI79': 'misc',
  'DI65': 'misc', 'DI67': 'misc', 'DI69': 'misc', 'DI66': 'misc', 'DI68': 'misc',
  'DI70': 'misc', 'STI 014': 'stim', 'ECG': 'ecg', 'EMG': 'emg'}

MAPPING_TYPE_CHE = {'D255': 'misc', 'DIN4': 'misc', 'DI75': 'misc', 'DI77': 'misc', 'DI79': 'misc',
  'DI65': 'misc', 'DI67': 'misc', 'DI69': 'misc', 'DI66': 'misc', 'DI68': 'misc',
  'DI70': 'misc', 'STI 014': 'stim', 'ECG': 'ecg', 'EMG': 'emg'}

MAPPING_TYPE_TAI = {
  'DI65': 'misc', 'DI67': 'misc', 'DI69': 'misc', 'DI66': 'misc', 'DI68': 'misc',
  'DI70': 'misc', 'STI 014': 'stim', 'ECG': 'ecg', 'EMG': 'emg'}


DEFAULT_TRIGGERS = ['DI65', 'DI66', 'DI67', 'DI68', 'DI69', 'DI70', 'STI 014']

# Preprocessing defaults
DEFAULT_CHAN_PSD_PLOT = ['E15','E11', 'E55', 'E62','E75', 'E108', 'E45', 'E122', 'E33']
DEFAULT_CHAN_MISC = ['E125','E126','E127','E128', 'E119', 'E48', 'EMG']
DEFAULT_BADS = ['VREF']
SFREQ = 200

# Channel names for montage (EGI 128)
EEG_CHAN_NAMES = ['E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10',
                'E11', 'E12', 'E13', 'E14', 'E15', 'E16', 'E17', 'E18', 'E19', 'E20',
                'E21', 'E22', 'E23', 'E24', 'E25', 'E26', 'E27', 'E28', 'E29', 'E30',
                'E31', 'E32', 'E33', 'E34', 'E35', 'E36', 'E37', 'E38', 'E39', 'E40',
                'E41', 'E42', 'E43', 'E44', 'E45', 'E46', 'E47', 'E48', 'E49', 'E50',
                'E51', 'E52', 'E53', 'E54', 'E55', 'E56', 'E57', 'E58', 'E59', 'E60',
                'E61', 'E62', 'E63', 'E64', 'E65', 'E66', 'E67', 'E68', 'E69', 'E70',
                'E71', 'E72', 'E73', 'E74', 'E75', 'E76', 'E77', 'E78', 'E79', 'E80',
                'E81', 'E82', 'E83', 'E84', 'E85', 'E86', 'E87', 'E88', 'E89', 'E90',
                'E91', 'E92', 'E93', 'E94', 'E95', 'E96', 'E97', 'E98', 'E99', 'E100',
                'E101', 'E102', 'E103', 'E104', 'E105', 'E106', 'E107', 'E108', 'E109', 'E110',
                'E111', 'E112', 'E113', 'E114', 'E115', 'E116', 'E117', 'E118', 'E119', 'E120',
                'E121', 'E122', 'E123', 'E124', 'E125', 'E126', 'E127', 'E128', 'VREF'] #'E129'

# ICA defaults
EEG_FOR_EOG = ['E25']
BLINK_DETECT_TH = 0.00005
MIN_BLINKS_ICA = 150
EOG_THRESHOLD = 3
N_COMPONENTS = 10
ICA_METHOD = 'fastica'
ICA_DECIM = 2
ICA_RANDOM_STATE = 23
