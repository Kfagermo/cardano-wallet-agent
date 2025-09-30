# Environment Variables Template

This document lists all environment variables used by the Cardano Wallet Agent.

## How to Use

**For Railway**: Set these in the Railway dashboard under Variables tab  
**For Local**: Create a `.env` file in the project root (never commit this!)

## Required for Production

| Variable | Description | Example |
|----------|-------------|---------|
| `MASUMI_BYPASS_PAYMENTS` | Payment bypass (MUST be `false` in production) | `false` |
| `NETWORK` | Cardano network | `mainnet` or `preprod` |
| `SELLER_VKEY` | Your seller verification key | `your_seller_vkey_here` |
| `MASUMI_PAYMENT_SERVICE_URL` | Masumi Payment Service URL (must include `/api/v1`) | `https://your-service.com/api/v1` |
| `MASUMI_API_KEY` | Masumi API key | `your_masumi_api_key_here` |

## Optional but Recommended

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `BLOCKFROST_PROJECT_ID` | Blockfrost API key for on-chain data | - | `mainnetABC123...` |
| `OPENAI_API_KEY` | OpenAI API key for AI analysis | - | `sk-proj-...` |
| `AI_ANALYSIS_MODE` | AI mode: `openai`, `crewai`, or `deterministic` | `deterministic` | `openai` |
| `PRICE_PER_ADDRESS_ADA` | Price per analysis (reference only) | `0.03` | `0.05` |
| `CACHE_TTL_SEC` | Cache duration in seconds | `86400` | `86400` (24h) |
| `MASUMI_PAYMENT_TIMEOUT_SEC` | Payment timeout | `600` | `600` (10min) |
| `IDEMPOTENCY_WINDOW_SEC` | Idempotency window | `600` | `600` (10min) |
| `LOG_LEVEL` | Logging level | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `RATE_LIMIT_RPM` | Rate limit (requests/min/IP) | `60` | `60` |

## Railway-Specific

| Variable | Description | Note |
|----------|-------------|------|
| `PORT` | Server port | ⚠️ Set automatically by Railway - do not override |

## Security Notes

1. ⚠️ **Never commit `.env` files** with real values to git
2. 🔄 **Rotate keys regularly** - especially `MASUMI_API_KEY` and `SELLER_VKEY`
3. 🔒 **Use Railway dashboard** to manage secrets securely
4. 🎯 **Separate environments** - Use different keys for dev/staging/production

## Quick Setup (Railway CLI)

```bash
# Set all variables at once (replace values first)
railway variables set MASUMI_BYPASS_PAYMENTS=false
railway variables set NETWORK=mainnet
railway variables set SELLER_VKEY="your_seller_vkey_here"
railway variables set MASUMI_PAYMENT_SERVICE_URL="https://your-payment-service.com/api/v1"
railway variables set MASUMI_API_KEY="your_masumi_api_key_here"
railway variables set BLOCKFROST_PROJECT_ID="your_blockfrost_key"
railway variables set OPENAI_API_KEY="sk-proj-your_key"
railway variables set AI_ANALYSIS_MODE="openai"
railway variables set PRICE_PER_ADDRESS_ADA=0.05
railway variables set LOG_LEVEL=INFO
```

## Local Development

Create a `.env` file in the project root:

```bash
# .env (never commit this!)
MASUMI_BYPASS_PAYMENTS=true
NETWORK=preprod
BLOCKFROST_PROJECT_ID=preprodABC123...
OPENAI_API_KEY=sk-proj-...
AI_ANALYSIS_MODE=openai
LOG_LEVEL=DEBUG
```
