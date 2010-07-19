import os
import sys
import numpy as np

CURRDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRDIR)
from setup_mlab import mlab
sys.path.remove(CURRDIR)

mlab.addpath(os.path.join(CURRDIR, 'coversongs'))

def extract_features(track, feature_name, feature_kwargs={},
                     beat_tracker_name='beats', beat_tracker_kwargs={}):
    """Coonverts fixed-framerate features to beat-synchronous features.

    For folding spectrograms down into beat-sync features.  Calls Dan
    Ellis' beatavg.m Matlab function.

    See http://labrosa.ee.columbia.edu/projects/coversongs
    for more details.

    Parameters
    ----------
    track : gordon Track instance
    feature_name : string
        Name of gordon feature extractor used to calculate features on
        a fixed time grid.  Each column of the returned feature matrix
        should correspond to a fixed length window of the audio.
    feature_kwargs : dict
        Keyword arguments to pass to the fixed-framerate feature
        extractor.  Defaults to {}.
    beat_tracker_name : string
        Name of gordon feature extractor used to calculate beat times.
        Each element of the returned array should contain the start
        time in seconds of each beat.
    beat_tracker_kwargs : dict
        Keyword arguments to pass to the beat tracker feature
        extractor.  Defaults to {}.
    """

    fixed_framerate_feats = track.features(feature_name, **feature_kwargs)
    beattimes = track.features(beat_tracker_name, **beat_tracker_kwargs)
    
    x,fs,svals = track.audio()
    nsamples = x.shape[0]
    nframes = fixed_framerate_feats.shape[1]

    # Note that this is approximate if fixed_framerate_feats used any
    # zero padding on the end of the signal, so we floor.
    samples_per_frame = np.floor(nsamples / float(nframes))

    frames_per_second = fs / samples_per_frame

    beattimes_matrix = beattimes[np.newaxis,:]
    feats = mlab.beatavg(fixed_framerate_feats,
                         beattimes_matrix * frames_per_second)

    return feats.T
