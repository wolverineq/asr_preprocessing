#! /usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import join


def setup(corpus, feature, channels, save_path, sampling_rate=16000, window=0.025, slide=0.01,
          energy=True, delta=True, deltadelta=True, window_func='hamming'):
    """Setting for HTK.
    Args:
        feature: fbank or mfcc
        channels:
        save_path:
        sampling_rate:
        window:
        slide:
        energy:
        delta:
        deltadelta:
        window_func:
"""

    with open(join(save_path, 'config_fbank'), 'w') as f:
        if corpus == 'timit':
            f.write('SOURCEFORMAT = NIST\n')
        else:
            f.write('SOURCEFORMAT = WAV\n')

        # Sampling rate
        if sampling_rate == 16000:
            f.write('SOURCERATE = 625\n')
        elif sampling_rate == 8000:
            f.write('SOURCERATE = 1250\n')

        # Target features
        target = feature.upper()
        if energy:
            target += '_E'
        if delta:
            target += '_D'
        if deltadelta:
            target += '_A'
        f.write('TARGETKIND = %s\n' % target)

        # f.write('DELTAWINDOW = 2')
        # f.write('ACCWINDOW = 2')

        # Extract per slide
        f.write('TARGETRATE = %.1f\n' % (slide * 10000000))

        f.write('SAVECOMPRESSED = F\n')
        f.write('SAVEWITHCRC = F\n')

        # Window size
        f.write('WINDOWSIZE = %.1f\n' % (window * 10000000))

        # Window function
        if window_func == 'hamming':
            f.write('USEHAMMING = T\n')  # hamming window

        f.write('PREEMCOEF = 0.97\n')
        f.write('NUMCHANS = %d\n' % channels)
        f.write('ENORMALISE = F\n')
        f.write('ZMEANSOURCE = T\n')