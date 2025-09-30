# Railway Deployment Guide — Wallet Health & Risk Scoring Agent

This guide shows how to deploy your Masumi MIP-003 compliant agent to Railway.com for use as a rentable AI agent on Masumi Network and Sokosumi marketplace.

## Why Railway?

- **One-command deployment** with Railway CLI
- **Automatic HTTPS** with custom domains
- **Built-in monitoring** and logs
- **$5/month starter plan** (500 hours free trial)
- **Perfect for Masumi agents** - stable public URL, 99%+ uptime
- **Persistent volumes** for SQLite database

## Prerequisites

1. **Railway Account**: Sign up at https://railway.app
2. **Railway CLI**: Install from https://docs.railway.com/guides/cli
3. **GitHub/GitLab** (optional): For automatic deployments

## Quick Start (Railway CLI)

### 1. Install Railway CLI

**Windows (PowerShell):**
```powershell
iwr https://railway.app/install.ps1 | iex
```

**macOS/Linux:**
```bash
curl -fsSL https://railway.app/install.sh | sh
```

### 2. Login to Railway

```bash
railway login
```

This opens your browser to authenticate.

### 3. Initialize Project

From your project root (`h:\Code\cryptoAnalyst`):

```bash
railway init
```

Choose:
- **Create new project** or link to existing
- Name it: `cardano-wallet-agent` (or your preference)

### 4. Set Environment Variables

Railway needs these production variables:

```bash
# Required for production
railway variables set MASUMI_BYPASS_PAYMENTS=false
railway variables set NETWORK=preprod
railway variables set SELLER_VKEY="your_seller_vkey_here"
railway variables set MASUMI_PAYMENT_SERVICE_URL="https://your-payment-service.com/api/v1"
railway variables set MASUMI_API_KEY="your_masumi_api_key_here"

# Optional but recommended
railway variables set BLOCKFROST_PROJECT_ID="your_blockfrost_key"
railway variables set PRICE_PER_ADDRESS_ADA=0.05
railway variables set CACHE_TTL_SEC=86400
railway variables set MASUMI_PAYMENT_TIMEOUT_SEC=600
railway variables set LOG_LEVEL=INFO
railway variables set RATE_LIMIT_RPM=60

# AI-powered analysis (HIGHLY RECOMMENDED for premium positioning)
railway variables set OPENAI_API_KEY="sk-proj-your_key_here"
railway variables set AI_ANALYSIS_MODE="openai"
```

**Important Security Notes:**
- Never commit these values to git
- Rotate `MASUMI_API_KEY` and `SELLER_VKEY` before production launch
- Use Railway's dashboard to manage secrets securely

### 5. Add Persistent Volume (for SQLite)

Railway provides persistent volumes to keep your database across deployments:

```bash
railway volume create
```

When prompted:
- **Name**: `wallet-agent-data`
- **Mount path**: `/app/data`

This ensures your SQLite database (`data/app.db`) persists across restarts.

### 6. Deploy

```bash
railway up
```

Railway will:
1. Build your Docker image
2. Deploy to their infrastructure
3. Assign a public URL (e.g., `https://cardano-wallet-agent-production.up.railway.app`)
4. Start health checks on `/availability`

### 7. Get Your Public URL

```bash
railway domain
```

This shows your assigned Railway domain. You can also add a custom domain:

```bash
railway domain add yourdomain.com
```

### 8. View Logs

```bash
railway logs
```

Monitor your agent's structured JSON logs in real-time.

## Alternative: Deploy via GitHub

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit - Masumi wallet agent"
git remote add origin https://github.com/yourusername/cardano-wallet-agent.git
git push -u origin main
```

### 2. Connect to Railway

1. Go to https://railway.app/new
2. Click **Deploy from GitHub repo**
3. Select your repository
4. Railway auto-detects the Dockerfile
5. Add environment variables in the dashboard
6. Click **Deploy**

Railway will automatically redeploy on every git push to `main`.

## Post-Deployment Checklist

### 1. Verify Endpoints

Test your deployed agent:

```bash
# Get your Railway URL
RAILWAY_URL=$(railway domain)

# Test availability
curl https://$RAILWAY_URL/availability

# Test input schema
curl https://$RAILWAY_URL/input_schema

# Test payment information
curl "https://$RAILWAY_URL/payment_information?payment_id=test-123"
```

Expected responses:
- `/availability`: `{"status":"available","uptime":...}`
- `/input_schema`: MIP-003 schema with address/network fields
- `/payment_information`: Payment details and refund policy

### 2. Run End-to-End Test

**Important**: Test with `MASUMI_BYPASS_PAYMENTS=false` to validate the full payment flow:

```bash
# Start a job
curl -X POST https://$RAILWAY_URL/start_job \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": [
      {"key": "address", "value": "addr1qx2kd28nq8ac5prwg32hhvudlwggpgfp8utlyqxu6wqgz62f79qsdmm5dsknt9ecr5w468r9ey0fxwkdrwh08ly3tu9sy0f4qd"},
      {"key": "network", "value": "preprod"}
    ]
  }'

# Response: {"job_id":"...","payment_id":"..."}

# Check status (should be "awaiting payment" initially)
curl "https://$RAILWAY_URL/status?job_id=YOUR_JOB_ID"
```

### 3. Configure Custom Domain (Optional)

For production, use a custom domain for your Masumi agent:

```bash
railway domain add agent.yourdomain.com
```

Then add a CNAME record in your DNS:
- **Type**: CNAME
- **Name**: agent
- **Value**: [your-railway-domain].up.railway.app

Railway automatically provisions SSL certificates.

## Register on Masumi & List on Sokosumi

### 1. Register Your Agent

Once deployed, register your agent on Masumi:

**Agent Details:**
- **Name**: Cardano Wallet Health & Risk Scoring Agent
- **URL**: `https://your-railway-domain.up.railway.app`
- **MIP-003 Compliant**: Yes
- **Endpoints**: `/availability`, `/input_schema`, `/start_job`, `/status`

Follow: https://docs.masumi.network/documentation/how-to-guides/how-to-enable-agent-collaboration

### 2. List on Sokosumi Marketplace

Submit your agent to Sokosumi for discovery:

**Listing Form**: https://tally.so/r/nPLBaV

**Required Information:**
- **Agent Name**: Cardano Wallet Health & Risk Scoring Agent
- **Description**: Deterministic on-chain wallet analysis with risk scoring (0-100), health classification (safe/caution/risky), and detailed insights on balances, staking, transaction velocity, and counterparty diversity.
- **Pricing**: 0.05 ADA per address (or your chosen price)
- **SLOs**: 
  - Availability: 99%+
  - Latency: <500ms cached, <2s cold
- **Input Schema**: 
  ```json
  {
    "input_data": [
      {"key": "address", "value": "string"},
      {"key": "network", "value": "string"}
    ]
  }
  ```
- **Example Output**: See `examples/` directory or generate via `/start_job`
- **Use Cases**: 
  - Agent-to-agent wallet verification
  - DeFi risk assessment
  - Portfolio health monitoring
  - Compliance screening

**Screenshots**: Generate 2-3 example reports and include:
1. API response JSON
2. HTML report (from `reports/` directory)
3. Health score visualization

### 3. Enable Agent-to-Agent (A2A) Consumption

Your agent is now discoverable by other Masumi agents. They can call your service programmatically:

**A2A Flow:**
1. Agent A needs wallet risk score
2. Agent A calls your `/start_job` with address
3. Your agent returns `job_id` and `payment_id`
4. Agent A pays via Masumi Payment Service
5. Your agent processes and returns result via `/status`

This creates a **revenue stream from other agents** using your service as infrastructure.

## Monitoring & Maintenance

### View Logs

```bash
railway logs --follow
```

Your structured JSON logs include:
- `event`: Event type (start_job_received, payment_confirmed, job_completed, etc.)
- `job_id`: Correlation ID
- `ts`: Unix timestamp
- Additional context per event

### Monitor Metrics

Railway dashboard shows:
- **CPU/Memory usage**
- **Request count**
- **Response times**
- **Error rates**

Set up alerts for:
- Availability < 99%
- P95 latency > 2s
- Error rate > 1%

### Database Backups

Your SQLite database is in the persistent volume. To backup:

```bash
# Connect to Railway shell
railway run bash

# Inside container
cp /app/data/app.db /app/data/app.db.backup

# Or download locally
railway run cat /app/data/app.db > backup-$(date +%Y%m%d).db
```

Schedule weekly backups if job history is critical.

### Scaling

Railway auto-scales based on load. For higher traffic:

1. **Increase workers**: Edit `railway.json` startCommand to `--workers 4`
2. **Upgrade plan**: Railway Pro ($20/mo) for more resources
3. **Add caching**: Your agent already uses SQLite cache with TTL
4. **Optimize queries**: Blockfrost calls are cached; tune `CACHE_TTL_SEC`

## Cost Estimates

**Railway Pricing:**
- **Starter**: $5/month (500 hours free trial)
- **Pro**: $20/month (more resources, priority support)

**Additional Costs:**
- **Blockfrost**: Free tier → Starter ($9/mo) as needed
- **OpenAI API**: ~$0.0002 per analysis (GPT-4o-mini)
  - 300 analyses/month = $0.06/month
  - With 70% cache hit rate = ~$0.02/month effective cost
- **Domain**: $10-15/year (optional)

**Revenue Potential** (from SURVIVAL_PLAN.md):
- Marketplace-only: 10-50 paid runs/month
- With ecosystem promotion: 100-300 paid runs/month
- B2B plans: $19-49/month per customer
- **Target**: $100-500/month within 30 days

**Gross Margin**: >80% with caching (most requests hit cache, minimal Blockfrost costs)

## Troubleshooting

### Build Fails

**Issue**: Docker build fails on Railway

**Solution**: Check `railway logs --build` for errors. Common fixes:
- Ensure `requirements.txt` is up to date
- Verify Dockerfile syntax
- Check for missing dependencies

### Health Check Fails

**Issue**: Railway marks service as unhealthy

**Solution**: 
```bash
# Test locally first
curl https://your-railway-domain.up.railway.app/availability

# Should return: {"status":"available","uptime":...}
```

If it fails, check:
- `PORT` environment variable is used (Railway sets this dynamically)
- Dockerfile `EXPOSE 8000` matches your startCommand port
- `/availability` endpoint is accessible

### Payment Verification Fails

**Issue**: Jobs stuck in "awaiting payment"

**Solution**:
1. Verify `MASUMI_PAYMENT_SERVICE_URL` includes `/api/v1`
2. Check `MASUMI_API_KEY` is correct (header: `token`)
3. Ensure `network` parameter is `Preprod` or `Mainnet` (capitalized)
4. Test payment service directly:
   ```bash
   curl -H "token: YOUR_API_KEY" \
     "https://your-payment-service.com/api/v1/purchase?identifierFromPurchaser=test-id&network=Preprod"
   ```

### Database Locked

**Issue**: SQLite database locked errors

**Solution**: 
- Railway persistent volumes are single-instance (no concurrent writes)
- If using multiple workers, consider Redis for job queue
- Current setup with `--workers 2` is safe for SQLite

## Security Best Practices

1. **Rotate Secrets**: Before production launch
   ```bash
   railway variables set MASUMI_API_KEY="new_key_here"
   railway variables set SELLER_VKEY="new_vkey_here"
   ```

2. **Rate Limiting**: Already enabled (60 RPM default)
   ```bash
   railway variables set RATE_LIMIT_RPM=120  # Increase if needed
   ```

3. **HTTPS Only**: Railway provides automatic SSL
   - Never expose HTTP endpoints
   - Use Railway domains or custom domains with SSL

4. **Environment Variables**: Never commit to git
   - Use `.env` locally (gitignored)
   - Use Railway dashboard/CLI for production

5. **API Key Scope**: Use limited-scope Masumi API keys
   - Separate keys for dev/prod
   - Rotate monthly

## Next Steps

1. **Deploy to Railway** using this guide
2. **Test end-to-end** with real Masumi payments
3. **Generate example outputs** (3+ JSON responses + HTML reports)
4. **Submit Sokosumi listing** with screenshots and pricing
5. **Announce in Masumi community** (Discord, forums)
6. **Monitor KPIs** (see SURVIVAL_PLAN.md Section 8)

## AI Analysis Setup

Your agent now supports **AI-powered analysis** using OpenAI GPT models. This is **highly recommended** for premium positioning on Sokosumi.

### Quick Setup

```bash
# Get API key from https://platform.openai.com/api-keys
railway variables set OPENAI_API_KEY="sk-proj-..."
railway variables set AI_ANALYSIS_MODE="openai"
railway up
```

### Verify AI is Working

```bash
curl https://your-railway-domain.up.railway.app/

# Look for:
# "ai": {
#   "mode": "openai",
#   "enabled": true
# }
```

See **AI_ANALYSIS_GUIDE.md** for complete documentation.

## Resources

- **Railway Docs**: https://docs.railway.com
- **Railway CLI Guide**: https://docs.railway.com/guides/cli
- **Masumi Docs**: https://docs.masumi.network
- **Sokosumi Listing**: https://tally.so/r/nPLBaV
- **MIP-003 Spec**: https://docs.masumi.network/documentation/technical-documentation/agentic-service-api
- **OpenAI Platform**: https://platform.openai.com
- **AI Analysis Guide**: See AI_ANALYSIS_GUIDE.md

## Support

- **Railway**: https://railway.app/help
- **Masumi Discord**: https://discord.gg/masumi
- **Project Issues**: File issues in your GitHub repo

---

**You're now ready to deploy a production Masumi agent on Railway and start earning on Sokosumi!** 🚀
