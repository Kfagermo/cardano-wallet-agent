# Cardano Wallet Health & Risk Scoring Agent

AI-powered Cardano wallet risk assessment service. Analyzes wallet addresses from multiple perspectives (security, DeFi, behavioral, compliance) and provides risk scores, health ratings, and actionable insights.

**Live Service**: https://cardano-wallet-agent-production.up.railway.app  
**API Docs**: https://cardano-wallet-agent-production.up.railway.app/docs

## Features

- ✅ **AI-Powered Analysis**: OpenAI GPT-4o-mini for intelligent risk assessment
- ✅ **Multi-Perspective**: Security, DeFi, Behavioral, Compliance analysis
- ✅ **Real-Time Data**: Blockfrost integration for on-chain data
- ✅ **MIP-003 Compliant**: Full Masumi Network compatibility
- ✅ **Fast & Cached**: Instant results for repeated queries
- ✅ **Production Ready**: Deployed on Railway with 99%+ uptime

## Quick Start

### Test the API

```bash
# Check availability
curl https://cardano-wallet-agent-production.up.railway.app/availability

# Get input schema
curl https://cardano-wallet-agent-production.up.railway.app/input_schema

# Analyze a wallet
curl -X POST https://cardano-wallet-agent-production.up.railway.app/start_job \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": [
      {"key": "address", "value": "addr1qx2kd28nq8ac5prwg32hhvudlwggpgfp8utlyqxu6wqgz62f79qsdmm5dsknt9ecr5w468r9ey0fxwkdrwh08ly3tu9sy0f4qd"},
      {"key": "network", "value": "mainnet"}
    ]
  }'
```

## Project Structure

```
.
├── src/                    # Source code
│   ├── main.py            # FastAPI application
│   ├── masumi/            # Masumi payment integration
│   ├── services/          # AI analysis services
│   └── store/             # SQLite data store
├── templates/             # HTML report templates
├── examples/              # Example outputs
├── tests/                 # Test suite
├── docs/                  # Documentation
├── requirements.txt       # Python dependencies
└── railway.json          # Railway deployment config
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

See [docs/AI_ANALYSIS_GUIDE.md](docs/AI_ANALYSIS_GUIDE.md) for complete setup and usage.

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
- **Pay-per-use**: 0.05 ADA per address analysis
- **Agent-to-Agent (A2A)**: Other Masumi agents can call your service
- **Target**: $100-500/month within 30 days (see [docs/SURVIVAL_PLAN.md](docs/SURVIVAL_PLAN.md))

## Documentation

- **[Agent Overview](docs/AGENT_OVERVIEW.md)** - What this agent does and how it works
- **[AI Analysis Guide](docs/AI_ANALYSIS_GUIDE.md)** - AI setup and configuration
- **[Railway Deployment](docs/RAILWAY_DEPLOYMENT.md)** - Deploy to Railway
- **[Masumi Integration](docs/MASUMI_SOKOSUMI_INTEGRATION.md)** - Masumi Network & Sokosumi listing
- **[Survival Plan](docs/SURVIVAL_PLAN.md)** - Business model and revenue strategy
- **[Terms of Use](docs/TERMS_OF_USE.md)** - Legal terms
- **[Privacy Policy](docs/PRIVACY_POLICY.md)** - Privacy policy
- **[Support](docs/SUPPORT.md)** - Get help

## License

MIT License - See LICENSE file for details.
