FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Model files are not committed (see docs/MODEL_PROVENANCE.md). Train the
# synthetic demonstration models at build time, the same way CI does.
RUN python tools/train_synthetic_models.py --seed 42 --rows 5000 --out models
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["gunicorn", "gym_config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
