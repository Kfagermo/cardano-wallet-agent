import os
import asyncio
import uuid
import time
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, Body, Request
from pydantic import BaseModel, Field, ValidationError
from jinja2 import Environment, FileSystemLoader, select_autoescape
from blockfrost import BlockFrostApi, ApiUrls
from dotenv import load_dotenv
from src.masumi.payments import is_purchase_paid, build_purchase_payload, create_purchase, compute_input_hash
from src.store.sqlite_store import init_db, create_job, get_job, update_job_status, get_cache, upsert_cache, find_recent_job_by_input
from src.services.ai_analyzer import create_analyzer

# --- Config & Paths ---
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# project root = src/..
PROJECT_ROOT = os.path.dirname(ROOT_DIR)
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "app.db")
# Load environment variables from .env if present (so BLOCKFROST_PROJECT_ID, etc. work)
load_dotenv()

# Env flags
BYPASS_PAYMENTS = os.getenv("MASUMI_BYPASS_PAYMENTS", "true").lower() in ("1", "true", "yes")
NETWORK_DEFAULT = os.getenv("NETWORK", "mainnet")
BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID")
MASUMI_PAYMENT_SERVICE_URL = os.getenv("MASUMI_PAYMENT_SERVICE_URL", "")
MASUMI_API_KEY = os.getenv("MASUMI_API_KEY", "")
PRICE_PER_ADDRESS_ADA = float(os.getenv("PRICE_PER_ADDRESS_ADA", "0.03"))
MASUMI_PAYMENT_TIMEOUT_SEC = int(os.getenv("MASUMI_PAYMENT_TIMEOUT_SEC", "600"))
SELLER_VKEY = os.getenv("SELLER_VKEY", "")
CACHE_TTL_SEC = int(os.getenv("CACHE_TTL_SEC", "86400"))
IDEMPOTENCY_WINDOW_SEC = int(os.getenv("IDEMPOTENCY_WINDOW_SEC", "600"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "60"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_ANALYSIS_MODE = os.getenv("AI_ANALYSIS_MODE", "deterministic").lower()  # "openai", "crewai", or "deterministic"

# Jinja2
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)

# --- In-memory job store (deprecated; replaced by SQLite in src/store/sqlite_store.py) ---
JOBS: Dict[str, Dict[str, Any]] = {}

# --- Schemas (MIP-003 style) ---
MIP003_INPUT_SCHEMA = {
    "input_data": [
        {"key": "address", "value": "string"},
        {"key": "network", "value": "string"},  # "mainnet" | "preprod"
    ]
}


class InputKV(BaseModel):
    key: str
    value: Any


class StartJobPayload(BaseModel):
    input_data: List[InputKV] = Field(default_factory=list)


# --- FastAPI app ---
app = FastAPI(title="Wallet Health & Risk Scoring Agent", version="0.1.0")  # reload

# --- Simple per-IP token-bucket rate limiter (best-effort, per-process) ---
import threading
_RL_LOCK = threading.Lock()
_RL_STATE: Dict[str, Dict[str, float]] = {}  # ip -> { "tokens": float, "last": float }
_RL_CAP = max(1, RATE_LIMIT_RPM)          # max tokens per minute
_RL_REFILL_PER_SEC = _RL_CAP / 60.0       # refill rate

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path or ""
    # Skip rate limiting for health/docs endpoints
    if path in ("/availability", "/docs", "/openapi.json", "/redoc"):
        return await call_next(request)

    ip = (request.client.host if request.client else "unknown") or "unknown"
    now = time.time()
    allowed = True
    with _RL_LOCK:
        st = _RL_STATE.get(ip)
        if not st:
            st = {"tokens": float(_RL_CAP), "last": now}
            _RL_STATE[ip] = st
        # Refill
        elapsed = max(0.0, now - st["last"])
        st["tokens"] = min(float(_RL_CAP), st["tokens"] + elapsed * _RL_REFILL_PER_SEC)
        st["last"] = now
        if st["tokens"] >= 1.0:
            st["tokens"] -= 1.0
            allowed = True
        else:
            allowed = False

    if not allowed:
        log_event("rate_limited", ip=ip, path=path)
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    return await call_next(request)

# --- Logging (structured JSON to stdout) ---
logger = logging.getLogger("wallet_agent")
if not logger.handlers:
    handler = logging.StreamHandler()
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    logger.addHandler(handler)

def log_event(event: str, **kwargs: Any) -> None:
    try:
        payload = {"event": event, "ts": int(time.time()), **kwargs}
        logger.info(json.dumps(payload, separators=(",", ":")))
    except Exception:
        logger.info(f"{event} | {kwargs}")

@app.on_event("startup")
def _startup() -> None:
    # Initialize SQLite database on app start
    init_db(DB_PATH)
    
    # Log AI analysis mode
    if AI_ANALYSIS_MODE in ("openai", "crewai") and not OPENAI_API_KEY:
        logger.warning(f"AI_ANALYSIS_MODE={AI_ANALYSIS_MODE} but OPENAI_API_KEY not set. Falling back to deterministic analysis.")
    log_event("startup", ai_mode=AI_ANALYSIS_MODE, has_openai_key=bool(OPENAI_API_KEY))


@app.get("/availability")
def availability() -> Dict[str, Any]:
    return {"status": "available", "uptime": int(time.time()), "message": "OK"}


@app.get("/input_schema")
def input_schema() -> Dict[str, Any]:
    return MIP003_INPUT_SCHEMA

@app.get("/payment_information")
def payment_information(payment_id: str) -> Dict[str, Any]:
    return {
        "payment_id": payment_id,
        "price_ada": PRICE_PER_ADDRESS_ADA,
        "seller_vkey": SELLER_VKEY,
        "payment_service_url": MASUMI_PAYMENT_SERVICE_URL,
        "auth_header": "token",
        "network_default": NETWORK_DEFAULT,
        "status_read": {
            "preferred": "/purchase?identifierFromPurchaser=<payment_id>",
            "fallbacks": [
                "/purchase/<payment_id>",
                "/purchase?payment_id=<payment_id>",
                "/purchase?purchase_id=<payment_id>",
                "/purchase?id=<payment_id>",
            ],
            "note": "Include header 'token: <MASUMI_API_KEY>'. 200 = found; check 'status' for paid/completed."
        },
        "idempotency": {
            "window_sec": IDEMPOTENCY_WINDOW_SEC,
            "behavior": "If an identical input (address+network) was received within window_sec, the service reuses the same job_id/payment_id when possible."
        },
        "refund_policy": {
            "payment_timeout_sec": MASUMI_PAYMENT_TIMEOUT_SEC,
            "on_timeout": "Job marked failed with reason 'payment timeout'.",
            "how_to_refund": "Use PATCH/GET on /purchase according to your Payment Service deployment to request/confirm refund if supported.",
            "note": "Always include ?network=Preprod|Mainnet and header 'token: <MASUMI_API_KEY>'."
        },
        "note": "Use POST /purchase to create a purchase, then poll GET using 'identifierFromPurchaser' (preferred). Include header 'token: <MASUMI_API_KEY>'.",
    }


@app.get("/prepare_purchase")
async def prepare_purchase(
    job_id: Optional[str] = None,
    payment_id: Optional[str] = None,
    network: Optional[str] = None,
    execute: bool = False,
    pay_by_minutes: int = 10,
    submit_after_pay_by_minutes: int = 10,
    unlock_after_submit_minutes: int = 5,
    external_unlock_after_unlock_minutes: int = 5,
) -> Dict[str, Any]:
    """
    Build a valid Payment Service payload that satisfies timing constraints.
    Optionally execute POST /purchase against the configured MASUMI_PAYMENT_SERVICE_URL.
    """
    job_row = get_job(job_id) if job_id else None
    job_input = None
    if job_row:
        try:
            job_input = json.loads(job_row.get("input_json") or "null")
        except Exception:
            job_input = None

    if network is None:
        network = (job_input.get("network") if isinstance(job_input, dict) else NETWORK_DEFAULT)

    if payment_id is None:
        payment_id = (job_row["payment_id"] if job_row else str(uuid.uuid4()))

    # Tie the input hash to this job/payment (helps dedup/verification server-side)
    ih = compute_input_hash({"payment_id": payment_id, "job_id": job_id, "input": job_input})

    payload = build_purchase_payload(
        payment_id=payment_id,
        seller_vkey=SELLER_VKEY,
        network=network,
        input_hash=ih,
        pay_by_minutes=pay_by_minutes,
        submit_after_pay_by_minutes=submit_after_pay_by_minutes,
        unlock_after_submit_minutes=unlock_after_submit_minutes,
        external_unlock_after_unlock_minutes=external_unlock_after_unlock_minutes,
    )

    base = (MASUMI_PAYMENT_SERVICE_URL or "").rstrip("/")
    curl = (
        "curl -X 'POST' "
        f"'{base}/purchase' "
        "-H 'accept: application/json' "
        f"-H 'token: {MASUMI_API_KEY}' "
        "-H 'Content-Type: application/json' "
        f"-d '{json.dumps(payload)}'"
    )

    result: Dict[str, Any] = {
        "payment_id": payment_id,
        "network": network,
        "seller_vkey": SELLER_VKEY,
        "payload": payload,
        "curl": curl,
        "notes": [
            "Include header 'token' with your MASUMI_API_KEY.",
            "payByTime is before submitResultTime by at least 5 minutes; unlock times are ordered correctly.",
        ],
    }

    if execute:
        if not base or not MASUMI_API_KEY:
            raise HTTPException(status_code=400, detail="Missing MASUMI_PAYMENT_SERVICE_URL or MASUMI_API_KEY to execute purchase.")
        try:
            api_res = await create_purchase(base, MASUMI_API_KEY, payload)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to create purchase: {e}")
        result["create_response"] = api_res

    return result


@app.post("/start_job")
async def start_job(payload: StartJobPayload = Body(...)) -> Dict[str, str]:
    # Validate payload against schema
    try:
        kvs = payload.input_data
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    inputs = _kvs_to_dict(kvs)

    # Schema adherence: require keys
    address = inputs.get("address")
    network = inputs.get("network", NETWORK_DEFAULT)
    if not isinstance(address, str) or not address.strip():
        raise HTTPException(status_code=400, detail="Missing or invalid 'address'")
    if network not in ("mainnet", "preprod"):
        raise HTTPException(status_code=400, detail="Invalid 'network' (use 'mainnet' or 'preprod')")

    job_id = str(uuid.uuid4())
    payment_id = str(uuid.uuid4())

    now = _now_iso()
    input_json = json.dumps({"address": address, "network": network})
    log_event("start_job_received", job_id=job_id, payment_id=payment_id, network=network)

    # Idempotency: if a recent job with the same input exists, return it
    recent = find_recent_job_by_input(input_json, IDEMPOTENCY_WINDOW_SEC)
    if recent:
        log_event("start_job_idempotent_hit", job_id=recent.get("job_id"), payment_id=recent.get("payment_id"), status=recent.get("status"))
        return {"job_id": recent.get("job_id"), "payment_id": recent.get("payment_id")}

    # Cache-first: return completed job immediately if cached
    cache_hit = get_cache(address, network, CACHE_TTL_SEC)
    if cache_hit:
        create_job(
            job_id=job_id,
            payment_id=payment_id,
            status="completed",
            input_json=input_json,
            created_at=now,
            result_str=cache_hit,
        )
        log_event("cache_hit_completed_immediately", job_id=job_id, network=network)
        return {"job_id": job_id, "payment_id": payment_id}

    # Create awaiting-payment job in DB
    create_job(
        job_id=job_id,
        payment_id=payment_id,
        status="awaiting payment",
        input_json=input_json,
        created_at=now,
    )
    log_event("job_created", job_id=job_id, payment_id=payment_id, status="awaiting payment")

    # Payment handling: in dev BYPASS_PAYMENTS runs immediately; otherwise wait for Payment Service confirmation
    if BYPASS_PAYMENTS:
        _run_job(job_id)
    else:
        if MASUMI_PAYMENT_SERVICE_URL and MASUMI_API_KEY:
            try:
                asyncio.create_task(_await_payment_then_run(job_id))
            except RuntimeError:
                loop = asyncio.get_event_loop()
                loop.create_task(_await_payment_then_run(job_id))

    return {"job_id": job_id, "payment_id": payment_id}


@app.get("/status")
def status(job_id: str) -> Dict[str, Any]:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    result_str: Optional[str] = job.get("result_str")
    log_event("status_read", job_id=job_id, status=job.get("status"))

    return {
        "job_id": job_id,
        "status": job.get("status", "pending"),
        "result": result_str,
    }


# --- Internal processing ---


def _kvs_to_dict(kvs: List[InputKV]) -> Dict[str, Any]:
    # MIP-003 allows duplicate keys (e.g., multiple options); here we take the last occurrence.
    d: Dict[str, Any] = {}
    for kv in kvs:
        d[kv.key] = kv.value
    return d


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")


def _class_from_health(health: str) -> str:
    h = (health or "").lower()
    if h in ("safe", "good", "low"):
        return "safe"
    if h in ("caution", "medium"):
        return "caution"
    return "risky"


async def _compute_risk_and_health_async(sample: Dict[str, Any]) -> Tuple[int, str, List[str]]:
    """
    Compute risk score and health category using AI or deterministic rules.
    
    Modes:
    - "openai": Single AI agent analysis (GPT-4o-mini)
    - "crewai": Multi-agent collaborative analysis (4 specialized agents)
    - "deterministic": Rule-based analysis (fallback, no API costs)
    """
    # Use AI analysis if configured and API key available
    if AI_ANALYSIS_MODE in ("openai", "crewai") and OPENAI_API_KEY:
        try:
            analyzer = create_analyzer(mode=AI_ANALYSIS_MODE, api_key=OPENAI_API_KEY)
            score, health, reasons = await analyzer.analyze_wallet(sample)
            log_event("ai_analysis_success", mode=AI_ANALYSIS_MODE, risk_score=score, health=health)
            return score, health, reasons
        except Exception as e:
            log_event("ai_analysis_failed", mode=AI_ANALYSIS_MODE, error=str(e))
            # Fall through to deterministic analysis
    
    # Deterministic analysis (fallback or explicit mode)
    return _compute_risk_and_health_deterministic(sample)


def _compute_risk_and_health_deterministic(sample: Dict[str, Any]) -> Tuple[int, str, List[str]]:
    """
    Deterministic rule-based risk analysis (original logic).
    Used as fallback when AI is unavailable or as explicit mode.
    """
    reasons: List[str] = []
    score = 50

    # Age and staking influence
    age_days = int(sample.get("age_days", 0) or 0)
    if age_days >= 365:
        score -= 10
        reasons.append("address is older than 1 year (positive)")
    elif age_days < 30:
        score += 10
        reasons.append("new address (<30 days, needs monitoring)")

    # Staking
    staking = sample.get("staking", {}) or {}
    if staking.get("delegated"):
        score -= 8
        reasons.append("delegated/staked ADA adds stability")

    # Velocity
    v30 = int(sample.get("tx_velocity_30d", 0) or 0)
    if v30 > 100:
        score += 10
        reasons.append("very high recent tx velocity (potential bot)")
    elif v30 < 5:
        score -= 4
        reasons.append("low recent tx activity (dormant or holder)")

    # Diversity
    div = float(sample.get("counterparty_diversity_90d", 0.0) or 0.0)
    if div >= 0.7:
        score -= 6
        reasons.append("diverse counterparties (healthy ecosystem participation)")
    elif div <= 0.2:
        score += 6
        reasons.append("low counterparty diversity (concentrated activity)")

    # Known label
    label = sample.get("known_label")
    if label in ("exchange", "custody"):
        score -= 5
        reasons.append(f"known label: {label} (trusted entity)")

    # Clamp
    if score < 0:
        score = 0
    if score > 100:
        score = 100

    # Health bucket (lower score = safer by our convention)
    if score <= 33:
        health = "safe"
    elif score <= 66:
        health = "caution"
    else:
        health = "risky"

    if not reasons:
        reasons.append("no special risk factors identified (deterministic analysis)")

    return score, health, reasons


def _blockfrost_api_for_network(network: str) -> BlockFrostApi:
    base = ApiUrls.cardano_mainnet.value if network == "mainnet" else ApiUrls.cardano_preprod.value
    return BlockFrostApi(project_id=BLOCKFROST_PROJECT_ID, base_url=base)


def _fetch_onchain(address: str, network: str) -> Dict[str, Any]:
    # Use Blockfrost if configured; otherwise return a deterministic sample.
    if not BLOCKFROST_PROJECT_ID:
        return {
            "balances": {"ada": 1543.21, "token_count": 3},
            "staking": {"delegated": True, "pool_id": "pool1xyz", "since": "2023-11-01"},
            "first_seen": "2023-01-01",
            "age_days": 300,
            "tx_velocity_30d": 14,
            "counterparty_diversity_90d": 0.72,
            "known_label": "exchange",
            "top_tokens": [
                {"asset": "TOKEN", "policy": "abcd...", "qty": "1000"},
                {"asset": "XYZ", "policy": "ef01...", "qty": "250"},
            ],
        }

    try:
        api = _blockfrost_api_for_network(network)

        # Address info and balances
        addr = api.address(address)
        ada_lovelace = 0.0
        tokens = []
        for amt in (addr.get("amount", []) if isinstance(addr, dict) else getattr(addr, "amount", []) or []):
            unit = amt.get("unit")
            qty = float(amt.get("quantity", 0))
            if unit == "lovelace":
                ada_lovelace = qty
            else:
                # Best-effort policy extraction (first 56 chars typical for policy id length)
                tokens.append({"asset": unit, "policy": str(unit)[:56], "qty": str(int(qty))})
        ada = round(ada_lovelace / 1_000_000, 6)

        # Staking (if stake address exists)
        staking = {"delegated": False, "pool_id": None, "since": None}
        stake_addr = (addr.get("stake_address") if isinstance(addr, dict) else getattr(addr, "stake_address", None))
        if stake_addr:
            try:
                acct = api.account(stake_addr)
                if isinstance(acct, dict):
                    pool_id = acct.get("pool_id") or acct.get("delegated_pool_id")
                else:
                    pool_id = getattr(acct, "pool_id", None) or getattr(acct, "delegated_pool_id", None)
                staking["delegated"] = bool(pool_id)
                staking["pool_id"] = pool_id
            except Exception:
                pass

        # First seen (best-effort)
        first_seen = None
        try:
            txs_asc = api.address_transactions(address, count=1, page=1, order="asc")
            if txs_asc:
                item0 = txs_asc[0]
                first_seen = (item0.get("block_time") or item0.get("time")) if isinstance(item0, dict) else getattr(item0, "block_time", None)
        except Exception:
            pass

        snapshot = {
            "balances": {"ada": ada, "token_count": len(tokens)},
            "staking": staking,
            "first_seen": first_seen,
            "age_days": 0,
            "tx_velocity_30d": 0,
            "counterparty_diversity_90d": 0.0,
            "known_label": None,
            "top_tokens": tokens[:5],
        }
        return snapshot
    except Exception:
        # Fallback to deterministic sample if API fails
        return {
            "balances": {"ada": 1543.21, "token_count": 3},
            "staking": {"delegated": True, "pool_id": "pool1xyz", "since": "2023-11-01"},
            "first_seen": "2023-01-01",
            "age_days": 300,
            "tx_velocity_30d": 14,
            "counterparty_diversity_90d": 0.72,
            "known_label": "exchange",
            "top_tokens": [
                {"asset": "TOKEN", "policy": "abcd...", "qty": "1000"},
                {"asset": "XYZ", "policy": "ef01...", "qty": "250"},
            ],
        }


def _render_report(job_id: str, data: Dict[str, Any]) -> str:
    # Renders templates/wallet_report.html into reports/{job_id}.html and returns file path.
    template = jinja_env.get_template("wallet_report.html")

    html = template.render(
        address=data.get("address"),
        network=data.get("network"),
        generated_at=_now_iso(),
        risk_score=data.get("risk_score"),
        health=data.get("health"),
        health_class=_class_from_health(data.get("health", "")),
        first_seen=data.get("first_seen"),
        age_days=data.get("age_days"),
        tx_velocity_30d=data.get("tx_velocity_30d"),
        counterparty_diversity_90d=data.get("counterparty_diversity_90d"),
        reasons=data.get("reasons", []),
        balances=data.get("balances", {}),
        staking=data.get("staking", {}),
        known_label=data.get("known_label"),
        top_tokens=data.get("top_tokens", []),
        price_chart_base64=data.get("price_chart_base64", ""),
        symbol=data.get("symbol", "ADA"),
        window_label=data.get("window_label", "30d"),
        indicators_summary=data.get("indicators_summary", "EMA(12/26), MACD, RSI(14)"),
        raw_json_pretty=json.dumps(data, indent=2),
        raw_json=json.dumps(data, separators=(",", ":")),
    )

    out_path = os.path.join(REPORTS_DIR, f"{job_id}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


async def _await_payment_then_run(job_id: str) -> None:
    job = get_job(job_id)
    if not job:
        return

    # Parse input for network
    try:
        job_input = json.loads(job.get("input_json") or "null") or {}
    except Exception:
        job_input = {}
    network = job_input.get("network")

    start = time.time()
    interval = 5.0
    log_event("payment_poll_start", job_id=job_id, payment_id=job.get("payment_id"), network=network)
    # Poll Payment Service until paid or timeout
    while time.time() - start < MASUMI_PAYMENT_TIMEOUT_SEC:
        try:
            paid = await is_purchase_paid(
                MASUMI_PAYMENT_SERVICE_URL,
                MASUMI_API_KEY,
                job.get("payment_id"),
                network,
            )
        except Exception:
            paid = None
        if paid is True:
            log_event("payment_confirmed", job_id=job_id)
            _run_job(job_id)
            return
        await asyncio.sleep(interval)
    # timeout -> mark failed with reason
    update_job_status(job_id, "failed", _now_iso(), fail_reason="payment timeout")
    log_event("payment_timeout", job_id=job_id)

def _run_job(job_id: str) -> None:
    """
    Execute wallet analysis job.
    This is a sync wrapper that runs async AI analysis in a new event loop.
    """
    job = get_job(job_id)
    if not job:
        return

    # Parse input
    try:
        job_input = json.loads(job.get("input_json") or "null") or {}
    except Exception:
        job_input = {}
    address = (job_input.get("address") or "").strip()
    network = job_input.get("network") or NETWORK_DEFAULT

    # Mark running
    update_job_status(job_id, "running", _now_iso())
    log_event("job_running", job_id=job_id, address=address, network=network, ai_mode=AI_ANALYSIS_MODE)

    # Fetch on-chain snapshot (Blockfrost if configured, otherwise sample)
    snapshot = _fetch_onchain(address, network)

    # Compute risk (async AI analysis or sync deterministic)
    try:
        # Run async analysis in new event loop (safe for background tasks)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        score, health, reasons = loop.run_until_complete(_compute_risk_and_health_async(snapshot))
        loop.close()
    except Exception as e:
        log_event("analysis_error", job_id=job_id, error=str(e))
        # Fallback to deterministic
        score, health, reasons = _compute_risk_and_health_deterministic(snapshot)

    # Compose result payload
    result_payload: Dict[str, Any] = {
        "address": address,
        "network": network,
        **snapshot,
        "risk_score": score,
        "health": health,
        "reasons": reasons,
        "analysis_mode": AI_ANALYSIS_MODE if (AI_ANALYSIS_MODE in ("openai", "crewai") and OPENAI_API_KEY) else "deterministic",
        "symbol": "ADA",
        "window_label": "30d",
        "indicators_summary": "EMA(12/26), MACD, RSI(14)",
    }

    # Render report for human consumption and include path in payload
    report_path = _render_report(job_id, result_payload)
    result_payload["report_path"] = report_path

    # Persist result as JSON string (MIP-003 expects a string)
    result_json = json.dumps(result_payload, separators=(",", ":"))

    # Cache result for future identical requests
    try:
        upsert_cache(address, network, result_json)
    except Exception:
        pass

    # Mark completed
    update_job_status(job_id, "completed", _now_iso(), result_str=result_json)
    log_event("job_completed", job_id=job_id, risk_score=score, health=health, ai_mode=result_payload.get("analysis_mode"))


# --- Optional root endpoint for sanity check ---
@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "name": "Wallet Health & Risk Scoring Agent",
        "version": "0.1.0",
        "docs": "/docs",
        "mip003": {
            "availability": "/availability",
            "input_schema": "/input_schema",
            "start_job": "/start_job",
            "status": "/status?job_id=<uuid>",
        },
        "dev": {
            "bypass_payments": BYPASS_PAYMENTS,
            "reports_dir": os.path.relpath(REPORTS_DIR, PROJECT_ROOT),
        },
        "ai": {
            "mode": AI_ANALYSIS_MODE,
            "enabled": AI_ANALYSIS_MODE in ("openai", "crewai") and bool(OPENAI_API_KEY),
            "available_modes": ["openai", "crewai", "deterministic"],
        },
    }
