# El modelo se exporta y verifica antes de construir la imagen.
FROM python:3.11.9-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    MODEL_DIR=/app/model MODEL_MANIFEST=/app/references/etapa4/model_manifest.json \
    MPLCONFIGDIR=/tmp/matplotlib HOME=/tmp
WORKDIR /app
COPY requirements-api.txt /app/requirements-api.txt
RUN python -m pip install --no-cache-dir -r requirements-api.txt && python -m pip check
COPY mibici_equipo39 /app/mibici_equipo39
COPY references/etapa4/model_manifest.json /app/references/etapa4/model_manifest.json
COPY models/serving/p1 /app/model
RUN python -B -c "from mibici_equipo39.serving.model_loader import load_model; load_model('/app/model', '/app/references/etapa4/model_manifest.json')"
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=3).read()"
CMD ["python", "-B", "-m", "uvicorn", "mibici_equipo39.serving.app:app", "--host", "0.0.0.0", "--port", "8000"]
