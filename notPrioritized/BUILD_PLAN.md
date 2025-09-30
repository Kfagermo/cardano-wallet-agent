# Build Plan: Cardano Wallet Health & Risk Scoring Agent (Masumi, MIP-003)

Version: 1.1  
Owner: You (Windsurf + Cline + OpenRouter)  
Last updated: 2025-09-22

Goal: Ship in 7 days and start earning with minimal external marketing (per Survival Plan). This build plan is aligned to the current repo and code state.

-------------------------------------------------------------------------------

1) Current Status (Recap)

Implemented
- API (FastAPI) endpoints: /availability, /input_schema, /start_job, /status
- Payment integration (Masumi Payment Service):
  - Fixed polling: prefers GET /purchase?identifierFromPurchaser=...&network=Preprod|Mainnet
  - Added required network param everywhere; path variant returns 404 on this deployment
  - /prepare_purchase builds compliant payloads and can POST /purchase
- Heuristics: Deterministic risk scoring and health bucket with reasons
- Blockfrost integration: Real SDK usage if key present, with safe fallback sample
- Reports: HTML report generation
- Config: .env with MASUMI_PAYMENT_SERVICE_URL (/api/v1), MASUMI_API_KEY, NETWORK

Gaps
- In-memory job store only (no persistence/caching)
- No unit tests; no structured logs; no rate limiting
- Refund and idempotent flows not implemented
- Docs: Need to clearly document Payment Service read requirements (network param)
- Registry + Sokosumi listing not started
- No batch endpoint

-------------------------------------------------------------------------------

2) Next Session — Starting Point (Do These First)

Priority A (Core Functionality)
- [ ] Replace in-memory JOBS with SQLite (persistent job store)
  - jobs table: job_id (PK), payment_id, status, input_json, result_str, created_at, updated_at
  - helpers: get_job, upsert_job, update_status, set_result
- [ ] Add result caching for (address, network)
  - cache table: address, network, result_json, computed_at; TTL configurable (e.g., 24h)
  - on /start_job: if cache hit, short-circuit path after payment to return cached result
- [ ] Unit tests (pytest)
  - tests for scoring heuristics
  - API smoke test: start_job → simulate paid → status completed

Priority B (Payments Completeness)
- [ ] Implement timeout+refund path (PATCH/POST flow per Masumi docs)
  - When payment timed out: update status; optionally call refund endpoint if required
  - Ensure idempotent job handling (repeated polls safe)
- [ ] Document GET /purchase read requirements (network param) in README and /payment_information

Priority C (Hardening)
- [ ] Structured JSON logs and basic rate limit (e.g., simple IP+window)
- [ ] Error handling pass: clear HTTPException messages, validation

Priority D (Go-to-Market Prep)
- [ ] Produce 3 JSON example outputs and 2–3 screenshots
- [ ] Write listing materials (schema, pricing, SLOs, sample cURL)
- [ ] Register agent on Masumi registry and prepare Sokosumi listing

-------------------------------------------------------------------------------

3) Detailed Tasks

A) Persistence (SQLite) and Cache
- Add module: src/store/sqlite_store.py
  - init_db(): create tables if not exist
  - Jobs CRUD: create_job(job), get_job(job_id), update_job_status(job_id, status), set_result(job_id, result_str)
  - Cache CRUD: get_cache(address, network), set_cache(address, network, result_json, ttl)
- Wire into src/main.py
  - Replace in-memory dict with store calls
  - After computing result, write to cache keyed by (address, network)

Schema (SQL)
- jobs(job_id TEXT PRIMARY KEY, payment_id TEXT, status TEXT, input_json TEXT, result_str TEXT, created_at TEXT, updated_at TEXT)
- cache(address TEXT, network TEXT, result_json TEXT, computed_at INTEGER, PRIMARY KEY(address, network))

B) Payments Completeness
- Timeouts: existing polling uses MASUMI_PAYMENT_TIMEOUT_SEC; when exceeded:
  - Persist status “awaiting payment” (already done), consider auto-cancel if business policy requires
- Refund path:
  - Use POST /purchase/request-refund if applicable to completed purchases where SLA missed
  - Store refund initiation timestamps; expose to status if relevant
- Idempotency:
  - Before running job, re-check status transitions atomically in DB (e.g., only run if currently “awaiting payment”)

C) Tests (pytest)
- tests/test_scoring.py: cover _compute_risk_and_health thresholds and buckets
- tests/test_api_smoke.py:
  - POST /start_job (with valid payload) → returns job_id, payment_id
  - Force BYPASS_PAYMENTS=true for smoke path (or mock is_purchase_paid) → run job → GET /status returns completed with result str

D) Hardening
- Logging: use Python logging with JSON formatter for key events (start_job, payment poll tick, job completed)
- Rate limit: primitive token bucket (IP or API key) in-memory for now; can be toggled via env
- Input validation: ensure address and network thorough checks; normalise network to lower-case at ingress

E) Docs & Listing
- README: add explicit note that GET /purchase requires network param; show cURL examples
- /payment_information: add note “GET requires network=Preprod|Mainnet”
- Generate three sample reports (HTML + JSON snippets in docs)
- Listing content: schema, pricing 0.03 ADA per address, SLOs, screenshots

F) Registry & Deployment
- Register agent on Masumi registry (per docs)
- Deployment target: Kodosumi or small VPS
- Post-deploy smoke tests:
  - /availability, /input_schema
  - end-to-end paid flow using payment service (preprod)

G) Batch Endpoint (Post-listing)
- /start_job_batch: accept up to 20 addresses; discount pricing; reuse caching inside

-------------------------------------------------------------------------------

4) Acceptance Criteria (Next Milestone)

- Persistent jobs in SQLite; server restarts do not lose state
- Cache hit path returns a completed result within 500ms for a previously seen (address, network)
- Payment polling stable against Payment Service with network param; 0% 400 errors on read path
- Unit tests passing (scoring + API smoke)
- README and /payment_information document network requirement and preferred GET key
- Two screenshots and three JSON examples available
- Ready to begin registry and listing tasks

-------------------------------------------------------------------------------

5) Command Snippets (Windows/PowerShell)

Run API locally
- uvicorn src.main:app --reload --port 8000

Payment Service read (must include network)
- curl.exe -s -o NUL -w "HTTP %{http_code}\n" -H "Accept: application/json" -H "token: $Env:MASUMI_API_KEY" "$Env:MASUMI_PAYMENT_SERVICE_URL/purchase" -G --data-urlencode "identifierFromPurchaser=<payment_id>" --data-urlencode "network=Preprod"

Prepare purchase (server helper)
- Invoke-RestMethod -Uri "http://127.0.0.1:8000/prepare_purchase?execute=false" -Method GET

Start job (dev)
- $body = @{ input_data = @(@{ key="address"; value="addr1..."}; @{ key="network"; value="preprod"}) } | ConvertTo-Json -Depth 5
- Invoke-RestMethod -Uri "http://127.0.0.1:8000/start_job" -Method POST -ContentType "application/json" -Body $body

-------------------------------------------------------------------------------

6) Timeline Alignment (Survival Plan)

- Day 1–2: DONE (MIP-003 endpoints, heuristics); add tests next
- Day 3: Payments integration: VERIFIED; add refund/idempotency in this next session
- Day 4: Hardening + perf: start logging, rate limiting, and caching now
- Day 5–7: Registry, listing, deploy; then add batch endpoint

-------------------------------------------------------------------------------

7) Backlog (Future)

- Extended heuristics and labels enrichment
- Metrics endpoint and dashboards
- Optional B2B plans and API keys for rate limits/SLA

Acceptance:
- API returns normalized JSON for at least 3 assets under 1s p95

Phase 2 — Sentiment (0.5–1.5 days)
- Twitter/X keyword search for selected asset
- VADER baseline scores
- Optional: LLM classify (OpenRouter) on 20–50 sampled tweets for nuance

Deliverables:
- agents/sentiment.py with unit tests
- Configurable keywords, sample size

Acceptance:
- Returns sentiment score + confidence within cost budget

Phase 3 — Signals/ML (1–2 days)
- Indicators: EMA, MACD, RSI, momentum
- Simple classification of next-horizon up/down using logistic regression
- Optional: shallow LSTM (stretch)

Deliverables:
- agents/signals.py, models/ folder
- Basic backtest over recent window for sanity

Acceptance:
- p95 runtime under 2s on 1 symbol, reasonable accuracy vs. naive baseline

Phase 4 — Reporting (0.5–1 day)
- Markdown/HTML report generation with embedded charts
- Include: summary, sentiment, indicators, recommendation, confidence, disclaimers

Deliverables:
- agents/reporter.py + templates/
- Static chart assets in /reports/<id>/

Acceptance:
- Clean one-pager generated locally in under 2s

Phase 5 — Orchestration & API (0.5–1 day)
- CrewAI workflow wiring (fetch → sentiment → signals → report)
- FastAPI endpoints: POST /analyze, GET /health, GET /pricing

Deliverables:
- main.py, api/routes.py, crew/orchestrator.py

Acceptance:
- End-to-end analysis via HTTP works locally

Phase 6 — Masumi Integration (1–2 days)
- Register agent: unique ID
- Payment guard: verify ADA/USDM payment per request
- Action logs: transaction hash and summary reference

Deliverables:
- masumi/client.py with register/verify functions
- Payment-verified execution path

Acceptance:
- Pay-gated /analyze returns 402 if unpaid; 200 with report when paid

Phase 7 — Packaging & Deploy (0.5–1 day)
- Dockerfile
- Deploy alongside Masumi Node (Railway or similar)
- Public endpoint (or Masumi-native callable agent)

Deliverables:
- Docker image, deployment notes
- Service URL or Masumi registry link

Acceptance:
- Publicly accessible, pay-gated analysis runs successfully

Phase 8 — Tests, Observability, Hardening (0.5–1 day)
- pytest for units + one E2E
- Rate limiting, input validation
- Structured logging, error handling
- Security: .env, key handling, CORS

Phase 9 — Launch & Growth (ongoing)
- Masumi registry listing
- Social posts (X, Reddit)
- Offer free samples and discount codes
- Collect feedback, iterate

## 11) Project Structure (proposed)

/src  
- api/  
  - routes.py  
- agents/  
  - data_fetcher.py  
  - sentiment.py  
  - signals.py  
  - reporter.py  
- crew/  
  - orchestrator.py  
- masumi/  
  - client.py  
- models/  
- templates/  
- utils/  
  - caching.py  
  - indicators.py  
main.py  
requirements.txt  
.env.example  
README.md  
Dockerfile  
reports/ (generated)  
tests/

## 12) Budget (MVP, monthly estimates)

- OpenRouter LLM: $5–$30 (optimize with small, cheap models and caching)
- Blockfrost: Free → Starter paid tier as needed
- Hosting (Railway/similar): $5–$20
- Domain (optional): $10/year

Target gross margin: >70% at low volume; scale margins with caching and indicator-heavy approach.

## 13) Compliance & Security

- Include strong “Not financial advice” disclaimer
- Log only aggregate sentiment (avoid storing PII)
- Never commit secrets; use .env and .gitignore
- Consider regional API compliance (Twitter dev terms, exchange TOS)
- On-chain logs should avoid sensitive data, only hashes/refs

## 14) Roadmap (post-MVP)

- Alerts (webhooks, email, Telegram)
- Portfolio insights (position sizing, risk)
- Multi-asset batching
- Advanced ML and explainability
- Integrations (trading APIs, DeFi protocols)
- Dashboard UI (Next.js) and embedded widgets for partners

## 15) Acceptance Criteria (MVP)

- Pay-per-use, on-chain-verified analysis available publicly
- Report returned in < 5 seconds p95 for a single symbol
- Clear, understandable indicators and sentiment
- At least one paying user or 10+ runs/day within first 2 weeks post-launch
- Error rate < 1% on happy path

## 16) Commands & Setup (Windows-friendly)

Create environment and install deps:
```
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip

pip install crewai fastapi uvicorn[standard] httpx pandas numpy scikit-learn \
matplotlib vaderSentiment python-dotenv blockfrost-python

# Optional (use only if enabling LSTM early)
pip install tensorflow==2.16.1
```

Run API locally:
```
uvicorn main:app --reload --port 8000
```

Example .env.example:
```
OPENROUTER_API_KEY=sk-or-...
COINGECKO_API_KEY=optional-or-empty
CMC_API_KEY=optional
TWITTER_BEARER=...
BLOCKFROST_PROJECT_ID=...
MASUMI_API_KEY=...
MASUMI_AGENT_ID=to-be-set-after-registration
PRICE_PER_REPORT_ADA=0.1
```

## 17) API Sketch (FastAPI)

- POST /analyze
  - Body: { "symbol": "ADA", "horizonHours": 24 }
  - Headers: payment proof or session referencing Masumi tx
  - Response: { "reportUrl": "...", "summary": "...", "txHash": "..." }
- GET /pricing → { "ada": 0.1, "usdm": "auto-converted" }
- GET /health → { "status": "ok" }

## 18) CrewAI Orchestration Sketch (Python)

```python
# crew/orchestrator.py (sketch)
from crewai import Agent, Task, Crew
from agents.data_fetcher import fetch_market_and_onchain
from agents.sentiment import compute_sentiment
from agents.signals import compute_signals
from agents.reporter import generate_report

def run_workflow(symbol: str, horizon_hours: int) -> dict:
    data_agent = Agent(role="DataFetcher", goal="Collect market/on-chain data")
    sentiment_agent = Agent(role="SentimentAnalyst", goal="Score sentiment")
    signal_agent = Agent(role="SignalEngine", goal="Produce indicators/signals")
    reporter_agent = Agent(role="Reporter", goal="Create concise report")

    # Tasks could carry inputs/outputs or use shared context
    data = fetch_market_and_onchain(symbol)
    sentiment = compute_sentiment(symbol, data)
    signals = compute_signals(symbol, data, sentiment, horizon_hours)
    report_path, summary = generate_report(symbol, data, sentiment, signals)

    return {"report_path": report_path, "summary": summary}
```

## 19) Masumi Integration Sketch

```python
# masumi/client.py (pseudocode)
from masumi import AgentClient  # per Masumi SDK docs

client = AgentClient(api_key=os.getenv("MASUMI_API_KEY"))

def register_agent(metadata: dict) -> str:
    agent_id = client.register(metadata=metadata)
    return agent_id

def is_payment_verified(agent_id: str, user_proof: str, price_ada: float) -> bool:
    return client.verify_payment(agent_id=agent_id, proof=user_proof, amount=price_ada)

def log_action(agent_id: str, tx_hash: str, summary_hash: str) -> None:
    client.log(agent_id=agent_id, tx_hash=tx_hash, ref=summary_hash)
```

Use in API guard:
```python
if not is_payment_verified(MASUMI_AGENT_ID, payment_proof, PRICE_PER_REPORT_ADA):
    raise HTTPException(status_code=402, detail="Payment required")
```

## 20) Testing Strategy

- Unit tests for each agent module (pytest)
- E2E test calling /analyze for ADA with a mocked payment
- Property tests for indicators (monotonicity, bounds)
- Load smoke: 10 concurrent requests < 10s total time

## 21) Go-To-Market (first 30 days)

- Masumi registry listing with clear description and sample images
- X/Twitter thread showcasing report examples; tag Cardano/Masumi communities
- Offer first 50 runs free (sponsored) to seed testimonials
- DM micro-influencers/newsletters for embedding the analyst via API
- Enter Masumi hackathon for exposure and prize opportunities

---

Checklist to build:
- Phase 0: Environment and scaffolding
- Phase 1–4: Agents and reporting
- Phase 5: FastAPI + workflow
- Phase 6: Masumi pay-gate and logs
- Phase 7–8: Deploy, test, harden
- Launch: Listing, posts, partnerships

Aim for clarity, reliability, and fast iteration. Start simple, monetize early, and let usage data guide advanced features.
