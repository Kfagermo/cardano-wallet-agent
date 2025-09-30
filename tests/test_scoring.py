import os
import importlib

# Ensure any environment-sensitive code is stable during import
os.environ.setdefault("NETWORK", "preprod")
os.environ.setdefault("MASUMI_BYPASS_PAYMENTS", "true")

from src import main  # noqa: E402

# Reload to ensure current defs are in scope if server hot-reloaded earlier
importlib.reload(main)


def test_scoring_safe_profile():
    # Expected: strong negatives -> low risk score, "safe"
    sample = {
        "age_days": 400,                      # -10
        "staking": {"delegated": True},       # -8
        "tx_velocity_30d": 2,                 # -4
        "counterparty_diversity_90d": 0.75,   # -6
        "known_label": "exchange",            # -5
    }
    score, health, reasons = main._compute_risk_and_health(sample)
    assert 0 <= score <= 100
    assert score <= 33
    assert health == "safe"
    # Check presence of some expected reasons
    assert any("older than 1 year" in r for r in reasons)
    assert any("delegated/staked ADA" in r for r in reasons)
    assert any("diverse counterparties" in r for r in reasons)
    assert any("known label" in r for r in reasons)


def test_scoring_risky_profile():
    # Expected: positives -> higher risk score, "risky"
    sample = {
        "age_days": 10,                       # +10
        "staking": {"delegated": False},      #  0
        "tx_velocity_30d": 120,               # +10
        "counterparty_diversity_90d": 0.1,    # +6
        "known_label": None,                  #  0
    }
    score, health, reasons = main._compute_risk_and_health(sample)
    assert 0 <= score <= 100
    assert score > 66
    assert health == "risky"
    # New address reason expected
    assert any("new address" in r for r in reasons)


def test_scoring_caution_profile():
    # Balanced -> around mid score, "caution"
    sample = {
        "age_days": 300,                      #  0
        "staking": {"delegated": False},      #  0
        "tx_velocity_30d": 14,                #  0
        "counterparty_diversity_90d": 0.5,    #  0
        "known_label": None,                  #  0
    }
    score, health, reasons = main._compute_risk_and_health(sample)
    assert 0 <= score <= 100
    assert 33 < score <= 66
    assert health == "caution"
