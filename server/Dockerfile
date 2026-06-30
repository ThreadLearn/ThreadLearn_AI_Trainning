FROM python:3.13-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server source
COPY server/ ./server/
COPY knowledge-base/knowledge_base.json ./knowledge-base/knowledge_base.json

WORKDIR /app/server

EXPOSE 8001

# Healthcheck — Docker tự kiểm tra sau 30s
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
