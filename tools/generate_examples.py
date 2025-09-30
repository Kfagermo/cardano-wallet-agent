import os
import json

# Ensure project root is importable when running as a script
try:
    # Import internal helpers from the app
    from src.main import _compute_risk_and_health, _render_report  # type: ignore
except ModuleNotFoundError:
    import sys as _sys
    _CUR_DIR = os.path.dirname(os.path.abspath(__file__))
    _PROJECT_ROOT = os.path.abspath(os.path.join(_CUR_DIR, ".."))
    if _PROJECT_ROOT not in _sys.path:
        _sys.path.insert(0, _PROJECT_ROOT)
    from src.main import _compute_risk_and_health, _render_report  # type: ignore


CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CUR_DIR, ".."))
EXAMPLES_DIR = os.path.join(PROJECT_ROOT, "examples")
os.makedirs(EXAMPLES_DIR, exist_ok=True)


def make_example(name: str, address: str, network: str, snapshot: dict) -> dict:
    score, health, reasons = _compute_risk_and_health(snapshot)
    result = {
        "address": address,
        "network": network,
        **snapshot,
        "risk_score": score,
        "health": health,
        "reasons": reasons,
        "symbol": "ADA",
        "window_label": "30d",
        "indicators_summary": "EMA(12/26), MACD, RSI(14)",
    }

    # Save JSON example
    json_path = os.path.join(EXAMPLES_DIR, f"example_{name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    # Render an HTML report for demo purposes
    report_path = _render_report(f"example_{name}", result)
    return {"json": json_path, "report": report_path, "score": score, "health": health}


def main():
    examples = []

    # Safe profile
    safe_snapshot = {
        "balances": {"ada": 1543.21, "token_count": 3},
        "staking": {"delegated": True, "pool_id": "pool1xyz", "since": "2023-11-01"},
        "first_seen": "2023-01-01",
        "age_days": 400,
        "tx_velocity_30d": 2,
        "counterparty_diversity_90d": 0.75,
        "known_label": "exchange",
        "top_tokens": [
            {"asset": "TOKEN", "policy": "abcd...", "qty": "1000"},
            {"asset": "XYZ", "policy": "ef01...", "qty": "250"},
        ],
    }
    examples.append(make_example("safe", "addr1qxyzdemoaddress", "preprod", safe_snapshot))

    # Caution profile
    caution_snapshot = {
        "balances": {"ada": 322.12, "token_count": 1},
        "staking": {"delegated": False, "pool_id": None, "since": None},
        "first_seen": "2024-01-01",
        "age_days": 150,
        "tx_velocity_30d": 14,
        "counterparty_diversity_90d": 0.5,
        "known_label": None,
        "top_tokens": [
            {"asset": "MID", "policy": "12ab...", "qty": "50"},
        ],
    }
    examples.append(make_example("caution", "addr1qmidaddress", "preprod", caution_snapshot))

    # Risky profile
    risky_snapshot = {
        "balances": {"ada": 25.0, "token_count": 0},
        "staking": {"delegated": False, "pool_id": None, "since": None},
        "first_seen": "2025-09-01",
        "age_days": 10,
        "tx_velocity_30d": 120,
        "counterparty_diversity_90d": 0.1,
        "known_label": None,
        "top_tokens": [],
    }
    examples.append(make_example("risky", "addr1qriskyaddress", "preprod", risky_snapshot))

    print(json.dumps({"examples": examples}, indent=2))


if __name__ == "__main__":
    main()
