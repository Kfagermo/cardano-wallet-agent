# Deployment Status - Cardano Wallet Agent

## ✅ What's Been Done

### 1. GitHub Repository Created
- **URL**: https://github.com/Kfagermo/cardano-wallet-agent
- **Status**: ✅ Live and synced
- **Commits**: 2 (initial + port fix)

### 2. Railway CLI Installed & Configured
- **Version**: railway 4.10.0
- **Logged in as**: Kfagermo@gmail.com
- **Project**: awake-gentleness
- **Service**: cardano-wallet-agent

### 3. Environment Variables Set
```
✅ MASUMI_BYPASS_PAYMENTS=true (testing mode)
✅ NETWORK=mainnet
✅ BLOCKFROST_PROJECT_ID=mainnetzD5WcmBu56UNEEXRjQHh0LByan0KYtVt
✅ AI_ANALYSIS_MODE=deterministic (no OpenAI cost)
✅ LOG_LEVEL=INFO
```

### 4. Critical Fix Applied
**Problem**: Dockerfile was hardcoded to port 8000, but Railway uses dynamic `$PORT`

**Fix**: Changed CMD to use `${PORT:-8000}` (Railway's dynamic port with fallback)

**Commit**: `006f5e2` - "Fix: Use Railway dynamic PORT variable"

## 🚀 Deployment URL

**Service URL**: https://cardano-wallet-agent-production.up.railway.app

**Endpoints**:
- Health: `/availability`
- Schema: `/input_schema`
- Start Job: `POST /start_job`
- Check Status: `GET /status?job_id={uuid}`
- Info: `/`

## 📊 Current Status

**Deployment**: In progress (Railway auto-deploys on git push)

**Expected**: Service should be healthy within 2-3 minutes

## ✅ How to Verify It's Working

### 1. Check Health
```bash
curl https://cardano-wallet-agent-production.up.railway.app/availability
```

**Expected**:
```json
{"status":"available","uptime":1234567890,"message":"OK"}
```

### 2. Check Service Info
```bash
curl https://cardano-wallet-agent-production.up.railway.app/
```

**Expected**:
```json
{
  "name": "Wallet Health & Risk Scoring Agent",
  "version": "0.1.0",
  "ai": {
    "mode": "deterministic",
    "enabled": false
  }
}
```

### 3. Test Wallet Analysis
```bash
curl -X POST https://cardano-wallet-agent-production.up.railway.app/start_job \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": [
      {"key": "address", "value": "addr1qx2kd28nq8ac5prwg32hhvudlwggpgfp8utlyqxu6wqgz62f79qsdmm5dsknt9ecr5w468r9ey0fxwkdrwh08ly3tu9sy0f4qd"},
      {"key": "network", "value": "mainnet"}
    ]
  }'
```

**Expected**:
```json
{"job_id":"uuid-here","payment_id":"uuid-here"}
```

Then check status:
```bash
curl "https://cardano-wallet-agent-production.up.railway.app/status?job_id=YOUR_JOB_ID"
```

## 🔍 Monitoring

### Via Railway CLI
```bash
# Check logs
railway logs

# Check status
railway status

# Check variables
railway variables
```

### Via Railway Dashboard
https://railway.com/project/aa6a16f9-9f6e-4ebc-a90c-aea8fd5f288f

## ⚠️ If Still Failing

### Check Logs
```bash
railway logs --tail 100
```

### Common Issues

**1. Port Mismatch**
- ✅ Fixed: Now using `${PORT:-8000}`

**2. Missing Dependencies**
- Check: `railway logs` for pip install errors
- Solution: Verify `requirements.txt` is complete

**3. Startup Errors**
- Check: Python import errors in logs
- Solution: Verify all files copied correctly

**4. Environment Variables**
- Check: `railway variables`
- Solution: Ensure all required vars are set

## 📋 Next Steps

### Once Service is Healthy

1. **Add OpenAI for AI Analysis** (optional):
   ```bash
   railway variables --set "OPENAI_API_KEY=sk-proj-your_key"
   railway variables --set "AI_ANALYSIS_MODE=openai"
   ```

2. **Enable Payment Integration** (for production):
   ```bash
   # Get your payment service URL from Railway dashboard
   railway variables --set "MASUMI_BYPASS_PAYMENTS=false"
   railway variables --set "MASUMI_PAYMENT_SERVICE_URL=https://your-payment-service.up.railway.app/api/v1"
   railway variables --set "MASUMI_API_KEY=your_key"
   railway variables --set "SELLER_VKEY=your_vkey"
   ```

3. **List on Sokosumi**:
   - Generate 3 example outputs
   - Take screenshots
   - Submit form: https://tally.so/r/nPLBaV

## 🎯 Current Configuration

**Mode**: Testing (bypass payments)
**Network**: Mainnet
**AI**: Deterministic (rule-based, no API cost)
**Blockfrost**: Enabled (real on-chain data)

**This configuration allows**:
- ✅ Test wallet analysis without payments
- ✅ Real Blockfrost data from mainnet
- ✅ Fast responses (no AI API calls)
- ✅ Zero ongoing costs

**To upgrade to production**:
- Add OpenAI key for AI analysis
- Add Masumi payment integration
- Set `MASUMI_BYPASS_PAYMENTS=false`

## 📞 Support

**Railway Docs**: https://docs.railway.com
**Project URL**: https://railway.com/project/aa6a16f9-9f6e-4ebc-a90c-aea8fd5f288f
**GitHub Repo**: https://github.com/Kfagermo/cardano-wallet-agent

---

**Last Updated**: 2025-09-30 15:52 UTC
**Status**: Deploying (waiting for health check to pass)
