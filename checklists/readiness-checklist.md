# Readiness Checklist - Demo Day Team A1

Tick each item only after verifying it on the demo laptop.

- [ ] Radmin VPN is installed and joined to the correct Demo Network.
- [ ] Windows Firewall has an inbound rule allowing TCP port 8000.
- [ ] `.env` contains the assigned HiveMQ host, port, username, password, and exact input/output topics.
- [ ] No real MQTT credential appears in source code or `.env.example`.
- [ ] `docker compose up -d --build` completes successfully.
- [ ] `docker compose ps` shows `fit4110-api-demo-day` as healthy.
- [ ] `GET /health` returns HTTP 200 with `mqtt=connected`.
- [ ] Logs show a successful HiveMQ connection and subscription to `smart-campus/raw/iot/environment`.
- [ ] The worker receives raw events and publishes processed events to `smart-campus/events/sensor`.
- [ ] Output payload follows `contracts/mqtt-contract.md`.
- [ ] Output does not contain `scenario_hint_for_teacher`.
- [ ] Invalid schema is logged and not published.
- [ ] Sensor errors and unknown devices are classified correctly.
- [ ] MQTT reconnect and HTTP 503 behavior have been demonstrated.
- [ ] Analytics/Core has subscribed to the output topic and confirmed receipt.
- [ ] Current evidence is saved in `reports/` with clear filenames.

## Required Evidence

- [ ] `docker-compose-ps.png`
- [ ] `health-local.png`
- [ ] `mqtt-subscribe-evidence.png`
- [ ] `integration-evidence.png`
- [ ] `logs-compose.txt`
