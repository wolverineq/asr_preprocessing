#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Make target labels for the CTC model (CSJ corpus)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os.path import join, basename
import re
import numpy as np
import pandas as pd
from tqdm import tqdm
import jaconv

from utils.util import mkdir_join
from utils.labels.character import kana2num
from utils.labels.phone import phone2num
from csj.labels.fix_trans import fix_transcript
from csj.labels.fix_trans import is_hiragana, is_katakana

# NOTE:
############################################################
# CTC model

# [character]
# 145 kana characters, noise(NZ), space(_),
# = 145 + 2 + = 147 labels

# [phone]
# 36 phones, noise(NZ), sil(_),
# = 36 + 2 = 38 labels

# [kanji]
# ?? kanji characters, ?? kana characters, ?? hiragana characters,
# noise(NZ), sil(_),
# = ?? + ?? + ?? + 2 = 3386 lables
############################################################

############################################################
# Attention-based model

# [character]
# 145 kana characters, noise(NZ), space(_), <SOS>, <EOS>
# = 145 + 2 + 2 = 149 labels

# [phone]
# 36 phones, noise(NZ), sil(_), <SOS>, <EOS>
# = 36 + 2 + 2 = 40 labels

# [kanji]
# ?? kanji characters, ?? kana characters, ?? hiragana characters,
# noise(NZ), sil(_), <SOS>, <EOS>
# = ?? + ?? + ?? + 2 + 2 = 3388 lables
############################################################


def read_sdb(label_paths, run_root_path, model, is_test=None, save_map_file=False,
             kanji_save_path=None, kana_save_path=None, phone_save_path=None,
             divide_by_space=False, stdout_transcript=False):
    """Read transcripts (.sdb) & save files (.npy).
    Args:
        label_paths (list): list of paths to label files
        run_root_path (path): absolute path of make.sh
        model (string): ctc or attention
        is_test (bool): set to True when making the test set
        save_map_file (bool, optional): if True, save the mapping file
        kanji_save_path (string, optional): path to save kanji labels.
            If None, don't save labels
        kana_save_path (string, optional): path to save kana labels.
            If None, don't save labels
        phone_save_path (string, optional): path to save phone labels.
            If None, don't save labels
        divide_by_space (bool, optional): if True, each word will be diveded by space
        stdout_transcript (bool, optional): if True, print processed
            transcripts to standard output
    Returns:
        speaker_dict (dict): the dictionary of utterances of each speaker
            key (string) => speaker name
            value (dict) => the dictionary of utterance information of each speaker
                key (string) => utterance index
                value (list) => [start_frame, end_frame, trans_kana, trans_kanji]
    """
    if model not in ['ctc', 'attention']:
        raise ValueError('model must be ctc or attention.')

    print('===> Reading target labels...')
    speaker_dict = {}
    char_set = set([])
    all_char_set = set([])
    for label_path in tqdm(label_paths):
        col_names = [j for j in range(25)]
        df = pd.read_csv(label_path, names=col_names,
                         encoding='SHIFT-JIS', delimiter='\t', header=None)
        drop_column = col_names
        drop_column.remove(3)
        drop_column.remove(5)
        drop_column.remove(10)
        drop_column.remove(11)
        df = df.drop(drop_column, axis=1)

        utterance_dict = {}
        utt_index_pre = 1
        start_frame_pre, end_frame_pre = None, None
        trans_kana, trans_kanji = '', ''
        speaker = basename(label_path).split('.')[0]
        for key, row in df.iterrows():
            time_info = row[3].split(' ')
            utt_index = int(time_info[0])
            segment = time_info[1].split('-')
            start_frame = int(float(segment[0]) * 100 + 0.5)
            end_frame = int(float(segment[1]) * 100 + 0.5)
            if start_frame_pre is None:
                start_frame_pre = start_frame
            if end_frame_pre is None:
                end_frame_pre = end_frame

            kanji = row[5]  # include kanji characters
            yomi = row[10]
            # pos_tag = row[11]

            # Stack word in the same utterance
            if utt_index == utt_index_pre:
                if divide_by_space:
                    trans_kana += yomi + '_'
                    trans_kanji += kanji + '_'
                else:
                    trans_kana += yomi
                    trans_kanji += kanji

                utt_index_pre = utt_index
                end_frame_pre = end_frame
                continue
            else:
                # Count the number of kakko
                left_kanji = trans_kanji.count('(')
                right_kanji = trans_kanji.count(')')
                if left_kanji != right_kanji:
                    if divide_by_space:
                        trans_kana += yomi + '_'
                        trans_kanji += kanji + '_'
                    else:
                        trans_kana += yomi
                        trans_kanji += kanji

                    utt_index_pre = utt_index
                    end_frame_pre = end_frame
                    continue

                left_kana = trans_kana.count('(')
                right_kana = trans_kana.count(')')
                if left_kana != right_kana:
                    if divide_by_space:
                        trans_kana += yomi + '_'
                        trans_kanji += kanji + '_'
                    else:
                        trans_kana += yomi
                        trans_kanji += kanji

                    utt_index_pre = utt_index
                    end_frame_pre = end_frame
                    continue
                else:
                    if model == 'ctc':
                        # Clean transcript
                        trans_kana = '_' + fix_transcript(
                            trans_kana) + '_'
                        trans_kanji = '_' + fix_transcript(
                            trans_kanji) + '_'

                        # Remove double underbar
                        while '__' in trans_kana:
                            trans_kana = re.sub('__', '_', trans_kana)
                        while '__' in trans_kanji:
                            trans_kanji = re.sub('__', '_', trans_kanji)

                        # Skip silence & noise only utterance
                        if trans_kana not in ['_', '_NZ_']:
                            for char in list(trans_kana):
                                char_set.add(char)
                            for char in list(trans_kanji):
                                all_char_set.add(char)

                            utterance_dict[str(utt_index - 1).zfill(4)] = [
                                start_frame_pre,
                                end_frame_pre,
                                trans_kana,
                                trans_kanji]

                            # for debug
                            if stdout_transcript:
                                print(trans_kanji)
                                print(trans_kana)

                    elif model == 'attention':
                        # Clean transcript
                        trans_kana = '<' + fix_transcript(
                            trans_kana) + '>'
                        trans_kanji = '<' + fix_transcript(
                            trans_kanji) + '>'

                        # Remove double underbar
                        while '__' in trans_kana:
                            trans_kana = re.sub('__', '_', trans_kana)
                        while '__' in trans_kanji:
                            trans_kanji = re.sub('__', '_', trans_kanji)
                        trans_kana = re.sub(r'<_', '<', trans_kana)
                        trans_kana = re.sub(r'_>', '>', trans_kana)
                        trans_kanji = re.sub(r'<_', '<', trans_kanji)
                        trans_kanji = re.sub(r'_>', '>', trans_kanji)

                        # Skip silence & noise only utterance
                        if trans_kana not in ['<>', '<_>', '<NZ>']:
                            for char in list(trans_kana):
                                char_set.add(char)
                            for char in list(trans_kanji):
                                all_char_set.add(char)

                            utterance_dict[str(utt_index - 1).zfill(4)] = [
                                start_frame_pre,
                                end_frame_pre,
                                trans_kana,
                                trans_kanji]

                            # for debug
                            if stdout_transcript:
                                print(trans_kanji)
                                print(trans_kana)

                    # Initialization
                    if divide_by_space:
                        trans_kana = yomi + '_'
                        trans_kanji = kanji + '_'
                    else:
                        trans_kana = yomi
                        trans_kanji = kanji

                    utt_index_pre = utt_index
                    start_frame_pre = start_frame
                    end_frame_pre = end_frame

        # Register all utterances of each speaker
        speaker_dict[speaker] = utterance_dict

    # Make mapping dictionary from kana to phone
    kana_list = []
    kana2phone_dict = {}
    phone_set = set([])
    with open(join(run_root_path, 'labels/kana2phone.txt'), 'r') as f:
        for line in f:
            line = line.strip().split('+')
            kana, phone_seq = line
            kana_list.append(kana)
            kana2phone_dict[kana] = phone_seq
            for phone in phone_seq.split(' '):
                phone_set.add(phone)
        kana2phone_dict['_'] = '_'
        kana2phone_dict['NZ'] = 'NZ'
        if model == 'attention':
            kana2phone_dict['<'] = '<'
            kana2phone_dict['>'] = '>'

    # Make the mapping file (from kanji, kana, phone to number)
    kanji_map_file_path = join(run_root_path, 'labels/mapping_files' + model + '/kanji2num.txt')
    kana_map_file_path = join(run_root_path, 'labels/mapping_files' + model + '/kana2num.txt')
    phone_map_file_path = join(run_root_path, 'labels/mapping_files' + model + '/phone2num.txt')
    if save_map_file:
        # kanji
        with open(kanji_map_file_path, 'w') as f:
            # Reserve index
            all_char_set.discard('N')
            all_char_set.discard('Z')
            all_char_set.discard('_')
            if model == 'attention':
                all_char_set.discard('<')
                all_char_set.discard('>')

            kanji_set = set([])
            for char in all_char_set:
                if (not is_hiragana(char)) and (not is_katakana(char)):
                    kanji_set.add(char)
            for kana in kana_list:
                kanji_set.add(kana)
                kanji_set.add(jaconv.kata2hira(kana))
            # NOTE: 頻出するラベルにはなるべく小さいインデックスを与える？？
            if model == 'ctc':
                kanji_list = ['_', 'NZ'] + sorted(list(kanji_set))
            elif model == 'attention':
                kanji_list = ['_', '<', '>', 'NZ'] + sorted(list(kanji_set))

            for index, kanji in enumerate(kanji_list):
                f.write('%s  %s\n' % (kanji, str(index)))

        # kana
        with open(kana_map_file_path, 'w') as f:
            if model == 'ctc':
                kana_list = ['_', 'NZ'] + kana_list
            elif model == 'attention':
                kana_list = ['_', '<', '>', 'NZ'] + kana_list

            for index, kana in enumerate(kana_list):
                f.write('%s  %s\n' % (kana, str(index)))

        # phone
        with open(phone_map_file_path, 'w') as f:
            if model == 'ctc':
                phone_list = ['_', 'NZ'] + sorted(list(phone_set))
            elif model == 'attention':
                phone_list = ['_',  '<', '>', 'NZ'] + sorted(list(phone_set))

            for index, phone in enumerate(phone_list):
                f.write('%s  %s\n' % (phone, str(index)))

    # for debug
    for char in list(char_set):
        if char not in kana_list:
            print(char)

    if kanji_save_path is not None:
        # Save target labels
        print('===> Saving target labels...')
        for speaker, utterance_dict in tqdm(speaker_dict.items()):
            mkdir_join(kanji_save_path, speaker)
            mkdir_join(kana_save_path, speaker)
            mkdir_join(phone_save_path, speaker)
            for utt_index, utt_info in utterance_dict.items():
                start_frame, end_frame, trans_kana, trans_kanji = utt_info
                save_file_name = speaker + '_' + utt_index + '.npy'

                # kanji
                if not is_test:
                    # Convert from kana character to index
                    kanji_index_list = kana2num(trans_kanji, kanji_map_file_path)

                    # Save as npy file
                    np.save(join(kanji_save_path, speaker, save_file_name),
                            kanji_index_list)
                else:
                    # Save as npy file
                    np.save(join(kanji_save_path, speaker, save_file_name),
                            trans_kanji)
                    # NOTE: save test transcripts as stirng rather than index

                # kana
                if not is_test:
                    # Convert from kana character to index
                    kana_index_list = kana2num(trans_kana, kana_map_file_path)

                    # Save as npy file
                    np.save(join(kana_save_path, speaker, save_file_name),
                            kana_index_list)
                else:
                    # Save as npy file
                    np.save(join(kana_save_path, speaker, save_file_name),
                            trans_kana)
                    # NOTE: save test transcripts as stirng rather than index

                # Convert kana character to phone
                trans_kana_list = list(trans_kana)
                trans_phone_seq_list = []
                i = 0
                while i < len(trans_kana_list):
                    # Check whether next character is a double consonant
                    if i != len(trans_kana_list) - 1:
                        if trans_kana_list[i] + trans_kana_list[i + 1] in kana2phone_dict.keys():
                            trans_phone_seq_list.append(
                                kana2phone_dict[trans_kana_list[i] + trans_kana_list[i + 1]])
                            i += 1
                        elif trans_kana_list[i] in kana2phone_dict.keys():
                            trans_phone_seq_list.append(
                                kana2phone_dict[trans_kana_list[i]])
                        else:
                            raise ValueError(
                                'There are no character such as %s'
                                % trans_kana_list[i])
                    else:
                        if trans_kana_list[i] in kana2phone_dict.keys():
                            trans_phone_seq_list.append(
                                kana2phone_dict[trans_kana_list[i]])
                        else:
                            raise ValueError(
                                'There are no character such as %s'
                                % trans_kana_list[i])
                    i += 1
                trans_phone_list = []
                for phone_seq in trans_phone_seq_list:
                    trans_phone_list.extend(phone_seq.split(' '))

                # Convert from phone to index
                phone_index_list = phone2num(
                    trans_phone_list, phone_map_file_path)

                # Save as npy file
                np.save(join(phone_save_path, speaker, save_file_name),
                        phone_index_list)

    return speaker_dict
