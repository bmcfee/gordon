import os
import numpy as np

# Note that this feature extractor doesn't include pyechonest as a
# dependency, so it must be installed and accessible to gordon in
# order to use this module.
import pyechonest
import pyechonest.config
import pyechonest.track

pyechonest.config.ECHO_NEST_API_KEY = os.environ['ECHO_NEST_API_KEY']

def extract_features(track, analysis_name='pitches'):
    """Compute per-segment features using the Echo Nest Analyze API.

    Returns an N frames x D dimensions array of features where each
    row corresponds to an Echo Nest "segment".

    Requires that pyechonest (http://code.google.com/p/pyechonest/) be
    installed.  A valid Echo Nest API key should be accessible from
    the environment variable ECHO_NEST_API_KEY.

    Parameters
    ----------
    analysis_name : string
        Name of The Echo Nest analysis to return.  Defaults to 'pitches'.
    """
    entrack = pyechonest.track.track_from_filename(track.fn_audio)
    return np.array([x[analysis_name] for x in entrack.segments])

