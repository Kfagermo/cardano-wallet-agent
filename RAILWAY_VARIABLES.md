# Railway Environment Variables - Copy/Paste Guide

## Currently Set Variables ✅

These are already configured in Railway:
- ✅ `MASUMI_BYPASS_PAYMENTS=true`
- ✅ `NETWORK=mainnet`
- ✅ `BLOCKFROST_PROJECT_ID=mainnetzD5WcmBu56UNEEXRjQHh0LByan0KYtVt`
- ✅ `AI_ANALYSIS_MODE=deterministic`
- ✅ `LOG_LEVEL=INFO`

---

## Variables to Add in Railway UI

Go to: https://railway.com/project/aa6a16f9-9f6e-4ebc-a90c-aea8fd5f288f
Click: **cardano-wallet-agent** → **Variables** tab → **+ New Variable**

### 🤖 For AI Analysis (Recommended - Add These First)

**Variable Name**: `OPENAI_API_KEY`
**Value**: `sk-proj-your_openai_key_here`
**Where to get**: https://platform.openai.com/api-keys
**Cost**: ~$0.0002 per analysis

---

**Variable Name**: `AI_ANALYSIS_MODE`
**Value**: `openai`
**Options**: `openai` (recommended), `crewai` (advanced), `deterministic` (free)

---

### 💰 For Payment Integration (Add When Ready for Production)

**Variable Name**: `MASUMI_BYPASS_PAYMENTS`
**Value**: `false`
**Note**: Change from `true` to `false` to enable real payments

---

**Variable Name**: `MASUMI_PAYMENT_SERVICE_URL`
**Value**: `https://masumi-payment-service-production.up.railway.app/api/v1`
**Where to get**: From your masumi-payment-service in Railway dashboard → Settings → Domains
**Note**: Must include `/api/v1` at the end

---

**Variable Name**: `MASUMI_API_KEY`
**Value**: `your_masumi_admin_key_here`
**Where to get**: From your Masumi Payment Service setup/deployment logs

---

**Variable Name**: `SELLER_VKEY`
**Value**: `your_cardano_wallet_verification_key`
**Where to get**: From your Cardano wallet (verification key for receiving payments)

---

### ⚙️ Optional Tuning Variables

**Variable Name**: `PRICE_PER_ADDRESS_ADA`
**Value**: `0.05`
**Default**: 0.03
**Recommended**: 0.05 (with AI analysis)

---

**Variable Name**: `CACHE_TTL_SEC`
**Value**: `86400`
**Default**: 86400 (24 hours)
**Note**: How long to cache wallet analysis results

---

**Variable Name**: `MASUMI_PAYMENT_TIMEOUT_SEC`
**Value**: `600`
**Default**: 600 (10 minutes)
**Note**: How long to wait for payment before marking job as failed

---

**Variable Name**: `RATE_LIMIT_RPM`
**Value**: `60`
**Default**: 60 requests per minute per IP
**Increase to**: 120 or 180 if needed

---

## Quick Copy/Paste for Railway UI

### Step 1: Add AI (Do This First)

```
Variable: OPENAI_API_KEY
Value: sk-proj-[GET FROM https://platform.openai.com/api-keys]
```

```
Variable: AI_ANALYSIS_MODE  
Value: openai
```

### Step 2: Enable Payments (When Ready)

```
Variable: MASUMI_BYPASS_PAYMENTS
Value: false
```

```
Variable: MASUMI_PAYMENT_SERVICE_URL
Value: https://masumi-payment-service-production.up.railway.app/api/v1
```

```
Variable: MASUMI_API_KEY
Value: [GET FROM YOUR MASUMI SETUP]
```

```
Variable: SELLER_VKEY
Value: [YOUR CARDANO WALLET VKEY]
```

### Step 3: Optional Pricing

```
Variable: PRICE_PER_ADDRESS_ADA
Value: 0.05
```

---

## How to Add Variables in Railway UI

1. **Open Railway Dashboard**: https://railway.com/project/aa6a16f9-9f6e-4ebc-a90c-aea8fd5f288f

2. **Select Service**: Click "cardano-wallet-agent"

3. **Go to Variables**: Click "Variables" tab

4. **Add Variable**: Click "+ New Variable" button

5. **Enter Details**:
   - **Variable**: Enter the name (e.g., `OPENAI_API_KEY`)
   - **Value**: Enter the value (e.g., `sk-proj-...`)

6. **Save**: Railway automatically saves and redeploys

7. **Repeat**: Add each variable one by one

---

## Verification After Adding Variables

After adding variables, Railway will automatically redeploy. Check if they're set:

```bash
# Via CLI
railway variables

# Or test the service
curl https://cardano-wallet-agent-production.up.railway.app/

# Look for in response:
# "ai": {"mode": "openai", "enabled": true}
```

---

## Priority Order

### 🚀 Start Here (Immediate)
1. `OPENAI_API_KEY` - Enable AI analysis
2. `AI_ANALYSIS_MODE=openai` - Activate AI mode

### 💰 Add Next (Before Listing on Sokosumi)
3. `MASUMI_BYPASS_PAYMENTS=false` - Enable payments
4. `MASUMI_PAYMENT_SERVICE_URL` - Connect to payment service
5. `MASUMI_API_KEY` - Authenticate with payment service
6. `SELLER_VKEY` - Receive payments

### ⚙️ Optional (Fine-tuning)
7. `PRICE_PER_ADDRESS_ADA` - Set pricing
8. `CACHE_TTL_SEC` - Optimize caching
9. `RATE_LIMIT_RPM` - Adjust rate limits

---

## What Happens When You Add Variables

**Railway automatically**:
- Saves the variable
- Triggers a redeploy
- Restarts the service with new config
- Takes 1-2 minutes

**Your service will**:
- Pick up new variables
- Enable new features (AI, payments)
- Continue serving requests

---

## Getting Your Keys

### OpenAI API Key
1. Go to: https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-...`)
5. Add to Railway as `OPENAI_API_KEY`

### Masumi Payment Service URL
1. Go to Railway dashboard
2. Click "masumi-payment-service"
3. Go to "Settings" → "Domains"
4. Copy the URL
5. Add `/api/v1` to the end
6. Example: `https://masumi-payment-service-production-xxxxx.up.railway.app/api/v1`

### Masumi API Key
- Check your Masumi Payment Service deployment logs
- Or check your `.env` file from Masumi setup
- Should be a long string

### Seller VKey
- Your Cardano wallet's verification key
- Used to receive payments
- Get from your Cardano wallet (e.g., Nami, Eternl, Daedalus)

---

## Testing After Adding Variables

### Test AI Analysis
```bash
curl -X POST https://cardano-wallet-agent-production.up.railway.app/start_job \
  -H "Content-Type: application/json" \
  -d @test_request.json

# Check result - should show "analysis_mode": "openai"
curl "https://cardano-wallet-agent-production.up.railway.app/status?job_id=YOUR_JOB_ID"
```

### Test Payment Integration
```bash
# Start a job (should require payment)
curl -X POST https://cardano-wallet-agent-production.up.railway.app/start_job \
  -H "Content-Type: application/json" \
  -d @test_request.json

# Status should show "awaiting payment"
curl "https://cardano-wallet-agent-production.up.railway.app/status?job_id=YOUR_JOB_ID"
```

---

## Need Help?

**If variables don't work**:
1. Check Railway logs: `railway logs`
2. Verify variable names (case-sensitive!)
3. Check for typos in values
4. Ensure URLs include `https://` and `/api/v1`

**If service doesn't restart**:
1. Go to Railway dashboard
2. Click "Deployments"
3. Click "Redeploy" on latest deployment

---

## Summary

**Minimum to get started**: Just add `OPENAI_API_KEY` and set `AI_ANALYSIS_MODE=openai`

**For production**: Add all payment-related variables

**Your service will automatically restart** when you add variables in the Railway UI!
