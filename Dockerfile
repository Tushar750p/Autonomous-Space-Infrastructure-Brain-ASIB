FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir .

ENV ASIB_HOST=0.0.0.0
ENV ASIB_PORT=8080
ENV ASIB_TICK_INTERVAL_S=1.0

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3   CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=3)" || exit 1

CMD ["python", "-c", "from asib.dashboard import run; run()"]
