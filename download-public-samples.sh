#!/bin/sh
set -eu

sample_dir=${SAMPLE_DIR:-/samples}
manifest=${AMI_SAMPLE_MANIFEST:-/app/ami-samples.tsv}
base_url=https://groups.inf.ed.ac.uk/ami/AMICorpusMirror/amicorpus

mkdir -p "$sample_dir"

tail -n +2 "$manifest" |
while IFS="$(printf '\t')" read -r sample_id meeting_id start_sec duration_sec expected_decision
do
    output="$sample_dir/$sample_id-$meeting_id.wav"
    if [ -s "$output" ]; then
        echo "SKIP $output"
        continue
    fi

    source_url="$base_url/$meeting_id/audio/$meeting_id.Mix-Headset.wav"
    temporary="$output.part.wav"
    echo "GET  $sample_id ($meeting_id ${start_sec}s + ${duration_sec}s)"
    ffmpeg \
        -hide_banner \
        -loglevel error \
        -nostdin \
        -ss "$start_sec" \
        -t "$duration_sec" \
        -i "$source_url" \
        -ac 1 \
        -ar 16000 \
        -sample_fmt s16 \
        -y "$temporary"
    mv "$temporary" "$output"
done

echo "AMI 공개 회의 샘플 준비 완료"
