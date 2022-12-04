#!/usr/bin/env bash

set -e
set -u
set -o pipefail

train_set="tr_2000h_utt"
valid_set="cv05_utt"
test_sets="dev5_test_utt"

asr_config=conf/tuning/train_asr_conformer.yaml
inference_config=conf/decode_asr.yaml

feats_type=extracted

token_type=bpe

nlsyms=data/nlsyms
nbpe=1000
bpe_nlsyms="[hes]"

use_lm=false


./asr.sh \
    --lang en \
    --feats_type ${feats_type} \
    --token_type ${token_type} \
    --nbpe ${nbpe} \
    --nlsyms_txt ${nlsyms} \
    --bpe_nlsyms ${bpe_nlsyms} \
    --use_lm ${use_lm} \
    --asr_config "${asr_config}" \
    --inference_config "${inference_config}" \
    --train_set "${train_set}" \
    --valid_set "${valid_set}" \
    --test_sets "${test_sets}" \
    --asr_args "--use_wandb true --wandb_project how2-proposal --wandb_name how2_base_d8_l1024_conformer" \
    --bpe_train_text "data/${train_set}/text" "$@"
