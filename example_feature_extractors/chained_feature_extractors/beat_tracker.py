import os
import sys
import numpy as np

CURRDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRDIR)
from setup_mlab import mlab
sys.path.remove(CURRDIR)

mlab.addpath(os.path.join(CURRDIR, 'coversongs'))

def extract_features(track, startbpm=[240, 1.0], tightness=[6, 0.8]):
    """Computes beat times.

    Returns the times (in sec) of the beats in the given track using
    Dan Ellis' beat.m Matlab function from:
    http://labrosa.ee.columbia.edu/projects/coversongs

    Parameters
    ----------
    track : gordon Track instance
    startbpm : float or length 2 list of floats
        The target tempo.  If startbpm is a two-element vector, it is
        taken as the mode of a tempo search window, with the second
        envelope being the spread (in octaves) of the search, and the
        best tempo is calculated (with tempo.m).
    tightness : float or length 2 list of floats
        Controls how tightly the start tempo is enforced within the
        beat (default 6, larger = more rigid); if it is a two-element
        vector the second parameter is alpha, the strength of
        transition costs relative to local match (0..1, default 0.8).
    """
    x,fs,svals = track.audio()

    beat_times = mlab.beat(x, fs, startbpm, tightness, 0);

    return beat_times.flatten()
