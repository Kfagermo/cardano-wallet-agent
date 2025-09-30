# Survival Plan: Earn Fast on Masumi With Minimal Marketing

Version: 1.0  
Owner: You (Windsurf + Cline + OpenRouter)  
Goal: Ship in 7 days and start earning with minimal external marketing

## 1) Product to Build Now (Money-First)

Cardano Wallet Health & Risk Scoring Agent (MIP-003 compliant)

Why this:
- Cross-agent utility: Many agents/dashboards need deterministic wallet insights.
- Cheap to operate: Only on-chain reads (Blockfrost), no paid LLMs/social APIs needed.
- Cache-friendly: Address-based responses make margins high.
- Clear value/price per call: Perfect for Sokosumi marketplace and agent-to-agent consumption.

Inputs/Outputs:
- Input: Cardano address(es), network (mainnet/preprod)
- Output: JSON scorecard with:
  - Balances, tokens, staking status
  - Age/first-seen, recent activity (tx velocity)
  - Counterparty diversity heuristic
  - Known-label flag (if enrichment available)
  - Risk score (0–100) + “health” category (safe/caution/risky) + reasons

SLOs:
- Latency: < 1s cached, 1–3s cold
- Availability: 99%+

## 2) Monetization

Primary: Pay-per-use via Masumi
- 0.02–0.05 ADA per address (discounts for batches)

Secondary:
- B2B/API plans: $19–$49/month (rate limits/SLA)
- Upsell later: “Portfolio health check” and “watchlist alerts”

Distribution:
- Sokosumi marketplace listing (discovery)
- Agent-to-Agent (A2A) consumption (other agents call your service)
- Optional: Masumi hackathons and community posts (ecosystem-native)

## 3) Masumi Compatibility (MIP-003 API)

Implement these endpoints on your service (Agentic Service API):

- GET /availability
  - Response:
    ```
    {
      "status": "available",
      "uptime": 123456,
      "message": "OK"
    }
    ```
- GET /input_schema
  - Response:
    ```
    {
      "input_data": [
        { "key": "address", "value": "string" },
        { "key": "network", "value": "string" }  // "mainnet" | "preprod"
      ]
    }
    ```
- POST /start_job
  - Body:
    ```
    {
      "input_data": [
        { "key": "address", "value": "addr1..." },
        { "key": "network", "value": "mainnet" }
      ]
    }
    ```
  - Response:
    ```
    { "job_id": "uuid", "payment_id": "string" }
    ```
- GET /status?job_id=UUID
  - Response:
    ```
    {
      "job_id": "UUID",
      "status": "awaiting payment | running | completed | failed",
      "result": "string or URL" // JSON string or link to JSON
    }
    ```

Example result payload (as JSON string in `result`):
```
{
  "address": "addr1...",
  "network": "mainnet",
  "balances": { "ada": 1543.21, "tokens": [{ "policy": "...", "asset": "...", "qty": "1000" }] },
  "staking": { "delegated": true, "pool_id": "pool1...", "since": "2023-11-01" },
  "age_days": 682,
  "tx_velocity_30d": 14,
  "counterparty_diversity_90d": 0.72,
  "known_label": "exchange",
  "risk_score": 27,
  "health": "safe",
  "reasons": ["stable staking", "diverse counterparties", "no risky token inflows detected"]
}
```

Docs:
- Agentic Service API: https://docs.masumi.network/documentation/technical-documentation/agentic-service-api
- Enable Agent Collaboration: https://docs.masumi.network/documentation/how-to-guides/how-to-enable-agent-collaboration
- List on Sokosumi: https://docs.masumi.network/documentation/how-to-guides/list-agent-on-sokosumi

## 4) Payment & Listing Flow (Masumi)

- Operate Masumi Payment Service (your node):
  - Accept human-to-agent and agent-to-agent payments
  - Use `/payment-information`, `/purchase`, `GET/PATCH /purchase` (refund/timeouts)
- Register your agent on Masumi (registry)
- List on Sokosumi:
  - Requirements: Registered agent + MIP-003-compliant API
  - Submit form: https://tally.so/r/nPLBaV
  - Listing content: Clear schema, pricing, sample input/output, screenshots, latency/availability claims

## 5) Tech, Cost, and Architecture

Stack:
- Python, FastAPI, httpx
- Blockfrost SDK (Cardano reads)
- SQLite/Redis (job store + cache)
- Masumi Payment Service (self-host per docs)

Infra:
- Kodosumi (recommended) or a small VPS ($5–$10/mo)
- Domains optional

Costs (monthly estimates):
- Hosting: $5–$10
- Blockfrost: Free → Starter paid as needed
- LLMs: $0 (not required for MVP)
- Gross margin: >80% with caching

High-level data flow:
1) Client/Agent calls `/start_job` with address, gets `job_id` and `payment_id`
2) Payment via Masumi (`/purchase`)
3) Service verifies payment → runs job → stores result → `/status` returns result
4) Refunds honored if timeout per docs

## 6) Feasibility & Revenue Expectation (Minimal Marketing)

- Doable: High — matches Masumi’s API and flows directly.
- Marketplace-only: 10–50 paid runs/month likely once listed with a good demo.
- Minimal ecosystem promotion (Sokosumi + Masumi/Cardano channels + hackathon): 100–300 paid runs/month plausible if positioned as a utility used by other agents/teams.
- Path to $100–$500/mo: Pay-per-use volume + 1–5 small B2B plans.

## 7) 7-Day Survival Sprint

Day 1
- Scaffold FastAPI project, implement `/availability`, `/input_schema`, `/start_job`, `/status`
- Create SQLite job store + cache
- Integrate Blockfrost (balances, staking, recent tx list)

Day 2
- Implement heuristics + risk score (transparent rules)
- Deterministic JSON outputs, unit tests for scoring

Day 3
- Integrate Masumi Payment Service (awaiting payment → running → completed)
- Implement timeouts + refund path (idempotent job handling)

Day 4
- Hardening: input validation, rate limiting, error handling, structured logs
- Perf: cache hits < 0.5s; p95 cold < 1.5s
- Produce 3 public example outputs

Day 5
- Register agent on Masumi registry
- Prepare Sokosumi listing materials: schema, screenshots, price (e.g., 0.03 ADA), SLOs

Day 6
- Deploy (Kodosumi or VPS), end-to-end smoke tests
- Submit listing; post short thread in Masumi/Cardano channels
- Submit to next Masumi hackathon

Day 7
- Add batch endpoint (score up to 20 addresses) with small discount
- Track KPIs; pricing experiments; tighten timeouts and retries

## 8) KPIs (First 30 Days)

- SLOs: 99% availability; p95 latency < 1.5s cold, < 0.5s hot
- Revenue: 100–300 paid calls/month at 0.03 ADA
- Adoption: 3+ A2A integrations; 1 dashboard on B2B plan
- Quality: refund rate < 1%; user rating ≥ 4/5

## 9) Risks & Mitigations

- Low initial traffic
  - Build a cross-agent utility; publish client snippets/templates
- Blockfrost limits
  - Backoff + robust caching; upgrade tier if needed
- Refunds/chargebacks
  - Strict timeouts; clear SLAs; idempotent jobs
- Copycats
  - Ship first; iterate quickly; refine heuristics; keep price attractive

## 10) Implementation Notes

Suggested repo structure:
```
/src
  api/
    routes.py
  services/
    scoring.py
    blockfrost_client.py
  store/
    jobs.py
    cache.py
  masumi/
    payments.py
  main.py
requirements.txt
.env.example
README.md
```

.env.example:
```
BLOCKFROST_PROJECT_ID=...
NETWORK=mainnet
MASUMI_PAYMENT_SERVICE_URL=...
MASUMI_API_KEY=...
PRICE_PER_ADDRESS_ADA=0.03
```

FastAPI skeleton (sketch):
```python
from fastapi import FastAPI, HTTPException
import uuid, time, json

app = FastAPI()
JOBS = {}

@app.get("/availability")
def availability():
    return {"status": "available", "uptime": int(time.time()), "message": "OK"}

@app.get("/input_schema")
def input_schema():
    return {"input_data": [
        {"key": "address", "value": "string"},
        {"key": "network", "value": "string"}  # "mainnet" | "preprod"
    ]}

@app.post("/start_job")
def start_job(payload: dict):
    # validate payload vs schema...
    job_id = str(uuid.uuid4())
    payment_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "awaiting payment", "result": None, "payment_id": payment_id}
    return {"job_id": job_id, "payment_id": payment_id}

@app.get("/status")
def status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {"job_id": job_id, "status": job["status"], "result": job["result"]}
```

## 11) Listing Checklist (Sokosumi)

- [ ] Working MIP-003 endpoints with sample curl commands
- [ ] Clear /input_schema example
- [ ] Example input/output JSON and 2–3 screenshots
- [ ] Pricing (e.g., 0.03 ADA per address) and SLOs
- [ ] Refund/timeout policy stated
- [ ] Submit via Tally form and track approval

## 12) Next Steps

- Build from this plan now (Day 1 tasks)
- After smoke tests, register and list on Sokosumi
- Announce only within Masumi/Cardano channels and hackathon — keep external marketing minimal
- Iterate pricing and batching based on usage

Make it simple, reliable, cheap, and easy for other agents to integrate — that’s the fastest path to revenue with minimal marketing on Masumi.

---

# Addendum — Status Snapshot and Next Session Plan (2025-09-22)

This section captures the current repo state and a concrete starting checklist for the next session.

## A) Current Status Snapshot

What’s working
- MIP-003 endpoints: /availability, /input_schema, /start_job, /status
- Payment verification (Masumi Payment Service):
  - Fixed GET reads: use identifierFromPurchaser with required network param (Preprod/Mainnet)
  - Path form /purchase/{id} returns 404 on this deployment — handled
  - /prepare_purchase generates valid payloads and can POST purchases
- Heuristics: Deterministic scoring + health bucket with reasons
- On-chain reads: Blockfrost integration with safe fallback
- Reports: HTML generation
- Env: .env configured with MASUMI_PAYMENT_SERVICE_URL (includes /api/v1), MASUMI_API_KEY, NETWORK=preprod

Known gaps
- In-memory job store (no persistence/caching)
- No unit tests; minimal logging; no rate limiting
- Refund + idempotency flows not yet implemented
- Docs: Need explicit note that GET /purchase requires network=Preprod|Mainnet
- Registry/listing not started; no batch endpoint

## B) Next Session — High‑Priority Checklist

Core
- [ ] Replace in-memory JOBS with SQLite store
  - jobs(job_id PK, payment_id, status, input_json, result_str, created_at, updated_at)
  - CRUD helpers and transaction-safe status transitions
- [ ] Add cache for (address, network) → result_json with TTL
  - Use SQLite table cache(address, network, result_json, computed_at, PK(address, network))

Quality
- [ ] Add unit tests (pytest): scoring and API smoke path
- [ ] Structured JSON logging for key flows; simple rate limit (per IP)

Payments completeness
- [ ] Implement refund/timeout handling and idempotency guard
- [ ] Document GET /purchase network requirement in README and /payment_information

Go-to-market
- [ ] Produce 3 example JSON outputs and 2–3 screenshots
- [ ] Prepare registry + Sokosumi listing content (schema, pricing 0.03 ADA, SLOs)

Optional (after above)
- [ ] Batch endpoint: /start_job_batch (≤20 addresses) with discount; leverage cache

## C) Useful Commands (PowerShell)

Run API locally
- uvicorn src.main:app --reload --port 8000

Check Payment Service (requires network param)
- curl.exe -s -o NUL -w "HTTP %{http_code}\n" -H "Accept: application/json" -H "token: $Env:MASUMI_API_KEY" "$Env:MASUMI_PAYMENT_SERVICE_URL/purchase" -G --data-urlencode "identifierFromPurchaser=<payment_id>" --data-urlencode "network=Preprod"

Start a job (dev)
- $body = @{ input_data = @(@{ key="address"; value="addr1..."}; @{ key="network"; value="preprod"}) } | ConvertTo-Json -Depth 5
- Invoke-RestMethod -Uri "http://127.0.0.1:8000/start_job" -Method POST -ContentType "application/json" -Body $body

## Sprint Backlog — MVP Build Session (2025-09-22 → 2025-09-25)

Scope: Reach “listable MVP” with persistence, caching, payment completeness, and listing assets. This complements Sections 7 & Addendum.

Progress tracker (rolling)
- [x] MIP-003 endpoints: /availability, /input_schema, /start_job, /status
- [x] Deterministic heuristics + health bucket with reasons
- [x] On-chain reads with Blockfrost + safe fallback
- [x] HTML report template + sample reports
- [x] Payment verification polling (identifierFromPurchaser + network param)
- [x] Dev env + cURL examples
- [x] Persistent job store (SQLite)
- [x] Cache (address, network) → result with TTL
- [x] Status returns JSON string (A2A friendly) + report_path for humans
- [x] Payment timeout marks failed with reason
- [x] Deployment assets: Dockerfile, .dockerignore, DEPLOYMENT.md
- [ ] Idempotency guard (dedupe recent jobs by input)
- [ ] Structured JSON logging + simple rate limit
- [ ] Unit tests (pytest): scoring + API smoke (BYPASS=true)
- [ ] Registry + Sokosumi listing package (schema, price, screenshots)
- [ ] Deploy (Kodosumi/VPS), secrets rotation, SLO measurement

Definition of Done (MVP)
- Working MIP-003 endpoints with persistent jobs
- Cache hit path < 0.5s, p95 cold < 2s documented
- Status returns JSON string (and optional link to hosted report)
- Payment handling: timeout → failed; refund path documented; idempotency guard in place
- Basic tests pass; structured logs present; rate limit enabled
- Listing package ready and submitted

Active Session Plan (today)
1) Idempotency guard
   - [ ] Dedupe by input_json within a short window (e.g., 10 min). If a recent awaiting/running/completed job exists for the same input, return that job_id/payment_id.
2) Structured JSON logging
   - [ ] Add JSON logs for start_job/status/payment polling/run completion with job_id correlation and basic request metadata. Add simple per-IP rate limit.
3) Tests
   - [ ] pytest: unit test for _compute_risk_and_health; API smoke path with BYPASS=true using TestClient.
4) Listing package
   - [ ] Produce 3 example JSON outputs and 2–3 screenshots; finalize initial price (0.05 ADA) and SLOs copy.
5) Deploy + live purchase
   - [ ] Deploy on Kodosumi or Ubuntu VPS (DEPLOYMENT.md). Keep MASUMI_BYPASS_PAYMENTS=false. Run one real purchase end-to-end to validate paid flow.

Notes
- Security: Rotate MASUMI_API_KEY and SELLER_VKEY if ever committed; ensure .env is gitignored in deployment repo.
- Result format: Prefer JSON string in /status with an optional report_url for human view.

---

# Addendum 2 — Codebase Assessment & Recommendations (2025-09-26)

An automated review of the codebase was performed to assess its structure, quality, and alignment with the project's goals.

## Overall Assessment

**This is a high-quality project.** The file structure is logical, the planning documented in this file is exceptionally clear, and the existing code demonstrates strong, modern development practices. The project is in an excellent position to meet its goal of a fast, successful launch on the Sokosumi marketplace.

The following recommendations are intended to build on this strong foundation and address the known gaps identified in the status snapshot.

## High-Priority Recommendations

These align with the "Next Session Checklist" and are critical for a production-ready service.

1.  **Implement Unit Tests (as planned):** This is the most critical next step. Adding `pytest` tests for the scoring logic and API smoke paths will ensure reliability and prevent regressions. This is already on the checklist and should be prioritized.
2.  **Add Structured Logging (as planned):** Implementing structured (JSON) logging is crucial for debugging and monitoring the agent once it's live. Correlating logs with `job_id` will be invaluable.

## Medium-Priority Recommendations (Post-MVP Refactoring)

These can be addressed after the initial MVP is launched to improve long-term maintainability.

1.  **Refactor Monolithic `src/main.py`:** The `main.py` file currently contains a large amount of logic. To improve modularity and align with the original architecture plan (Section 10), consider refactoring it:
    *   Move API endpoint definitions to `src/api/routes.py`.
    *   Extract business logic (e.g., risk scoring, Blockfrost interaction) into a `src/services/` directory.
    *   This will make the codebase easier to navigate and maintain as it grows.

2.  **Review SQLite Implementation:** The migration to a persistent SQLite store is complete and noted in the progress tracker. A follow-up review to confirm that database connections are handled safely (e.g., closed properly) and that write operations are transaction-safe will prevent data corruption under load.
