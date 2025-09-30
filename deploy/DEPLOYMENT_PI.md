# Raspberry Pi Deployment — Clarification and Options

You saw this warning because only the `deploy/pi` folder was copied to the Pi:

> The docker-compose file is configured to build from context ../.. and a Dockerfile named Dockerfile at that context. From your current path (~/pi), that resolves to /home/Dockerfile, which doesn’t exist.

Why this happens
- `deploy/pi/docker-compose.yml` uses:
  ```
  build:
    context: ../..
    dockerfile: Dockerfile
  ```
- That means: two directories up from `deploy/pi` is the repo root, and the Dockerfile lives at that repo root alongside `src/`, `templates/`, `requirements.txt`, etc.
- If you copy only `deploy/pi`, Docker can’t see the app source or the root `Dockerfile`.

You have three ways to proceed

Option A — Copy the entire repository (recommended, simplest)
1) On your workstation:
   - Ensure the repo has this structure (simplified):
     ```
     .
     ├─ Dockerfile
     ├─ requirements.txt
     ├─ src/
     ├─ templates/
     └─ deploy/
        └─ pi/
           ├─ docker-compose.yml
           ├─ Caddyfile
           └─ .env.production.example
     ```
2) Copy the whole repo to your Pi, e.g.:
   - scp -r cryptoAnalyst pi@<pi-ip>:/opt/wallet-agent
   - or git clone on the Pi: `git clone <your-repo-url> /opt/wallet-agent`
3) On the Pi:
   - cd /opt/wallet-agent/deploy/pi
   - cp .env.production.example .env.production
   - Edit `.env.production` with your production values
   - Edit `Caddyfile` and set your host (e.g., agent.hulrom.no)
   - docker compose up -d

This works because `context: ../..` now correctly points at the repo root where the Dockerfile and source live.

Option B — Build from a remote Git context (no need to copy the repo)
- Docker supports remote build contexts (BuildKit). Edit `deploy/pi/docker-compose.yml`:
  ```
  services:
    wallet-agent:
      build:
        context: https://github.com/<your-username>/<your-repo>.git#<branch-or-tag>
        dockerfile: Dockerfile
      ...
  ```
- Then run:
  - cd deploy/pi
  - cp .env.production.example .env.production
  - docker compose up -d
- Replace the placeholders with your actual Git repo URL and branch/tag. This lets Docker fetch the repo source directly on the Pi.

Option C — Use a prebuilt image (no building on the Pi)
1) Build locally on your workstation:
   - docker build -t <registry>/<ns>/wallet-health-agent:latest .
   - docker push <registry>/<ns>/wallet-health-agent:latest
2) On the Pi, use the provided compose variant (see file below):
   - cd deploy/pi
   - cp .env.production.example .env.production
   - docker compose -f docker-compose.image.yml up -d

We included a compose file for Option C

File: `deploy/pi/docker-compose.image.yml` (already provided alongside your default compose)
- It uses `image:` instead of `build:` so you can pull a prebuilt image.

TLS and DNS reminders (Caddy)
- Use a real DNS name (e.g., agent.hulrom.no) that resolves to your Pi’s public IP.
- In Cloudflare, set the A record to DNS only (gray cloud) initially so Caddy can complete Let’s Encrypt HTTP-01 automatically.
- Ensure your router forwards 80/443 to the Pi’s LAN IP.

Health checks
- After `docker compose up -d`:
  - curl -s https://<your-domain>/availability
  - Visit https://<your-domain>/docs

Live payment test
- Keep `MASUMI_BYPASS_PAYMENTS=false` in production.
- POST `/start_job` with address + network, complete payment via your Masumi Payment Service, and poll `/status` until “completed”.

Need help choosing an option?
- If you want the least friction now: Option A (copy repo) is the most straightforward.
- If you don’t want to copy the repo: Option B (remote Git context) is one edit away, but requires your repo to be accessible.
- If you prefer CI publishing: Option C (prebuilt image) is best once you have a registry.
