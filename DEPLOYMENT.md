# Deployment Guide — Wallet Health & Risk Scoring Agent (Masumi MIP-003)

This guide covers two production-ready options:
- Option A: Kodosumi or any Docker-ready host
- Option B: Ubuntu VPS (systemd + Nginx + Uvicorn)

The service exposes FastAPI endpoints compatible with Masumi MIP-003:
/availability, /input_schema, /start_job, /status

IMPORTANT
- Keep MASUMI_BYPASS_PAYMENTS=false in production.
- Rotate secrets and never commit .env with secrets to your repo.
- Ensure HTTPS and a stable public URL before listing on Sokosumi.

Environment variables (required/optional)
- MASUMI_BYPASS_PAYMENTS=false        # production
- NETWORK=mainnet | preprod
- BLOCKFROST_PROJECT_ID=...           # optional for MVP; enables real on-chain reads
- MASUMI_PAYMENT_SERVICE_URL=...      # must include /api/v1
- MASUMI_API_KEY=...                  # API key header: token
- SELLER_VKEY=...                     # your seller verification key
- PRICE_PER_ADDRESS_ADA=0.03          # reference price only; enforce in Payment Service/listing
- CACHE_TTL_SEC=86400                  # cache lifetime in seconds (24h default)

Option A — Kodosumi / Docker

A1) Build a container image

Create a Dockerfile at repo root (see below). Then:

docker build -t wallet-health-agent:latest .

A2) Run locally for validation

docker run --rm -p 8000:8000 ^
  -e MASUMI_BYPASS_PAYMENTS=false ^
  -e NETWORK=preprod ^
  -e BLOCKFROST_PROJECT_ID=... ^
  -e MASUMI_PAYMENT_SERVICE_URL=https://.../api/v1 ^
  -e MASUMI_API_KEY=... ^
  -e SELLER_VKEY=... ^
  wallet-health-agent:latest

Visit http://localhost:8000/availability and /docs.

A3) Push to your registry (if needed)

docker tag wallet-health-agent:latest <registry>/<namespace>/wallet-health-agent:latest
docker push <registry>/<namespace>/wallet-health-agent:latest

A4) Deploy on Kodosumi (or any orchestrator)
- Create a service with the image and environment variables above
- Expose port 8000 behind HTTPS
- Add uptime checks against /availability
- Persist data/ (SQLite DB) if you need to retain jobs across restarts (mount a volume)

Recommended Dockerfile (Python 3.11 slim):

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for building some wheels; remove if not needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy and install deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY src ./src
COPY templates ./templates
COPY README.md SURVIVAL_PLAN.md ./

# Runtime dirs
RUN mkdir -p reports data

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

Recommended .dockerignore:

.git
__pycache__/
*.pyc
*.pyo
*.pyd
*.log
*.sqlite3
data/
reports/
.env
.venv/
.vscode/
dist/
build/

Option B — Ubuntu VPS (systemd + Nginx reverse proxy)

B1) Server prerequisites
- Ubuntu 22.04 or 24.04 LTS
- Python 3.11+ (sudo apt-get update && sudo apt-get install -y python3.11 python3.11-venv)
- Nginx + Certbot (sudo apt-get install -y nginx && sudo snap install --classic certbot)

B2) App installation

# Create app user and directory
sudo adduser --system --group appuser
sudo mkdir -p /opt/wallet-agent
sudo chown -R appuser:appuser /opt/wallet-agent

# Upload code to /opt/wallet-agent (git clone or rsync)
# Example (git):
sudo -u appuser git clone <your-repo-url> /opt/wallet-agent
cd /opt/wallet-agent

# Create venv and install deps
sudo -u appuser python3.11 -m venv .venv
sudo -u appuser bash -lc ". .venv/bin/activate && pip install -U pip && pip install -r requirements.txt"

# Create environment file at /etc/wallet-agent.env (root-owned)
sudo tee /etc/wallet-agent.env >/dev/null << 'EOF'
MASUMI_BYPASS_PAYMENTS=false
NETWORK=preprod
BLOCKFROST_PROJECT_ID=
MASUMI_PAYMENT_SERVICE_URL=
MASUMI_API_KEY=
SELLER_VKEY=
PRICE_PER_ADDRESS_ADA=0.05
CACHE_TTL_SEC=86400
EOF
sudo chmod 600 /etc/wallet-agent.env

B3) systemd unit file

Create /etc/systemd/system/wallet-agent.service:

[Unit]
Description=Wallet Health & Risk Scoring Agent (Uvicorn)
After=network.target

[Service]
User=appuser
Group=appuser
WorkingDirectory=/opt/wallet-agent
EnvironmentFile=/etc/wallet-agent.env
ExecStart=/opt/wallet-agent/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=5
# Optional resource limits
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target

Then:

sudo systemctl daemon-reload
sudo systemctl enable wallet-agent
sudo systemctl start wallet-agent
sudo systemctl status wallet-agent

B4) Nginx reverse proxy + TLS

Create /etc/nginx/sites-available/wallet-agent.conf:

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 75s;
    }

    location /availability {
        proxy_pass http://127.0.0.1:8000/availability;
    }
}

sudo ln -s /etc/nginx/sites-available/wallet-agent.conf /etc/nginx/sites-enabled/wallet-agent.conf
sudo nginx -t && sudo systemctl reload nginx

Issue TLS with Certbot:

sudo certbot --nginx -d your-domain.com
# Follow prompts to obtain and install certificate

B5) Health checks and monitoring
- Uptime: Nginx + systemd; external pinger against https://your-domain.com/availability
- Logs: Add structured JSON logging to the app (planned for next commit); setup logrotate if needed
- Backups: Periodic copy of /opt/wallet-agent/data/app.db if you need job history (cache can be rebuilt)

Scaling and performance
- Start with 1 vCPU, 1 GB RAM, 10 GB disk; ~ $5–$10/mo
- Set workers=2 if CPU allows; increase to 2 vCPU/2 GB if sustained cold-path RPS grows
- Use CACHE_TTL_SEC to maximize cache hits for repeated addresses (sub-500ms responses)

Security and hygiene
- Keep MASUMI_BYPASS_PAYMENTS=false in production
- Rotate MASUMI_API_KEY and SELLER_VKEY prior to launch
- Restrict inbound ports to 80/443 and SSH; use firewall (ufw)
- Do not store secrets in the repo. Use /etc/wallet-agent.env or a secret manager.

Post-deploy checklist (for listing)
- Run a real test purchase end-to-end (awaiting → running → completed)
- Idempotency guard documented and implemented (hash of payment_id + input)
- Refund/timeout policy documented (/payment_information + README)
- Produce 3 example outputs + screenshots
- Submit Sokosumi listing with schema, price (e.g., 0.05 ADA), and SLOs
