# Railway Setup — Troubleshooting “Application failed to respond”

Symptom
- URL used: `masumi-psql-database-production.up.railway.app`
- Result: “Application failed to respond”
- Logs show PostgreSQL activity and background workers (checkpoint, state monitoring)

Root cause
- That URL is your PostgreSQL service (database), not the Masumi Payment Service app.
- The DB service doesn’t expose an HTTP admin panel; it’s normal for a DB URL to fail HTTP requests.
- You must open/generate the URL for the Masumi Payment Service (the Node.js app), not the DB.

What you should have after deploying the template
- Two services on your Railway project canvas:
  1) PostgreSQL database (often named like “masumi-psql-database-production”)
  2) Masumi Payment Service (the actual web app/API you call)
- You must generate a public URL for the Masumi Payment Service (not the DB).

Fix — get the correct Payment Service URL
1) In Railway, open your project canvas.
2) Click the Masumi Payment Service service (NOT the Postgres/psql service).
3) Go to: Settings → Networking → Generate URL.
   - You’ll get something like: `https://your-masumi-service.up.railway.app`
4) Open:
   - Admin UI: `https://your-masumi-service.up.railway.app/admin`
   - Swagger: `https://your-masumi-service.up.railway.app/docs`
   - Health: `https://your-masumi-service.up.railway.app/api/v1/health/`
5) Variables for the Payment Service must include:
   - `ADMIN_KEY` (≥ 15 chars) → this is your Masumi API key (you can change/rotate it later)
   - `ENCRYPTION_KEY` (64 hex characters)
   - `BLOCKFROST_API_KEY_PREPROD` (for preprod/test)
   - DB connection string is auto-wired by the template

Configure this project (.env)
- Set these values in h:\Code\cryptoAnalyst\.env:
```
MASUMI_PAYMENT_SERVICE_URL=https://your-masumi-service.up.railway.app/api/v1
MASUMI_API_KEY=YOUR_ADMIN_KEY
SELLER_VKEY=from Admin > Selling wallet page
# Flip to false only when ready to enforce payments
MASUMI_BYPASS_PAYMENTS=false
```

Verify the Payment Service
- From a browser: open `/admin` (login with `ADMIN_KEY`)
- From a terminal (PowerShell):
```
curl.exe -s https://your-masumi-service.up.railway.app/api/v1/health/
```
Expected JSON (shape may vary):
```
{"status":"success","data":{"status":"ok"}}
```

Test end-to-end with our service (once URL/key set)
1) Start a job:
```
$payload = @{ input_data = @(@{ key = "address"; value = "addr1..." }, @{ key = "network"; value = "preprod" }) } | ConvertTo-Json -Depth 5
$resp = Invoke-RestMethod -Uri http://127.0.0.1:8000/start_job -Method POST -ContentType "application/json" -Body $payload
$resp
```
2) Get payment info:
```
Invoke-RestMethod -Uri ("http://127.0.0.1:8000/payment_information?payment_id=" + $resp.payment_id) -Method GET
```
3) Pay on Payment Service (in its `/docs`, call POST `/purchase` using your `payment_id`)
4) Poll status in our service:
```
Invoke-RestMethod -Uri ("http://127.0.0.1:8000/status?job_id=" + $resp.job_id) -Method GET
```
5) When it switches to `completed`, a report path will be returned.

Notes
- Always append `/api/v1` to `MASUMI_PAYMENT_SERVICE_URL`.
- Use preprod/test funds first (see docs for the tADA dispenser).
- If `/admin` or `/docs` isn’t available, you are on the DB service URL; return to the canvas and select the app service.
- Keep `MASUMI_BYPASS_PAYMENTS=true` until you confirm the Payment Service is reachable; then set it to `false` to enforce pay-to-run.
