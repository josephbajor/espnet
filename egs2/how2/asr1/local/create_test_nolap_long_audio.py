import os
import shutil

import kaldiio
import numpy as np

segment_duration = 15

for dset in ["dev5_test"]:
    dir = os.path.join("dump", "fbank_pitch", dset)
    out_dir = os.path.join(
        "dump", "fbank_pitch", dset + f"_seg{segment_duration}_nolap"
    )
    feat_dir = os.path.join(
        "dump", "fbank_pitch", dset + f"_seg{segment_duration}_nolap", "feats"
    )
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    if not os.path.isdir(feat_dir):
        os.mkdir(feat_dir)

    for f in os.listdir(dir + "/"):
        if os.path.isfile(f):
            shutil.copy(f, out_dir)

    shutil.copy(os.path.join(dir, "wav.scp"), os.path.join(out_dir, "wav.scp"))
    with open(os.path.join(dir, "text"), "r") as tex:
        utt2text = {
            line.strip().split(" ")[0]: " ".join(line.strip().split(" ")[1:])
            for line in tex.readlines()
        }

    with open(os.path.join(dir, "feats.scp"), "r") as fea:
        utt2feats = {
            line.strip().split(" ")[0]: " ".join(line.strip().split(" ")[1:])
            for line in fea.readlines()
        }

    with open(os.path.join(dir, "video_vit16.scp"), "r") as fea:
        utt2vit = {
            line.strip().split(" ")[0]: " ".join(line.strip().split(" ")[1:])
            for line in fea.readlines()
        }

    with open(os.path.join(dir, "video_resnext32.scp"), "r") as fea:
        utt2resnext = {
            line.strip().split(" ")[0]: " ".join(line.strip().split(" ")[1:])
            for line in fea.readlines()
        }

    # with open(os.path.join(dir, "video_r2plus1d.scp"), "r") as fea:
    #     utt2resnext = {
    #         line.strip().split(" ")[0]: " ".join(line.strip().split(" ")[1:])
    #         for line in fea.readlines()
    #     }

    dia2data = {}
    with open(os.path.join(dir, "segments"), "r") as seg:
        segments = seg.readlines()
        for line in segments:
            utt_id, dia_id, start_time, end_time = line.strip().split(" ")
            if dia_id in dia2data:
                dia2data[dia_id].append(
                    [
                        utt_id,
                        float(start_time),
                        float(end_time),
                        utt2text[utt_id],
                    ]
                )
            else:
                dia2data[dia_id] = [
                    [
                        utt_id,
                        float(start_time),
                        float(end_time),
                        utt2text[utt_id],
                    ]
                ]

    for dia_id, data in dia2data.items():
        data.sort(key=lambda x: x[1])

    new_segments = []
    new_text = []
    new_utt2spk = []
    with kaldiio.WriteHelper(
        "ark,scp:{},{}".format(
            os.path.join(feat_dir, "feats.ark"), os.path.join(out_dir, "feats.scp")
        )
    ) as writer, kaldiio.WriteHelper(
        "ark,scp:{},{}".format(
            os.path.join(feat_dir, "vit_feats.ark"),
            os.path.join(out_dir, "video_vit16.scp"),
        )
    ) as vit_writer, kaldiio.WriteHelper(
        "ark,scp:{},{}".format(
            os.path.join(feat_dir, "resnext_feats.ark"),
            os.path.join(out_dir, "video_resnext32.scp"),
        )
    ) as resnext_writer:
        for dia, data in dia2data.items():
            ## Merge segments of upto "segment_duration" seconds of audio
            while len(data) > 1:
                durations = np.array([x[2] - x[1] for x in data])
                # print("Durations {}".format(durations))
                cumsum = np.cumsum(durations, axis=0)
                # print("CumSum {}".format(cumsum))
                difference = segment_duration - cumsum
                difference[difference < 0] = np.inf
                index = np.argmin(difference)
                data_to_combine = data[: index + 1] if index + 1 <= len(data) else data
                # print("Data to Combine {} {} {}".format(data_to_combine, i, index))
                utt_ids = [x[0] for x in data_to_combine]
                combined_start = data_to_combine[0][1]
                combined_end = data_to_combine[-1][2]
                combined_text = " ".join([x[3] for x in data_to_combine])
                combined_feats = np.concatenate(
                    [kaldiio.load_mat(utt2feats[x]) for x in utt_ids], axis=0
                )
                combined_vit = np.concatenate(
                    [kaldiio.load_mat(utt2vit[x]) for x in utt_ids], axis=0
                )
                combined_resnext = np.concatenate(
                    [kaldiio.load_mat(utt2resnext[x]) for x in utt_ids], axis=0
                )
                print(
                    f"Combined vit shape {combined_vit.shape} Combined Feats shape {combined_feats.shape}"
                )
                writer(data_to_combine[0][0], combined_feats)
                vit_writer(data_to_combine[0][0], combined_vit)
                resnext_writer(data_to_combine[0][0], combined_resnext)
                # print("Combined Start {} | Combined End {} | Combined Duration {} ".format(combined_start,combined_end,combined_end-combined_start))
                # print("Combining Utts {} into {}".format([x[0] for x in data_to_combine],new_uttid))
                # print("Combined Text {}".format(combined_text))
                new_segments.append(
                    "{} {} {:.2f} {:.2f}".format(
                        data[0][0], dia, combined_start, combined_end
                    )
                )
                new_text.append("{} {}".format(data[0][0], combined_text))
                new_utt2spk.append("{} {}".format(data[0][0], dia))
                data = data[index + 1 :] if index + 1 < len(data) else []

    with open(os.path.join(out_dir, "segments"), "w") as f:
        f.write("\n".join(new_segments))

    with open(os.path.join(out_dir, "text"), "w") as f:
        f.write("\n".join(new_text))

    with open(os.path.join(out_dir, "utt2spk"), "w") as f:
        f.write("\n".join(new_utt2spk))
