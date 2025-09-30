# Crypto Analyst Agent (Masumi MIP-003) — Quickstart

Python + FastAPI implementation of a Masumi-compatible Agentic Service focused on Cardano Wallet Health & Risk Scoring. This is the fastest path to ship, monetize via Masumi payments, and list on Sokosumi with minimal marketing.

- Endpoints: `/availability`, `/input_schema`, `/start_job`, `/status`
- Report template: `templates/wallet_report.html` (responsive, dark-mode aware)
- Output: Deterministic JSON + rendered HTML report (saved to `reports/`)

Why Python?
- Minimal boilerplate to implement MIP-003 endpoints
- Great ecosystem for HTTP, templating (Jinja2), and future data/ML
- Works well on low-cost infra or Kodosumi; no LLMs required for MVP

## Project Structure

```
.
├─ src/
│  └─ main.py                    # FastAPI app, in-memory jobs, HTML render
├─ templates/
│  └─ wallet_report.html         # Jinja2 report template
├─ reports/                      # Generated HTML reports (created at runtime)
├─ requirements.txt
├─ SURVIVAL_PLAN.md              # Survival-mode plan to earn quickly on Masumi
├─ BUILD_PLAN.md                 # Broader build plan
└─ README.md
```

## Prerequisites

- Python 3.11+ (Windows: use the `py` launcher)
- pip (or uv) and virtual environment
- (Optional) Blockfrost API key for real on-chain data
- (Optional) Masumi Payment Service for live payment gating

## Setup (Windows 11 friendly)

Create and activate a virtual environment:
```
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
```

Install dependencies:
```
pip install -r requirements.txt
```

Environment variables (create `.env` if you prefer dotenv):
```
# .env example
MASUMI_BYPASS_PAYMENTS=true   # dev-only, auto-runs job without payment
NETWORK=mainnet               # or preprod
BLOCKFROST_PROJECT_ID=        # optional for real on-chain reads later
MASUMI_PAYMENT_SERVICE_URL=   # for real payment verification later
MASUMI_API_KEY=               # for Payment Service auth if needed
```

Note: The service loads env from the OS; if using python-dotenv, add a loader (see “Enable dotenv” below).

## Run

From repo root:
```
uvicorn src.main:app --reload --port 8000
```

Open interactive docs:
- http://localhost:8000/docs

## API (MIP-003)

1) Availability
```
GET /availability
```

2) Input schema
```
GET /input_schema
```
Example response:
```json
{
  "input_data": [
    {"key": "address", "value": "string"},
    {"key": "network", "value": "string"}
  ]
}
```

3) Start job
```
POST /start_job
Content-Type: application/json
```
Example payload:
```json
{
  "input_data": [
    { "key": "address", "value": "addr1qx..." },
    { "key": "network", "value": "mainnet" }
  ]
}
```
Example response:
```json
{
  "job_id": "c2a2f69c-...-....",
  "payment_id": "a6c0b0b1-...-...."
}
```

4) Check status
```
GET /status?job_id={UUID}
```
Example response (dev mode BYPASS_PAYMENTS=true):
```json
{
  "job_id": "c2a2f69c-...-....",
  "status": "completed",
  "result": "reports/c2a2f69c-...-.....html"
}
```

Open the `reports/{job_id}.html` file in your browser to view the rendered report.

## cURL Examples

Start a job:
```
curl -s -X POST http://localhost:8000/start_job ^
  -H "Content-Type: application/json" ^
  -d "{ \"input_data\": [ {\"key\":\"address\",\"value\":\"addr1...\"}, {\"key\":\"network\",\"value\":\"mainnet\"} ] }"
```

Check status:
```
curl -s "http://localhost:8000/status?job_id=YOUR_JOB_ID"
```

## Template Variables (wallet_report.html)

- `address`, `network`, `generated_at`
- `risk_score` (0–100), `health` (`safe|caution|risky`), `health_class`
- `first_seen`, `age_days`, `tx_velocity_30d`, `counterparty_diversity_90d`
- `reasons` (list)
- `balances`, `staking`, `known_label`, `top_tokens`
- `price_chart_base64` (optional), `symbol`, `window_label`, `indicators_summary`
- `raw_json_pretty`, `raw_json`

The template sets the progress bar width client-side from `data-risk="{{ risk_score }}"` to avoid CSS lint issues.

## Development Notes

- Current on-chain data is stubbed in `_fetch_onchain_minimal`. Replace with real Blockfrost calls using `blockfrost-python` when ready.
- Payments are bypassed by default for development. Set `MASUMI_BYPASS_PAYMENTS=false` and implement Payment Service verification logic before production.

Enable dotenv (optional):
```python
# at the top of src/main.py
from dotenv import load_dotenv
load_dotenv()
```

## Next Steps (toward production)

- Set up Masumi Payment Service and obtain ADMIN_KEY (see MASUMI_SETUP.md). Configure:
  - MASUMI_PAYMENT_SERVICE_URL (must include /api/v1)
  - MASUMI_API_KEY (your Admin Key or a limited-scope API key)
- Integrate Blockfrost:
  - Pull balances, staking state, and tx history for real data.
- Integrate Masumi Payment Service:
  - On `/start_job`, create a purchase requirement and keep `status=awaiting payment`.
  - After payment confirmation, run the job and update `status`.
  - Honor timeouts and provide refunds per docs.
- Persist jobs:
  - Move from in-memory store to SQLite/Redis.
- Register and list:
  - Register the agent on Masumi and list on Sokosumi with schema, price (e.g., 0.03 ADA), and example screenshots.
- Hardening:
  - Input validation, rate limiting, structured logging, tests.

## Deployment

### Quick Deploy to Railway (Recommended)

**One-command deployment** with automatic HTTPS and monitoring:

```bash
# Install Railway CLI
iwr https://railway.app/install.ps1 | iex

# Login and deploy
railway login
railway init
railway up
```

See **RAILWAY_DEPLOYMENT.md** for complete Railway setup guide.

### Other Options

See **DEPLOYMENT.md** for:
- **Kodosumi/Docker**: Container-based deployment
- **Ubuntu VPS**: systemd + Nginx + Certbot

Docker quickstart:
```bash
docker build -t wallet-health-agent:latest .
docker run --rm -p 8000:8000 ^
  -e MASUMI_BYPASS_PAYMENTS=false ^
  -e NETWORK=preprod ^
  -e BLOCKFROST_PROJECT_ID=... ^
  -e MASUMI_PAYMENT_SERVICE_URL=https://.../api/v1 ^
  -e MASUMI_API_KEY=... ^
  -e SELLER_VKEY=... ^
  wallet-health-agent:latest
```

## AI-Powered Analysis 🤖

This agent now includes **true AI reasoning** using OpenAI GPT models:

- **OpenAI Mode**: Single AI agent with multi-perspective analysis (recommended)
- **CrewAI Mode**: 5 specialized AI agents collaborating (premium tier)
- **Deterministic Mode**: Rule-based fallback (no API costs)

**Why AI matters**: Masumi guidelines require intelligent reasoning from multiple perspectives (security, DeFi, behavioral, compliance), not just simple if/else rules.

See **AI_ANALYSIS_GUIDE.md** for complete setup and usage.

### Quick AI Setup

```bash
# Get OpenAI API key from https://platform.openai.com/api-keys
railway variables set OPENAI_API_KEY="sk-proj-..."
railway variables set AI_ANALYSIS_MODE="openai"
railway up
```

**Cost**: ~$0.0002 per analysis (negligible with 90%+ margins)

## Masumi & Sokosumi Integration

This agent is **MIP-003 compliant** and ready to list on Sokosumi marketplace:

- **Masumi Network**: https://www.masumi.network
- **Sokosumi Marketplace**: https://www.sokosumi.com
- **Integration Guide**: See **MASUMI_SOKOSUMI_INTEGRATION.md**
- **Listing Form**: https://tally.so/r/nPLBaV

### Revenue Model
- **Pay-per-use**: 0.05-0.10 ADA per address (AI-powered = premium pricing)
- **Agent-to-Agent (A2A)**: Other agents call your service
- **Target**: $100-500/month within 30 days (see SURVIVAL_PLAN.md)

## License

Proprietary for now (adjust as needed).
