# Constants for FFT Analysis

DEFAULT_FREQ_BANDS = {
    "delta": [0.5, 4.0],
    "theta": [4.0, 8.0],
    "alpha": [8.0, 13.0],
    "beta":  [13.0, 30.0],
    "sigma": [30.0, 45.0]
}

DEFAULT_ROI_ANT = ['E33', 'E26', 'E22', 'E15', 'E9', 'E2', 'E122', 'E34', 'E27', 'E23',
                   'E18', 'E16', 'E10', 'E3', 'E123', 'E116', 'E35', 'E28', 'E24', 'E19',
                   'E11', 'E4', 'E124', 'E117', 'E110', 'E111', 'E118', 'E5', 'E12', 'E20',
                   'E29', 'E30', 'E13', 'E6', 'E112', 'E105', 'E7', 'E106']

DEFAULT_ROI_POST = ['E64', 'E69', 'E74', 'E82', 'E89', 'E95', 'E96', 'E90', 'E83', 'E75',
                    'E70', 'E65', 'E58', 'E59', 'E66', 'E71', 'E76', 'E84', 'E91', 'E92',
                    'E85', 'E77', 'E72', 'E67', 'E60', 'E52', 'E53', 'E61', 'E62', 'E78',
                    'E86', 'E79', 'E54', 'E55']

MIN_FFT_SAMPLES = 32
MAX_N_FFT = 256
DEFAULT_FMIN = 0.5
DEFAULT_FMAX = 45.0
