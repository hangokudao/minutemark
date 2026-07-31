FROM python:3.12-slim AS app-base

ARG WHISPER_MODEL=small

RUN pip install --no-cache-dir \
    faster-whisper==1.2.1 \
    fastapi==0.116.1 \
    uvicorn==0.35.0 \
    python-multipart==0.0.20

RUN python -c "from faster_whisper.utils import download_model; download_model('${WHISPER_MODEL}', output_dir='/models/whisper')"

WORKDIR /app
COPY pipeline.py /app/pipeline.py
COPY app.py /app/app.py
COPY static /app/static
COPY samples/korean /app/samples/korean
COPY ami-samples.tsv /app/ami-samples.tsv
COPY download-public-samples.sh /app/download-public-samples.sh

ENV WHISPER_MODEL=${WHISPER_MODEL} \
    WHISPER_MODEL_PATH=/models/whisper \
    WHISPER_CACHE=/models/whisper \
    KOREAN_SAMPLE_DIR=/app/samples/korean \
    BUDGET_DB=/tmp/minutemark/budget.sqlite3 \
    PORT=8080

FROM app-base AS sample-tools

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

FROM app-base AS runtime

CMD ["sh", "-c", "exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}"]
