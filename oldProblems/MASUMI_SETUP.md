# Masumi API Key (Payment Service) — Setup Guide

Goal: Get a “Masumi API key” you can use to protect payments and call the Payment Service from your agent.

Important terminology
- The “Masumi API key” is the Payment Service ADMIN_KEY (or an API key you create in the admin panel). This key is used to:
  - Log in to the Payment Service Admin UI
  - Authenticate API requests (e.g., POST /purchase)
  - Optionally mint additional limited-scope API keys

Docs reference
- Installation: https://docs.masumi.network/documentation/get-started/installation
- Env vars: https://docs.masumi.network/documentation/technical-documentation/environment-variables
- Collaboration/payment flow: https://docs.masumi.network/documentation/how-to-guides/how-to-enable-agent-collaboration

## Option A — Quickstart with Docker Compose (local)

Prereqs
- Docker Desktop (Compose included)
- Blockfrost API key (you already have one)

Steps
1) Clone quickstart:
   git clone https://github.com/masumi-network/masumi-services-dev-quickstart.git
   cd masumi-services-dev-quickstart

2) Copy env and fill values:
   cp .env.example .env

   Required variables (see docs for full list):
   - ENCRYPTION_KEY=<random 64 hex chars>
   - ADMIN_KEY=<your long admin key, >= 15 chars>
   - BLOCKFROST_API_KEY_PREPROD=<your key>  # for preprod/test
   - (wallet variables will be created/filled by the service during onboarding if using templates)

   Generate ENCRYPTION_KEY (Windows-friendly):
   .\.venv\Scripts\python - << EOF
   import secrets; print(secrets.token_hex(32))
   EOF

   Pick a strong ADMIN_KEY (>= 15 chars). This is your initial Masumi API key.

3) Start services:
   docker compose up -d

4) Access services:
   - Payment Service Admin: http://localhost:3001/admin
   - Payment Service Swagger: http://localhost:3001/docs

5) Log in to Admin:
   - Use your ADMIN_KEY as the password (per docs: “Admin Key is your password that you will use to access admin interface later”).
   - In the Admin UI you can:
     - Top up wallets (test ADA/USDM)
     - View Selling wallet and copy SELLER_VKEY
     - Create additional API keys (limited scope) if supported by your version

The Payment Service base URL for API calls is:
- http://localhost:3001/api/v1

Use your ADMIN_KEY as the API key (e.g., header x-api-key or according to the Swagger docs on your instance).

## Option B — Railway (hosted quick deploy)

Prereqs
- Railway account
- Blockfrost API key

Steps
1) Deploy Payment Service:
   Use the “Deploy on Railway” button from the docs:
   https://railway.com/deploy/masumi-payment-service-official?referralCode=padierfind

   Provide your Blockfrost key -> deploy -> Generate a public URL for the service.

2) Admin Key on Railway:
   - Your default Admin Key is in Railway Variables after deployment.
   - Open the Admin panel at: https://<your-railway-host>/admin
   - Log in with the Admin Key and CHANGE it in the Admin UI.
   - This Admin Key is your Masumi API key (use as PAYMENT_API_KEY).

3) Verify endpoints:
   - Swagger at https://<your-railway-host>/docs
   - Ensure you prefix /api/v1 in your base URL (e.g., https://<host>/api/v1)

## Using the key in this project

In this repo, configure these env vars (see .env.example):
- MASUMI_PAYMENT_SERVICE_URL=https://<your-host>/api/v1
- MASUMI_API_KEY=<your Admin Key or limited API key>

Note: Current code bypasses payment for development (MASUMI_BYPASS_PAYMENTS=true). Before production:
- Set MASUMI_BYPASS_PAYMENTS=false
- Implement verification:
  - On /start_job, create purchase metadata for Payment Service and return a payment_id
  - Wait for Payment Service confirmation (poll GET /purchase) before running
  - Handle timeouts and refunds (PATCH /purchase) per Masumi docs

## Where to find SELLER_VKEY

- Payment Service Admin UI → Wallets → Selling wallet → Public verification key (SELLER_VKEY)
- Or via API: GET /payment-source/ on the Payment Service

You’ll need SELLER_VKEY if you use the Agentic Service Wrapper or register an agent that receives payments.

## Quick API sanity checks

Health (Payment Service):
curl -s http://localhost:3001/api/v1/health/

Swagger (Payment Service):
http://localhost:3001/docs

Admin UI:
http://localhost:3001/admin
(login with ADMIN_KEY)

## Notes and Tips

- Keep ADMIN_KEY secret; rotate it if leaked. You can create additional API keys in the admin panel for specific services/teams if supported.
- Always include /api/v1 when configuring MASUMI_PAYMENT_SERVICE_URL.
- Use preprod/test ADA first (see “Top Up Your Wallets” in docs) before going to mainnet.
- Registry Service is optional—Sokosumi listing relies on your Masumi-registered agent and compliant API.
