#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

"""Segment an audio file into each utterance (save as numpy files)."""

import numpy as np
from collections import OrderedDict

from utils.inputs.htk import read as read_htk
from utils.inputs.wav2feature_python_speech_features import wav2feature as w2f_psf
from utils.inputs.wav2feature_librosa import wav2feature as w2f_librosa


def segment(audio_path, speaker, utterance_dict, is_training,
            sil_duration=0., tool='htk', config=None, mean=None,
            dtype=np.float32):
    """Segment each HTK or WAV file into utterances. Normalization will not be
       conducted here.
    Args:
        audio_path (string): path to a HTK or WAV file
        speaker (string): speaker name
        utterance_dict (dict): dictionary of utterance information
            key (string) => utterance index
            value (list) => [start_frame, end_frame, transcript (, transcript2)]
        sil_duration (float): duration of silence at both ends. Default is 0.
        tool (string): htk or python_speech_features or librosa
        config (dict): a configuration for feature extraction
        mean (np.ndarray):  A mean vector over the file
        dtype (optional): default is np.float64
    Returns:
        input_data_dict (dict):
            key (string) => utt_index
            value (np.ndarray )=> a feature vector of size
                `(frame_num, feature_dim)`
        input_data_utt_sum (np.ndarray): A sum of feature vectors of a speaker
        mean (np.ndarray): A mean vector over the file
        stddev (np.ndarray): A stddev vector over the file
        total_frame_num_file (int): total frame num of the target speaker's utterances
    """
    if tool != 'htk' and config is None:
        raise ValueError('Set config dict.')

    # Read the HTK or WAV file
    if tool == 'htk':
        input_data, _, _ = read_htk(audio_path)
    elif tool == 'python_speech_features':
        input_data = w2f_psf(
            audio_path,
            feature_type=config['feature_type'],
            feature_dim=config['channels'],
            use_energy=config['energy'],
            use_delta1=config['delta'],
            use_delta2=config['deltadelta'],
            window=config['window'],
            slide=config['slide'])
    elif tool == 'librosa':
        input_data = w2f_librosa(
            audio_path,
            feature_type=config['feature_type'],
            feature_dim=config['channels'],
            use_energy=config['energy'],
            use_delta1=config['delta'],
            use_delta2=config['deltadelta'],
            window=config['window'],
            slide=config['slide'])

    assert isinstance(utterance_dict, OrderedDict)
    # NOTE: utterance_dict must be an instance of OrderedDict

    # Divide into each utterance
    feature_dim = input_data.shape[1]
    input_data_dict = {}
    total_frame_num_file = 0
    end_frame_pre = 0
    utt_num = len(utterance_dict.keys())
    input_data_utt_sum = np.zeros((feature_dim,), dtype=dtype)
    stddev = np.zeros((feature_dim,), dtype=dtype)
    keys = sorted(list(utterance_dict.keys()))
    for i, utt_index in enumerate(keys):
        utt_info = utterance_dict[utt_index]
        start_frame, end_frame = utt_info[0], utt_info[1]

        # Check timestamp
        if start_frame > end_frame:
            print('Warning: time stamp is reversed.')
            print('speaker index: %s' % speaker)
            print('utterance index: %s' % utt_index)
            print('start_frame: %.3f' % start_frame)
            print('end_frame: %.3f' % end_frame)
            raise ValueError

        # Check the first utterance
        if i == 0:
            if start_frame >= sil_duration:
                start_frame_extend = start_frame - sil_duration
            else:
                start_frame_extend = 0

            if len(utterance_dict) != 1:
                start_frame_next = utterance_dict[keys[i + 1]][0]
                if end_frame > start_frame_next:
                    print('Warning: utterances are overlapping.')
                    print('speaker index: %s' % speaker)
                    print('utterance index: %s' % utt_index)
                    print('end_frame: %.3f' % end_frame)
                    print('start_frame_next: %.3f' % start_frame_next)

                if start_frame_next - end_frame >= sil_duration * 2:
                    end_frame_extend = end_frame + sil_duration
                else:
                    end_frame_extend = end_frame + \
                        int((start_frame_next - end_frame) / 2)
            else:
                end_frame_extend = end_frame + sil_duration
                # end_frame_extend = end_frame

        # Check the last utterance
        elif i == utt_num - 1:
            if start_frame - end_frame_pre >= sil_duration * 2:
                start_frame_extend = start_frame - sil_duration
            else:
                start_frame_extend = start_frame - \
                    int((start_frame - end_frame_pre) / 2)

            if input_data.shape[0] - end_frame >= sil_duration:
                end_frame_extend = end_frame + sil_duration
            else:
                end_frame_extend = input_data.shape[0]  # last frame

        # Check other utterances
        else:
            if start_frame - end_frame_pre >= sil_duration * 2:
                start_frame_extend = start_frame - sil_duration
            else:
                start_frame_extend = start_frame - \
                    int((start_frame - end_frame_pre) / 2)

            start_frame_next = utterance_dict[keys[i + 1]][0]
            if end_frame > start_frame_next:
                print('Warning: utterances are overlapping.')
                print('speaker index: %s' % speaker)
                print('utterance index: %s' % utt_index)
                print('end_frame: %.3f' % end_frame)
                print('start_frame_next: %.3f' % start_frame_next)

            if start_frame_next - end_frame >= sil_duration * 2:
                end_frame_extend = end_frame + sil_duration
            else:
                end_frame_extend = end_frame + \
                    int((start_frame_next - end_frame) / 2)

        input_data_utt = input_data[start_frame_extend:end_frame_extend]
        input_data_utt_sum += np.sum(input_data_utt, axis=0)
        total_frame_num_file += (end_frame_extend - start_frame_extend)
        input_data_dict[str(utt_index)] = input_data_utt

        # For computing stddev over the file
        if mean is not None:
            stddev += np.sum(
                np.abs(input_data_utt - mean) ** 2, axis=0)

        # Update
        end_frame_pre = end_frame

    if is_training:
        if mean is not None:
            # Compute stddev over the file
            stddev = np.sqrt(stddev / (total_frame_num_file - 1))
        else:
            # Compute mean over the file
            mean = input_data_utt_sum / total_frame_num_file
            stddev = None
    else:
        mean, stddev = None, None

    return input_data_dict, input_data_utt_sum, mean, stddev, total_frame_num_file
