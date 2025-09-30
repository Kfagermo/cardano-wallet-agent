# Railway Environment Variables Setup

## Current Status
Your Railway service is **failing health checks** because it's missing required environment variables.

## Quick Fix: Add These Variables in Railway Dashboard

### Step 1: Go to Variables Tab
1. Open your Railway project: https://railway.com/project/aa6a16f9-9f6e-4ebc-a90c-aea8fd5f288f
2. Click on **"cardano-wallet-agent"** service
3. Click **"Variables"** tab
4. Click **"+ New Variable"** for each variable below

### Step 2: Add Minimum Variables (to get service running)

Copy and paste these one by one:

```
MASUMI_BYPASS_PAYMENTS=true
```
*Explanation: Enables testing without payment integration*

```
NETWORK=mainnet
```
*Explanation: Uses mainnet (matches your Blockfrost key)*

```
BLOCKFROST_PROJECT_ID=mainnetzD5WcmBu56UNEEXRjQHh0LByan0KYtVt
```
*Explanation: Your Blockfrost API key for on-chain data*

```
AI_ANALYSIS_MODE=deterministic
```
*Explanation: Uses rule-based analysis (no OpenAI cost for now)*

```
LOG_LEVEL=INFO
```
*Explanation: Standard logging level*

### Step 3: Save and Redeploy

Railway will automatically redeploy when you add variables. Wait for the build to complete.

### Step 4: Verify Service is Running

Once deployed, test the health check:
```bash
# Get your service URL from Railway dashboard, then:
curl https://your-service-url.up.railway.app/availability

# Should return:
# {"status":"available","uptime":...,"message":"OK"}
```

---

## Optional: Add AI Analysis (Recommended)

Once the service is running, add OpenAI for intelligent analysis:

### Get OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy the key (starts with `sk-proj-...`)

### Add to Railway
```
OPENAI_API_KEY=sk-proj-your_key_here
```

```
AI_ANALYSIS_MODE=openai
```

**Cost**: ~$0.0002 per analysis (negligible)

---

## Optional: Enable Payment Integration

To enable real payments via Masumi:

### 1. Get Your Payment Service URL

In Railway dashboard:
1. Click on **"masumi-payment-service"** (your other service)
2. Go to **Settings** → **Domains**
3. Copy the URL (e.g., `https://masumi-payment-service-production-xxxxx.up.railway.app`)

### 2. Get Masumi API Key

From your Masumi Payment Service setup (check your notes or deployment logs)

### 3. Get Seller Verification Key

Your Cardano wallet verification key for receiving payments

### 4. Add to Railway

```
MASUMI_BYPASS_PAYMENTS=false
```

```
MASUMI_PAYMENT_SERVICE_URL=https://your-payment-service-url.up.railway.app/api/v1
```

```
MASUMI_API_KEY=your_masumi_api_key_here
```

```
SELLER_VKEY=your_seller_vkey_here
```

---

## Complete Variable List (Reference)

### Required for Basic Operation
- ✅ `MASUMI_BYPASS_PAYMENTS` - Set to `true` for testing, `false` for production
- ✅ `NETWORK` - `mainnet` or `preprod`
- ✅ `BLOCKFROST_PROJECT_ID` - Your Blockfrost API key

### Optional but Recommended
- 🎯 `OPENAI_API_KEY` - For AI-powered analysis
- 🎯 `AI_ANALYSIS_MODE` - `openai`, `crewai`, or `deterministic`
- 🎯 `LOG_LEVEL` - `DEBUG`, `INFO`, `WARNING`, `ERROR`

### Required for Production (Payments)
- 💰 `MASUMI_PAYMENT_SERVICE_URL` - Your payment service URL + `/api/v1`
- 💰 `MASUMI_API_KEY` - Masumi payment service API key
- 💰 `SELLER_VKEY` - Your seller verification key

### Optional Tuning
- ⚙️ `PRICE_PER_ADDRESS_ADA` - Default: `0.05`
- ⚙️ `CACHE_TTL_SEC` - Default: `86400` (24 hours)
- ⚙️ `MASUMI_PAYMENT_TIMEOUT_SEC` - Default: `600` (10 minutes)
- ⚙️ `RATE_LIMIT_RPM` - Default: `60` (requests per minute)

---

## Troubleshooting

### Service Still Failing?

**Check Logs**:
1. In Railway dashboard, click your service
2. Go to **"Deployments"** tab
3. Click latest deployment
4. View logs for errors

**Common Issues**:
- ❌ Missing `BLOCKFROST_PROJECT_ID` → Service can't fetch on-chain data
- ❌ Wrong `NETWORK` value → Must be `mainnet` or `preprod`
- ❌ Invalid Blockfrost key → Check key matches network

### Health Check Failing?

The service must respond to `GET /availability` within 100 seconds.

**Possible causes**:
1. Service not starting (check logs)
2. Port mismatch (Railway sets `$PORT` automatically)
3. Missing dependencies (check build logs)

### Need Help?

Share:
1. Deployment logs from Railway
2. Which variables you've set
3. Error messages

---

## Next Steps After Service is Running

1. ✅ **Test the API**:
   ```bash
   curl https://your-url.up.railway.app/
   curl https://your-url.up.railway.app/input_schema
   ```

2. ✅ **Test wallet analysis**:
   ```bash
   curl -X POST https://your-url.up.railway.app/start_job \
     -H "Content-Type: application/json" \
     -d '{
       "input_data": [
         {"key": "address", "value": "addr1qx2kd28nq8ac5prwg32hhvudlwggpgfp8utlyqxu6wqgz62f79qsdmm5dsknt9ecr5w468r9ey0fxwkdrwh08ly3tu9sy0f4qd"},
         {"key": "network", "value": "mainnet"}
       ]
     }'
   ```

3. ✅ **List on Sokosumi**:
   - See `MASUMI_SOKOSUMI_INTEGRATION.md`
   - Submit form: https://tally.so/r/nPLBaV

---

## Railway CLI Alternative (Optional)

If you want to use CLI instead:

### Install Railway CLI
```powershell
iwr https://railway.app/install.ps1 | iex
```

### Set Variables via CLI
```bash
railway link aa6a16f9-9f6e-4ebc-a90c-aea8fd5f288f

railway variables set MASUMI_BYPASS_PAYMENTS=true
railway variables set NETWORK=mainnet
railway variables set BLOCKFROST_PROJECT_ID=mainnetzD5WcmBu56UNEEXRjQHh0LByan0KYtVt
railway variables set AI_ANALYSIS_MODE=deterministic
railway variables set LOG_LEVEL=INFO
```

But the dashboard method works just as well!
