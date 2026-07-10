FROM python:3.13-slim

LABEL maintainer="ListScanner"
LABEL description="ListScanner WebUI - Web路径扫描与敏感文件检测工具"

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY webapp.py .
COPY listscanner/ ./listscanner/
COPY templates/ ./templates/
COPY dictionary/ ./dictionary/

RUN rm -rf listscanner/study __pycache__

EXPOSE 5000

ENV FLASK_DEBUG=0

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "120", "webapp:app"]
