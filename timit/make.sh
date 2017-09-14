#!/bin/bash

echo '----------------------------------------------------'
echo '|                      TIMIT                        |'
echo '----------------------------------------------------'
RUN_ROOT_PATH=`pwd`

# Set the root path to TIMIT corpus
TIMIT_PATH='/home/huanglu/data/timit'

# Set the path to save dataset
DATASET_SAVE_PATH='/home/huanglu/asr/end2end/data/timit/dataset'

# Set the path to save input features (fbank or MFCC)
INPUT_FEATURE_SAVE_PATH='/home/huanglu/asr/end2end/data/timit/fbank/'


echo '--------------------------------'
echo '|      Feature extraction       |'
echo '--------------------------------'
# Set the path to HTK
HTK_PATH='/home/huanglu/asr/end2end/tools/htk/HTKTools/HCopy'

# Make a mapping file from wav to htk
python make_scp.py $TIMIT_PATH $INPUT_FEATURE_SAVE_PATH $RUN_ROOT_PATH
CONFIG_PATH="./config/config_fbank"

# Convert from wav to htk files
$HTK_PATH -T 1 -C $CONFIG_PATH -S config/wav2fbank_train.scp
$HTK_PATH -T 1 -C $CONFIG_PATH -S config/wav2fbank_dev.scp
$HTK_PATH -T 1 -C $CONFIG_PATH -S config/wav2fbank_test.scp


echo '--------------------------------'
echo '|         Input data            |'
echo '--------------------------------'
# Make input data
python make_input.py $DATASET_SAVE_PATH $INPUT_FEATURE_SAVE_PATH


echo '--------------------------------'
echo '|             CTC               |'
echo '--------------------------------'
# Make transcripts for CTC model
python make_label_ctc.py $TIMIT_PATH $DATASET_SAVE_PATH $RUN_ROOT_PATH


echo '--------------------------------'
echo '|           Attention           |'
echo '--------------------------------'
# Make transcripts for Attention-based model
python make_label_attention.py $TIMIT_PATH $DATASET_SAVE_PATH $RUN_ROOT_PATH
