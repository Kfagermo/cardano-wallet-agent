import asyncio
import time
import uuid
import hashlib
import json
from typing import Any, Dict, Optional

import httpx


def _norm_base(url: str) -> str:
    return url.rstrip("/")


async def is_purchase_paid(base_url: str, api_key: str, payment_id: str, network: Optional[str] = None) -> Optional[bool]:
    """
    Best-effort check if a purchase is paid on the Masumi Payment Service.
    Attempts multiple read patterns to be compatible with differing deployments:
      1) GET /purchase/{identifierFromPurchaser}            (some services 404 here)
      2) GET /purchase?identifierFromPurchaser={id}         (preferred)
      3) Fallbacks: /purchase?payment_id=..., ?purchase_id=..., ?id=...

    Returns:
      - True  -> paid/confirmed (you can execute the job)
      - False -> not paid yet
      - None  -> unknown/error (treat as not-yet, with backoff)
    """
    base = _norm_base(base_url)
    # Swagger shows API key header name = "token"
    headers = {"token": api_key, "Accept": "application/json"}
    net_label = None
    if network is not None:
        net_label = "Preprod" if str(network).lower() == "preprod" else "Mainnet"
    base_params: Dict[str, Any] = {"network": net_label} if net_label else {}

    async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
        # Try path form
        try:
            r = await client.get(f"{base}/purchase/{payment_id}", params=base_params)
            if r.status_code == 200:
                data = r.json()
                if _looks_paid(data):
                    return True
                return False
        except Exception:
            pass

        # Try query forms (most compatible)
        for key in ("identifierFromPurchaser", "payment_id", "purchase_id", "id"):
            try:
                r = await client.get(f"{base}/purchase", params={**base_params, key: payment_id})
                if r.status_code == 200:
                    data = r.json()
                    if _looks_paid(data):
                        return True
                    return False
            except Exception:
                pass

    return None


def _looks_paid(data: Dict[str, Any]) -> bool:
    """
    Interpret common Payment Service response shapes.
    We consider the purchase paid/confirmed if status contains 'paid' or 'completed'.
    """
    # Direct {'status': 'paid'} or similar
    status = _pluck_case_insensitive(data, "status")
    if isinstance(status, str) and any(s in status.lower() for s in ("paid", "completed", "success")):
        return True

    # Wrapped {'data': {'status': 'paid', ...}}
    inner = data.get("data")
    if isinstance(inner, dict):
        status = _pluck_case_insensitive(inner, "status")
        if isinstance(status, str) and any(s in status.lower() for s in ("paid", "completed", "success")):
            return True

    return False


def _pluck_case_insensitive(obj: Dict[str, Any], key: str) -> Any:
    for k, v in obj.items():
        if isinstance(k, str) and k.lower() == key.lower():
            return v
    return None


def compute_input_hash(data: Dict[str, Any]) -> str:
    """
    Stable SHA-256 hex of the provided data (JSON-serialized with sorted keys).
    This can be used for the 'inputHash' field when creating a purchase.
    """
    try:
        payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except Exception:
        payload = json.dumps(str(data)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_purchase_payload(
    payment_id: str,
    seller_vkey: str,
    network: str,
    input_hash: Optional[str] = None,
    pay_by_minutes: int = 10,
    submit_after_pay_by_minutes: int = 10,
    unlock_after_submit_minutes: int = 5,
    external_unlock_after_unlock_minutes: int = 5,
    blockchain_identifier: Optional[str] = None,
    agent_identifier: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a payload that satisfies the Payment Service timing constraints:
    - payByTime must be BEFORE submitResultTime by at least 5 minutes.
    - unlockTime must be AFTER submitResultTime.
    - externalDisputeUnlockTime must be AFTER unlockTime.

    All time fields are unix epoch seconds (stringified to match Swagger examples).
    """
    now = int(time.time())
    pay_by = now + max(1, int(pay_by_minutes)) * 60
    # Ensure submitResultTime is at least 5 minutes after payByTime
    submit_gap = max(5, int(submit_after_pay_by_minutes))
    submit_result = pay_by + submit_gap * 60
    unlock_time = submit_result + max(1, int(unlock_after_submit_minutes)) * 60
    external_unlock = unlock_time + max(1, int(external_unlock_after_unlock_minutes)) * 60

    # Map network to service-expected labels if necessary
    net_label = "Preprod" if str(network).lower() == "preprod" else "Mainnet"

    return {
        "blockchainIdentifier": blockchain_identifier or str(uuid.uuid4()),
        "agentIdentifier": agent_identifier or str(uuid.uuid4()),
        "submitResultTime": str(submit_result),
        "externalDisputeUnlockTime": str(external_unlock),
        "identifierFromPurchaser": payment_id,
        "payByTime": str(pay_by),
        "unlockTime": str(unlock_time),
        "sellerVkey": seller_vkey,
        "network": net_label,
        "inputHash": input_hash or compute_input_hash({"payment_id": payment_id}),
    }


async def create_purchase(
    base_url: str,
    api_key: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create a purchase via POST /purchase.

    Headers:
      - token: <api_key>   (per Swagger)
      - Content-Type: application/json
    """
    base = _norm_base(base_url)
    headers = {"token": api_key, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
        r = await client.post(f"{base}/purchase", json=payload)
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text}
        return {"status_code": r.status_code, "data": data}
