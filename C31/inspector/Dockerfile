# The run inspector as one image: standard-library Python and the prebuilt web pages. No packages to install.
#   docker build -t larkfield-inspector .
#   docker run --rm -p 127.0.0.1:8318:8318 larkfield-inspector
# Live mode (Tempo, Prometheus and Grafana run on your computer):
#   docker run --rm -p 127.0.0.1:8318:8318 -e INSPECTOR_MODE=live \
#     -e TEMPO_URL=http://host.docker.internal:3200 -e PROMETHEUS_URL=http://host.docker.internal:9090 \
#     -e AUDIT_STORE=/audit/audit.jsonl -v "$PWD/work/audit:/audit:ro" larkfield-inspector
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    INSPECTOR_HOST=0.0.0.0 \
    INSPECTOR_PORT=8318 \
    INSPECTOR_NO_BROWSER=1

WORKDIR /app
COPY larkfield_inspector /app/larkfield_inspector
COPY web/dist /app/larkfield_inspector/static
RUN useradd --system --no-create-home inspector
USER inspector

EXPOSE 8318
CMD ["python", "-m", "larkfield_inspector", "--no-browser"]
