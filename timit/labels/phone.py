#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Make phone-level target labels for the End-to-End model (TIMIT corpus)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os.path import join
import numpy as np
from tqdm import tqdm

from utils.labels.phone import phone2num
from timit.util import map_phone2phone


def read_phone(label_paths, label_type, run_root_path, model,
               save_map_file=False, save_path=None):
    """Read phone transcript.
    Args:
        label_paths (list): list of paths to label files
        label_type (string): phone39 or phone48 or phone61
        run_root_path (string): path to make.sh
        model (string): ctc or attention
        save_map_file (bool, optional): if True, save the mapping file
        save_path (string, bool): path to save labels. If None, don't save labels
    """
    if label_type not in ['phone39', 'phone48', 'phone61']:
        raise ValueError('data_type is "phone39" or "phone48" or "phone61".')

    print('===> Reading & Saving target labels...')
    phone2phone_map_file_path = join(run_root_path, 'labels/phone2phone.txt')
    for label_path in tqdm(label_paths):
        speaker_name = label_path.split('/')[-2]
        file_name = label_path.split('/')[-1].split('.')[0]
        save_file_name = speaker_name + '_' + file_name + '.npy'

        phone_list = []
        with open(label_path, 'r') as f:
            for line in f:
                line = line.strip().split(' ')
                # start_frame = line[0]
                # end_frame = line[1]
                phone_list.append(line[2])

        # Map from 61 phones to the corresponding phones
        phone_list = map_phone2phone(phone_list, label_type,
                                     phone2phone_map_file_path)

        # Make the mapping file
        phone2num_map_file_path = join(
            run_root_path, 'labels', 'mapping_files', model, label_type + '_to_num.txt')
        phone_set = set([])
        with open(phone2phone_map_file_path, 'r') as f:
            for line in f:
                line = line.strip().split()
                if line[1] != 'nan':
                    if label_type == 'phone61':
                        phone_set.add(line[0])
                    elif label_type == 'phone48':
                        phone_set.add(line[1])
                    elif label_type == 'phone39':
                        phone_set.add(line[2])
                else:
                    # Ignore "q" if phone39 or phone48
                    if label_type == 'phone61':
                        phone_set.add(line[0])

        # Save mapping file
        if save_map_file:
            with open(phone2num_map_file_path, 'w') as f:
                if model == 'ctc':
                    for index, phone in enumerate(sorted(list(phone_set))):
                        f.write('%s  %s\n' % (phone, str(index)))
                elif model == 'attention':
                    for index, phone in enumerate(['<', '>'] + sorted(list(phone_set))):
                        f.write('%s  %s\n' % (phone, str(index)))

        # Convert from phone to number
        if model == 'attention':
            phone_list = ['<'] + phone_list + ['>']  # add <SOS> & <EOS>
        phone_list = phone2num(phone_list, phone2num_map_file_path)

        if save_path is not None:
            # Save phone labels as npy file
            np.save(join(save_path, save_file_name), phone_list)
