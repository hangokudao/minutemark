FROM python:3.12-slim AS app-base

ARG WHISPER_MODEL=small

RUN python -m pip install --no-cache-dir --upgrade pip==26.1.2 \
    && python -m pip install --no-cache-dir \
    faster-whisper==1.2.1 \
    fastapi==0.139.2 \
    starlette==1.3.1 \
    uvicorn==0.35.0 \
    python-multipart==0.0.32 \
    firebase-admin==7.5.0 \
    google-cloud-firestore==2.28.0 \
    google-cloud-storage==3.13.0

RUN python -c "from faster_whisper.utils import download_model; download_model('${WHISPER_MODEL}', output_dir='/models/whisper')"

WORKDIR /app
COPY pipeline.py /app/pipeline.py
COPY members.py /app/members.py
COPY app.py /app/app.py
COPY download-korean-regression.py /download-korean-regression.py
COPY korean-sample-manifest.json /korean-sample-manifest.json
RUN chmod 644 /download-korean-regression.py /korean-sample-manifest.json
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

RUN groupadd --system minutemark \
    && useradd --system --gid minutemark --home-dir /app --no-create-home minutemark \
    && mkdir -p /data /tmp/minutemark \
    && chown -R minutemark:minutemark /app /data /tmp/minutemark

FROM app-base AS sample-tools

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

FROM app-base AS runtime

USER minutemark

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8080') + '/api/health', timeout=3)"

CMD ["sh", "-c", "exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}"]
