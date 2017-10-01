#!/bin/bash

echo ============================================================================
echo "                               Switchboard                                "
echo ============================================================================

# Set paths
SWBD_PATH='/n/sd8/inaguma/corpus/swbd/data/LDC97S62/'
FISHER_PATH='/n/sd8/inaguma/corpus/swbd/data/fisher/'
EVAL2000_AUDIO_PATH='/n/sd8/inaguma/corpus/swbd/data/eval2000/LDC2002S09/'
EVAL2000_TRANS_PATH='/n/sd8/inaguma/corpus/swbd/data/eval2000/LDC2002T43/'
DATASET_SAVE_PATH='/n/sd8/inaguma/corpus/swbd/dataset'
WAV_SAVE_PATH='/n/sd8/inaguma/corpus/swbd/wav2'
HTK_SAVE_PATH='/n/sd8/inaguma/corpus/swbd/htk'
HTK_PATH='/home/lab5/inaguma/htk-3.4/bin/HCopy'

### Select one tool to extract features (HTK is the fastest)
TOOL='htk'
# TOOL='python_speech_features'
# TOOL='librosa'

### Configuration (Set by yourself)
FEATURE_TYPE='logmelfbank'  # or mfcc
CHANNELS=40
SAMPLING_RATE=16000
WINDOW=0.025
SLIDE=0.01
ENERGY=0
DELTA=1
DELTADELTA=1
# NORMALIZE='global'
NORMALIZE='speaker'
# NORMALIZE='utterance'


########################################
# ↓↓↓ Don't change from here ↓↓↓
########################################
set -eu

if [ ! -e $SWBD_PATH ]; then
  echo "Switchboard directory was not found."
  exit 1
fi
if [ ! -e $FISHER_PATH ]; then
  echo "Warning: Fisher directory was not found."
fi
if [ ! -e $EVAL2000_AUDIO_PATH ]; then
  echo "eval2000 (audio) directory was not found."
  exit 1
fi
if [ ! -e $EVAL2000_TRANS_PATH ]; then
  echo "eval2000 (trans) directory was not found."
  exit 1
fi
if [ ! -e $DATASET_SAVE_PATH ]; then
  mkdir $DATASET_SAVE_PATH
fi
if [ ! -e $HTK_SAVE_PATH ] && [ $TOOL = 'htk' ]; then
  mkdir $HTK_SAVE_PATH
fi

RUN_ROOT_PATH=`pwd`


echo ============================================================================
echo "                   Download transcriptions (LDC97S62)                     "
echo ============================================================================

if [ -d $DATASET_SAVE_PATH/swb_ms98_transcriptions ]; then
  echo file exists: $DATASET_SAVE_PATH/swb_ms98_transcriptions
else
  if ! which wget >&/dev/null; then
    echo "This script requires you to first install wget";
    exit 1;
  fi

  wget http://www.openslr.org/resources/5/switchboard_word_alignments.tar.gz -P $DATASET_SAVE_PATH
    # wget http://www.isip.piconepress.com/projects/switchboard/releases/switchboard_word_alignments.tar.gz
  tar xzvf $DATASET_SAVE_PATH/switchboard_word_alignments.tar.gz -C $DATASET_SAVE_PATH
  rm $DATASET_SAVE_PATH/switchboard_word_alignments.tar.gz
fi

# Option A: SWBD dictionary file check
[ ! -f $DATASET_SAVE_PATH/swb_ms98_transcriptions/sw-ms98-dict.text ] && \
  echo  "SWBD dictionary file does not exist" &&  exit 1;



if [ ! -e ../tools/sph2pipe_v2.5/sph2pipe ]; then
  echo ============================================================================
  echo "                           Install sph2pipe                               "
  echo ============================================================================

  # Install instructions for sph2pipe_v2.5.tar.gz
  if ! which wget >&/dev/null; then
    echo "This script requires you to first install wget";
    exit 1;
  fi
  if ! which automake >&/dev/null; then
    echo "Warning: automake not installed (IRSTLM installation will not work)"
    sleep 1
  fi
  if ! which libtoolize >&/dev/null && ! which glibtoolize >&/dev/null; then
    echo "Warning: libtoolize or glibtoolize not installed (IRSTLM installation probably will not work)"
    sleep 1
  fi

  if [ ! -e ../tools/sph2pipe_v2.5.tar.gz ]; then
    wget -T 3 -t 3 http://www.openslr.org/resources/3/sph2pipe_v2.5.tar.gz -P ../tools
  else
    echo "sph2pipe_v2.5.tar.gz is already downloaded."
  fi
  tar -xovzf ../tools/sph2pipe_v2.5.tar.gz -C ../tools
  rm ../tools/sph2pipe_v2.5.tar.gz
  echo "Enter into ../tools/sph2pipe_v2.5 ..."
  cd ../tools/sph2pipe_v2.5
  gcc -o sph2pipe *.c -lm
  echo "Get out of ../tools/sph2pipe_v2.5 ..."
  cd ../../swbd
fi


echo ============================================================================
echo "                        Convert from sph to wav                           "
echo ============================================================================

mkdir -p $WAV_SAVE_PATH
mkdir -p $WAV_SAVE_PATH/swbd
mkdir -p $WAV_SAVE_PATH/fisher
mkdir -p $WAV_SAVE_PATH/eval2000/
mkdir -p $WAV_SAVE_PATH/eval2000/swbd
mkdir -p $WAV_SAVE_PATH/eval2000/callhome

##############################
# Switchboard
##############################
swbd_wav_paths=$(find $WAV_SAVE_PATH/swbd/ -iname '*.wav')
swbd_wav_file_num=$(find $WAV_SAVE_PATH/swbd/ -iname '*.wav' | wc -l)

if [ $swbd_wav_file_num -ne 4870 ] && [ $swbd_wav_file_num -ne 4876 ]; then
  swbd_sph_paths=$(find $SWBD_PATH -iname '*.sph')

  # file check
  swbd_sph_file_num=$(find $SWBD_PATH -iname '*.sph' | wc -l)
  [ $swbd_sph_file_num -ne 2435 ] && [ $swbd_sph_file_num -ne 2438 ] && \
    echo Warning: expected 2435 or 2438 data data files, found $swbd_sph_file_num

  for sph_path in $swbd_sph_paths ; do
    file_name=$(basename $sph_path)
    base=${file_name%.*}
    ext=${file_name##*.}
    wav_path_a=$WAV_SAVE_PATH/swbd/$base"-A.wav"
    wav_path_b=$WAV_SAVE_PATH/swbd/$base"-B.wav"
    echo "Converting from "$sph_path" to "$wav_path_a
    ../tools/sph2pipe_v2.5/sph2pipe -f wav -p -c 1 $sph_path $wav_path_a
    echo "Converting from "$sph_path" to "$wav_path_b
    ../tools/sph2pipe_v2.5/sph2pipe -f wav -p -c 2 $sph_path $wav_path_b
  done
else
  echo "Already converted: LDC97S62"
fi

##############################
# Fisher
##############################
fisher_wav_paths=$(find $WAV_SAVE_PATH/fisher/ -iname '*.wav')
fisher_wav_file_num=$(find $WAV_SAVE_PATH/fisher/ -iname '*.wav' | wc -l)

if [[ $fisher_wav_file_num -ne 23398 ]]; then
  fisher_sph_paths=$(find $FISHER_PATH -iname '*.sph')

  # file check
  fisher_sph_file_num=$(find $FISHER_PATH -iname '*.sph' | wc -l)
  [ $fisher_sph_file_num -ne 11699 ] && \
    echo Warning: expected 11699 data data files, found $fisher_sph_file_num

  for sph_path in $fisher_sph_paths ; do
    speaker=`echo $sph_path | awk -F "/" '{ print $(NF - 1) }'`
    file_name=$(basename $sph_path)
    base=${file_name%.*}
    ext=${file_name##*.}
    mkdir -p $WAV_SAVE_PATH/fisher/$speaker
    wav_path_a=$WAV_SAVE_PATH/fisher/$speaker/$base"-A.wav"
    wav_path_b=$WAV_SAVE_PATH/fisher/$speaker/$base"-B.wav"
    echo "Converting from "$sph_path" to "$wav_path_a
    ../tools/sph2pipe_v2.5/sph2pipe -f wav -p -c 1 $sph_path $wav_path_a
    echo "Converting from "$sph_path" to "$wav_path_b
    ../tools/sph2pipe_v2.5/sph2pipe -f wav -p -c 2 $sph_path $wav_path_b
  done
else
  echo "Already converted: Fisher"
fi

##############################
# eval2000 (swbd, callhome)
##############################
eval2000_wav_paths=$(find $EVAL2000_AUDIO_PATH -iname '*.wav')
eval2000_wav_file_num=$(find $EVAL2000_AUDIO_PATH -iname '*.wav' | wc -l)

if [[ $eval2000_wav_file_num -ne 80 ]]; then
  eval2000_sph_paths=$(find $EVAL2000_AUDIO_PATH -iname '*.sph')

  # file check
  eval2000_sph_file_num=$(find $EVAL2000_AUDIO_PATH -iname '*.sph' | wc -l)
  [ $eval2000_sph_file_num -ne 80 ] && \
    echo Warning: expected 80 data data files, found $eval2000_sph_file_num

  for sph_path in $eval2000_sph_paths ; do
    file_name=$(basename $sph_path)
    base=${file_name%.*}
    ext=${file_name##*.}
    if [[ ${file_name:0:2} = 'sw' ]]; then
      # swbd
      wav_path_a=$WAV_SAVE_PATH/eval2000/swbd/$base"-A.wav"
      wav_path_b=$WAV_SAVE_PATH/eval2000/swbd/$base"-B.wav"
    elif [[  ${file_name:0:2} = 'en' ]]; then
      # callhome
      wav_path_a=$WAV_SAVE_PATH/eval2000/callhome/$base"-A.wav"
      wav_path_b=$WAV_SAVE_PATH/eval2000/callhome/$base"-B.wav"
    fi
    echo "Converting from "$sph_path" to "$wav_path_a
    ../tools/sph2pipe_v2.5/sph2pipe -f wav -p -c 1 $sph_path $wav_path_a
    echo "Converting from "$sph_path" to "$wav_path_b
    ../tools/sph2pipe_v2.5/sph2pipe -f wav -p -c 2 $sph_path $wav_path_b
  done
else
  echo "Already converted: eval2000"
fi


if [ $TOOL = 'htk' ]; then
  echo ============================================================================
  echo "                   Feature extraction by HTK toolkit                      "
  echo ============================================================================

  mkdir -p $HTK_SAVE_PATH
  mkdir -p $HTK_SAVE_PATH/htk/swbd
  mkdir -p $HTK_SAVE_PATH/htk/fisher
  mkdir -p $HTK_SAVE_PATH/htk/eval2000/
  mkdir -p $HTK_SAVE_PATH/htk/eval2000/swbd
  mkdir -p $HTK_SAVE_PATH/htk/eval2000/callhome

  # Set the path to HTK (optional, set only when using HTK toolkit)
  if [ $FEATURE_TYPE = 'logmelfbank' ]; then
    CONFIG_PATH="./config/fbank.config"
  else
    CONFIG_PATH="./config/mfcc.config"
  fi

  # Make a config file to covert from wav to htk file
  python make_config.py \
    --wav_save_path $WAV_SAVE_PATH \
    --htk_save_path $HTK_SAVE_PATH \
    --run_root_path $RUN_ROOT_PATH \
    --feature_type $FEATURE_TYPE \
    --channels $CHANNELS \
    --sampling_rate $SAMPLING_RATE \
    --window $WINDOW \
    --slide $SLIDE \
    --energy $ENERGY \
    --delta $DELTA \
    --deltadelta $DELTADELTA \
    --config_path $CONFIG_PATH

  # Convert from wav to htk files
  $HTK_PATH -T 1 -C $CONFIG_PATH -S wav2fbank_swbd.scp
  $HTK_PATH -T 1 -C $CONFIG_PATH -S wav2fbank_fisher.scp
  $HTK_PATH -T 1 -C $CONFIG_PATH -S wav2fbank_eval2000_swbd.scp
  $HTK_PATH -T 1 -C $CONFIG_PATH -S wav2fbank_eval2000_ch.scp
fi


echo ============================================================================
echo "                                  Main                                    "
echo ============================================================================

exit 1

python main.py \
  --swbd_path $SWBD_PATH \
  --fisher_path $FISHER_PATH \
  --eval2000_trans_path $EVAL2000_TRANS_PATH \
  --dataset_save_path $DATASET_SAVE_PATH \
  --run_root_path $RUN_ROOT_PATH \
  --tool $TOOL \
  --wav_save_path $WAV_SAVE_PATH \
  --htk_save_path $HTK_SAVE_PATH \
  --feature_type $FEATURE_TYPE \
  --channels $CHANNELS \
  --sampling_rate $SAMPLING_RATE \
  --window $WINDOW \
  --slide $SLIDE \
  --energy $ENERGY \
  --delta $DELTA \
  --deltadelta $DELTADELTA \
  --normalize $NORMALIZE


echo 'Successfully completed!!!'