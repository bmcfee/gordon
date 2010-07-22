import numpy as np

def extract_features(track):
   """Computes the RMS energy in dB of the entire track."""
   samples, fs, svals = track.audio()
   return [20*np.log10(np.sqrt(np.mean(samples**2)))]
