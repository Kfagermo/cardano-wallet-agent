# Wallet Health & Risk Scoring Agent — Sokosumi Listing Package

Summary
- Purpose: Deterministic wallet health and risk scoring for Cardano addresses. Suitable for agent-to-agent consumption and dashboards.
- Why it’s useful: Many agents need fast, reliable wallet heuristics without maintaining their own on-chain analytics. This service provides a consistent JSON scorecard with reasons and an optional human-friendly HTML report.
- Operates: Read-only on-chain lookups (Blockfrost) + deterministic heuristics. No paid LLMs. Heavy caching for repeated addresses.

Pricing and SLOs
- Price: 0.05 ADA per address (batch discounts coming next).
- SLOs:
  - p95 latency: cold < 2.0s, hot (cache) < 0.5s
  - Availability: 99%+
- Refunds:
  - If payment not confirmed within the configured timeout window, jobs are marked failed (see refund_policy below).

MIP-003 Agentic Service API
Base URL: https://YOUR_DOMAIN

Endpoints
- GET /availability
- GET /input_schema
- POST /start_job
- GET /status?job_id=UUID
- GET /payment_information?payment_id=STRING (helper; documents payment read patterns, idempotency, refund policy)
- GET /prepare_purchase (optional helper to construct Payment Service payload; can also POST it if execute=true)

Input schema (GET /input_schema)
```json
{
  "input_data": [
    { "key": "address", "value": "string" },
    { "key": "network", "value": "string" }
  ]
}
```
Notes
- network: "mainnet" | "preprod"

Example input (POST /start_job)
```json
{
  "input_data": [
    { "key": "address", "value": "addr1..." },
    { "key": "network", "value": "preprod" }
  ]
}
```

Result format (GET /status)
- status: "awaiting payment" | "running" | "completed" | "failed"
- result: JSON string containing the scorecard (or URL). Example keys:
```json
{
  "address": "addr1...",
  "network": "preprod",
  "balances": { "ada": 1543.21, "token_count": 3 },
  "staking": { "delegated": true, "pool_id": "pool1xyz", "since": "2023-11-01" },
  "first_seen": "2023-01-01",
  "age_days": 300,
  "tx_velocity_30d": 14,
  "counterparty_diversity_90d": 0.72,
  "known_label": "exchange",
  "risk_score": 31,
  "health": "safe",
  "reasons": ["delegated/staked ADA adds stability", "diverse counterparties", "known label: exchange"],
  "report_path": "reports/<job_id>.html",
  "symbol": "ADA",
  "window_label": "30d",
  "indicators_summary": "EMA(12/26), MACD, RSI(14)"
}
```

Payments (Masumi Payment Service)
- Header: token: <MASUMI_API_KEY>
- Network param required when reading purchases: ?network=Preprod|Mainnet
- Preferred read: GET /purchase?identifierFromPurchaser=<payment_id>
- Fallbacks: /purchase/<payment_id>, /purchase?payment_id=..., /purchase?purchase_id=..., /purchase?id=...

Idempotency and refunds
- Idempotency:
  - Window: 600 seconds (configurable)
  - Behavior: If an identical input (address + network) arrives during the window, the same job_id/payment_id may be reused.
- Refund policy:
  - Payment timeout (default 600s): job marked failed with reason "payment timeout".
  - Refund path: Use PATCH/GET on /purchase at your Payment Service deployment (include network param and token header). Follow your deployment’s documentation for refunds.

cURL examples
Replace https://YOUR_DOMAIN with the deployed base URL.

Check availability:
```
curl -s https://YOUR_DOMAIN/availability
```

Get input schema:
```
curl -s https://YOUR_DOMAIN/input_schema
```

Start a job:
```
curl -s -X POST https://YOUR_DOMAIN/start_job \
  -H "Content-Type: application/json" \
  -d '{ "input_data": [ {"key":"address","value":"addr1..."}, {"key":"network","value":"preprod"} ] }'
```

Check status:
```
curl -s "https://YOUR_DOMAIN/status?job_id=YOUR_JOB_ID"
```

Payment info (helper):
```
curl -s "https://YOUR_DOMAIN/payment_information?payment_id=YOUR_PAYMENT_ID"
```

Example outputs
- JSON examples (generated from deterministic snapshots):
  - examples/example_safe.json
  - examples/example_caution.json
  - examples/example_risky.json
- HTML report screenshots:
  - reports/example_safe.html
  - reports/example_caution.html
  - reports/example_risky.html
You can open the HTML files in a browser and capture 2–3 screenshots to attach to the listing.

Constraints and notes
- Read-only on-chain integrations (Blockfrost). If Blockfrost is unavailable, the service uses safe fallback samples to maintain uptime (with a clear flag in logs).
- Caching: (address, network) pairs are cached for 24h by default to reduce on-chain calls and improve latency.
- Data quality: Heuristics are deterministic and transparent. Future enhancements may add additional signals (e.g., spam token inflow heuristics, faucet patterns).
- Batch endpoint: Planned as a next iteration (up to 20 addresses with a small discount).

Support
- Status page: /availability
- Contact: Provide preferred email/handle here
- SLA: p95 cold < 2.0s, hot < 0.5s; 99% availability; refunds honored on timeouts per payment policy

Submission checklist (for Sokosumi)
- [x] Working endpoints and schema
- [x] Pricing: 0.05 ADA per address (introductory; subject to change)
- [x] SLOs and refund policy
- [x] Example JSONs and HTML report screenshots
- [x] cURL examples (availability, schema, start/status, payment info)
