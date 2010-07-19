import os
import sys
import numpy as np

CURRDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRDIR)
from setup_mlab import mlab
sys.path.remove(CURRDIR)

mlab.addpath(os.path.join(CURRDIR, 'coversongs'))

def extract_features(track, fctr=400, fsd=1.0, type=1):
    """Computes chroma features.

    Returns a feature vector of chroma features (12 rows x n fixed
    time step columns) based on Dan Ellis' chrombeatftrs Matlab
    function.

    See http://labrosa.ee.columbia.edu/projects/coversongs
    for more details.

    Parameters
    ----------
    track : gordon Track instance
    fctr : float
        Center frequency (in Hz) for chromagram weighting.
    fsd : float
        Standard deviation (in octaves) for chromagram weighting.
    type : int
        Selects chroma calculation type; 1 (default) uses IF; 2 uses
        all FFT bins, 3 uses only local peaks (a bit like Emilia).
    """
    x,fs,svals = track.audio()
    x = x.mean(1)[:,np.newaxis]

    # Calculate frame-rate chromagram
    fftlen = 2 ** (np.round(np.log(fs*(2048.0/22050))/np.log(2.0)))
    nbin = 12;
    
    if type == 2:
        Y = mlab.chromagram_E(x, fs, fftlen, nbin, fctr, fsd)
    elif type == 3:
        Y = mlab.chromagram_P(x, fs, fftlen, nbin, fctr, fsd)
    else:
        Y = mlab.chromagram_IF(x, fs, fftlen, nbin, fctr, fsd)

    return Y
