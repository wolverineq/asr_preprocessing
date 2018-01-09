#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Prepare for making dataset (CSJ corpus)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os.path import join, basename, isfile, abspath
from glob import glob


class Path(object):
    """Prepare for making dataset.
    Args:
        data_path (string): path to CSJ corpus
        config_path (string): path to config dir
    """

    def __init__(self, data_path, config_path, htk_save_path=None):

        self.data_path = data_path
        self.config_path = config_path
        self.htk_save_path = htk_save_path

        self.wav_path = join(self.data_path, 'WAV')
        # NOTE: Update ver. (CSJ ver 4.)
        self.ver4_path = join(self.data_path, 'Ver4/SDB')

        self.__make()

    def __make(self):

        # Read eval speaker list
        eval1_speakers, eval2_speakers, eval3_speakers = [], [], []
        excluded_speakers = []
        # Speakers in test data
        with open(join(self.config_path, 'eval1_speaker_list.txt'), 'r') as f:
            for line in f:
                speaker = line.strip()
                eval1_speakers.append(speaker)
        with open(join(self.config_path, 'eval2_speaker_list.txt'), 'r') as f:
            for line in f:
                speaker = line.strip()
                eval2_speakers.append(speaker)
        with open(join(self.config_path, 'eval3_speaker_list.txt'), 'r') as f:
            for line in f:
                speaker = line.strip()
                eval3_speakers.append(speaker)

        # Exclude speakers in evaluation data
        with open(join(self.config_path, 'excluded_speaker_list.txt'), 'r') as f:
            for line in f:
                speaker = line.strip()
                excluded_speakers.append(speaker)
        # NOTE: Reference:
        # https://github.com/kaldi-asr/kaldi/blob/master/egs/csj/s5/local/csj_make_trans/csj_autorun.sh

        ####################
        # wav
        ####################
        self.wav_paths = {
            'train_subset': [],  # 967 A + 19 M files
            'train_fullset': [],  # 3212 (A + S + M + R) files
            'eval1': [],  # 10 files
            'eval2': [],  # 10 files
            'eval3': [],  # 10 files
            'dialog': []  # ?? files
        }

        # Core
        for wav_path in glob(join(self.wav_path, 'CORE/*/*/*.wav')):
            speaker = basename(wav_path).split('.')[0]
            if speaker in eval1_speakers:
                self.wav_paths['eval1'].append(wav_path)
            elif speaker in eval2_speakers:
                self.wav_paths['eval2'].append(wav_path)
            elif speaker in eval3_speakers:
                self.wav_paths['eval3'].append(wav_path)
            elif speaker.split('-')[0] in excluded_speakers:
                continue
            elif speaker[0] == 'D':
                # 学会講演インタビュー，模擬講演インタビュー，課題指向対話，自由対話
                if speaker not in excluded_speakers:
                    self.wav_paths['dialog'].append(wav_path)
            elif speaker[0] == 'A':
                self.wav_paths['train_subset'].append(wav_path)
                self.wav_paths['train_fullset'].append(wav_path)
            else:
                # S or R
                self.wav_paths['train_fullset'].append(wav_path)

        # Noncore
        for wav_path in glob(join(self.wav_path, 'NONCORE/*/*/*/*.wav')):
            speaker = basename(wav_path).split('.')[0]
            if speaker in eval1_speakers:
                self.wav_paths['eval1'].append(wav_path)
            elif speaker in eval2_speakers:
                self.wav_paths['eval2'].append(wav_path)
            elif speaker in eval3_speakers:
                self.wav_paths['eval3'].append(wav_path)
            elif speaker.split('-')[0] in excluded_speakers:
                continue
            elif speaker[0] in ['A', 'M']:
                self.wav_paths['train_subset'].append(wav_path)
                self.wav_paths['train_fullset'].append(wav_path)
            else:
                # S
                self.wav_paths['train_fullset'].append(wav_path)

        # Noncore dialog
        for wav_path in glob(join(self.wav_path, 'NONCORE-DIALOG/*/*.wav')):
            speaker = basename(wav_path).split('.')[0]
            if speaker.split('-')[0] in excluded_speakers:
                continue
            elif speaker[0] == 'D':
                # 学会講演インタビュー，模擬講演インタビュー，課題指向対話，自由対話
                if speaker not in excluded_speakers:
                    self.wav_paths['dialog'].append(wav_path)
                continue
            else:
                # R
                self.wav_paths['train_fullset'].append(wav_path)

        ##################################
        # Transcript (use ver4 if exists)
        ##################################
        self.trans_paths = {
            'train_subset': [],
            'train_fullset': [],
            'eval1': [],
            'eval2': [],
            'eval3': [],
            'dialog': []
        }

        for data_type in ['train_subset', 'train_fullset',
                          'eval1', 'eval2', 'eval3']:
            for i, wav_path in enumerate(self.wav_paths[data_type]):
                speaker = basename(wav_path).split('.')[0]
                ver4_path = join(self.ver4_path, speaker + '.sdb')
                if isfile(ver4_path):
                    self.trans_paths[data_type].append(ver4_path)
                else:
                    self.trans_paths[data_type].append(
                        wav_path.replace('.wav', '.sdb'))

    def wav(self, data_type):
        """Get paths to wav files.
        Args:
            data_type (string): train_subset or train_fullset or
                eval1 or eval2 or eval3
        Returns:
            list of paths to wav files
        """
        return sorted(self.wav_paths[data_type])

    def htk(self, data_type):
        """Get paths to htk files.
        Args:
            data_type (string): train_subset or train_fullset or
                eval1 or eval2 or eval3
        Returns:
            list of paths to htk files
        """
        if self.htk_save_path is None:
            raise ValueError('Set path to htk files.')

        # NOTE: ex.) cdj/htk/data_type/*.htk
        return [p for p in glob(join(self.htk_save_path, data_type, '*.htk'))]

    def trans(self, data_type):
        """Get paths to transcription (.sdb) files.
        Args:
            data_type (string): train_subset or train_fullset or
                eval1 or eval2 or eval3
        Returns:
            list of paths to transcription files
        """
        return sorted(self.trans_paths[data_type])


if __name__ == '__main__':

    path = Path(data_path='/n/sd8/inaguma/corpus/csj/data',
                config_path=abspath('./config'),
                htk_save_path='/n/sd8/inaguma/corpus/csj/htk')

    for data_type in ['train_fullset', 'train_subset',
                      'eval1', 'eval2', 'eval3']:

        print('===== %s =====' % data_type)
        print(len(path.wav(data_type=data_type)))
        print(len(path.htk(data_type=data_type)))
        print(len(path.trans(data_type=data_type)))
