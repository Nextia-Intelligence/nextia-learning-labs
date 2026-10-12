# The Grafana stack (optional)

One container, `grafana/otel-lgtm:0.36.0`: an OpenTelemetry Collector, Prometheus (metrics),
Tempo (traces), Loki (logs) and Grafana. Every lesson also works without it, from saved
telemetry and `python -m ops`.

```sh
docker compose --profile observability up -d observability
```

Then run the API and the worker with `OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318`
(in `.env`), and open http://127.0.0.1:3000. The dashboards are in the folder *Ticket service*;
the alert rules are under *Alerting*.

| File | What it is |
|---|---|
| `provisioning/dashboards.yaml` | tells Grafana to load the dashboards below at start |
| `dashboards/ticket-service-overview.json` | the journeys and their SLIs, the queue, the provider |
| `dashboards/ticket-service-ai.json` | outcomes, cost, time and tokens by prompt version; reviews; old sources; model versions |
| `dashboards/ticket-service-traces.json` | failed and slow traces (Tempo), failed tickets (Loki) |
| `dashboards/ticket-service-releases.json` | releases side by side (the canary against the active release) |
| `alerts/service.yaml`, `alerts/ai-quality.yaml` | the alert rules (the same as `operations/alerts.toml`) |

Grafana reads these files at start: after you change one, restart the container
(`docker compose --profile observability restart observability`).

**Access control.** People who are not signed in can look at dashboards, not change them
(`GF_AUTH_ANONYMOUS_ORG_ROLE: Viewer` in `compose.yaml`). The admin account is `admin` with
the password `admin` on your computer only: change it before anyone else can reach port 3000.

**Retention.** Data lives in the volume `lgtmdata`. `docker compose --profile observability
down --volumes` deletes it. In production, set each store's retention (Prometheus
`--storage.tsdb.retention.time`, Loki `retention_period`, Tempo `block_retention`) to what
the telemetry is needed for, and no longer.

**Memory.** On the course's laptop the container used about 1.3 GB while the practice
scenarios ran. Stop it when you do not need it: `docker compose --profile observability stop`.
