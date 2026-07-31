#!/bin/sh
set -eu

cd "$(dirname "$0")"
mkdir -p output samples

docker compose up --build --abort-on-container-exit --exit-code-from pipeline pipeline
