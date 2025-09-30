# Troubleshooting Railway Deployment

## Current Issue: Healthcheck Failing

### What We've Tried

1. ✅ **Fixed PORT variable** - Changed to use Railway's dynamic `$PORT`
2. ✅ **Increased healthcheck timeout** - From 100s to 300s  
3. ✅ **Reduced workers** - From 2 to 1 for faster startup
4. ✅ **Fixed Dockerfile CMD** - Better shell handling

### Next Steps to Debug

#### 1. Check if App is Actually Starting

The healthcheck might be failing even though the app starts. Test the service directly:

```bash
# Wait 2-3 minutes after deployment, then:
curl https://cardano-wallet-agent-production.up.railway.app/

# If this works but /availability fails, there's a routing issue
```

#### 2. Check Railway Logs for Python Errors

```bash
railway logs | Select-String "Error|Traceback|Exception"
```

**Common Python errors**:
- `ModuleNotFoundError` - Missing dependency in requirements.txt
- `ImportError` - Circular import or missing file
- `SyntaxError` - Python version mismatch

#### 3. Test Locally with Docker

Build and run the exact same Docker image locally:

```bash
# Build
docker build -t wallet-agent .

# Run with same env vars as Railway
docker run -p 8000:8000 \
  -e MASUMI_BYPASS_PAYMENTS=true \
  -e NETWORK=mainnet \
  -e BLOCKFROST_PROJECT_ID=mainnetzD5WcmBu56UNEEXRjQHh0LByan0KYtVt \
  -e AI_ANALYSIS_MODE=deterministic \
  -e LOG_LEVEL=INFO \
  -e PORT=8000 \
  wallet-agent

# Test
curl http://localhost:8000/availability
```

If this works locally but fails on Railway, it's a Railway-specific issue.

#### 4. Simplify the App

Create a minimal test version to isolate the issue:

**Create `test_main.py`**:
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/availability")
def availability():
    return {"status": "available"}
```

**Update railway.json temporarily**:
```json
{
  "deploy": {
    "startCommand": "uvicorn test_main:app --host 0.0.0.0 --port $PORT"
  }
}
```

If this works, the issue is in `src/main.py`.

### Possible Root Causes

#### A. Missing Environment Variable

The app might be crashing because a required env var is missing.

**Check**: Look for this in logs:
```
KeyError: 'SOME_VAR'
ValueError: SOME_VAR not set
```

**Fix**: Add the missing variable:
```bash
railway variables --set "MISSING_VAR=value"
```

#### B. Database/SQLite Issue

The app tries to create `data/app.db` but might not have permissions.

**Check logs for**:
```
sqlite3.OperationalError: unable to open database file
PermissionError: [Errno 13] Permission denied: 'data/app.db'
```

**Fix**: Add a volume in Railway dashboard or use `/tmp`:
```python
# In src/main.py
DB_PATH = os.path.join("/tmp", "app.db")  # Temporary fix
```

#### C. Import Error from AI Dependencies

OpenAI/CrewAI libraries might be failing to import even though we're in deterministic mode.

**Check logs for**:
```
ModuleNotFoundError: No module named 'openai'
ImportError: cannot import name 'create_analyzer'
```

**Fix**: Make AI imports optional:
```python
# In src/main.py
try:
    from src.services.ai_analyzer import create_analyzer
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    create_analyzer = None
```

#### D. Port Binding Issue

The app might be trying to bind to the wrong port.

**Check logs for**:
```
OSError: [Errno 98] Address already in use
OSError: [Errno 99] Cannot assign requested address
```

**Fix**: Ensure `$PORT` is being used correctly (already done in railway.json).

### Alternative: Use Nixpacks Instead of Dockerfile

Railway's Nixpacks might work better than Docker for Python apps.

**Try this**:
1. Rename `Dockerfile` to `Dockerfile.backup`
2. Create `nixpacks.toml`:
```toml
[phases.setup]
nixPkgs = ["python311"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "uvicorn src.main:app --host 0.0.0.0 --port $PORT"
```
3. Push to GitHub
4. Railway will auto-detect and use Nixpacks

### Emergency Fallback: Deploy Without Docker

If Docker keeps failing, deploy directly:

1. Remove `Dockerfile`
2. Railway will auto-detect Python
3. Add `Procfile`:
```
web: uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

### Get Help from Railway

If nothing works, Railway support is very responsive:

1. Go to Railway dashboard
2. Click "Help" → "Contact Support"
3. Share:
   - Project ID: `aa6a16f9-9f6e-4ebc-a90c-aea8fd5f288f`
   - Error: "Healthcheck failing, app not starting"
   - What you've tried (this document)

### Quick Diagnostic Commands

```bash
# Check current deployment status
railway status

# Get last 100 log lines
railway logs --tail 100

# Check environment variables
railway variables

# Force redeploy
railway up --detach

# Open Railway dashboard
railway open
```

### Success Indicators

When it finally works, you'll see:

**In logs**:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:XXXX
```

**In curl**:
```bash
$ curl https://cardano-wallet-agent-production.up.railway.app/availability
{"status":"available","uptime":1234567890,"message":"OK"}
```

**In Railway dashboard**:
- Green checkmark next to deployment
- "Healthy" status
- No error messages

---

## Current Deployment Attempt

**Commit**: `9726958` - "Fix: Increase healthcheck timeout and reduce workers for startup"

**Changes**:
- Workers: 2 → 1
- Healthcheck timeout: 100s → 300s  
- Dockerfile CMD: Improved shell handling

**Expected**: Service should start within 5 minutes

**Monitor**: `railway logs` or Railway dashboard
