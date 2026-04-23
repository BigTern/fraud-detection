from risk_rules import label_risk, score_transaction


def _tx(**kwargs) -> dict:
    base = {
        "device_risk_score": 5,
        "is_international": 0,
        "amount_usd": 50,
        "velocity_24h": 1,
        "failed_logins_24h": 0,
        "prior_chargebacks": 0,
        "merchant_category": "grocery",
    }
    return {**base, **kwargs}


# --- label_risk ---

def test_label_risk_thresholds():
    assert label_risk(10) == "low"
    assert label_risk(35) == "medium"
    assert label_risk(75) == "high"


def test_label_risk_boundaries():
    assert label_risk(29) == "low"
    assert label_risk(30) == "medium"
    assert label_risk(59) == "medium"
    assert label_risk(60) == "high"


# --- score_transaction: each signal adds risk ---

def test_large_amount_adds_risk():
    assert score_transaction(_tx(amount_usd=1200)) == 25   # +25
    assert score_transaction(_tx(amount_usd=600)) == 10    # +10
    assert score_transaction(_tx(amount_usd=499)) == 0     # no contribution


def test_high_device_risk_adds_risk():
    assert score_transaction(_tx(device_risk_score=75)) == 25   # +25
    assert score_transaction(_tx(device_risk_score=45)) == 10   # +10
    assert score_transaction(_tx(device_risk_score=39)) == 0    # no contribution


def test_international_adds_risk():
    assert score_transaction(_tx(is_international=1)) == 15
    assert score_transaction(_tx(is_international=0)) == 0


def test_high_velocity_adds_risk():
    assert score_transaction(_tx(velocity_24h=6)) == 20    # +20
    assert score_transaction(_tx(velocity_24h=3)) == 5     # +5
    assert score_transaction(_tx(velocity_24h=2)) == 0     # no contribution


def test_failed_logins_add_risk():
    assert score_transaction(_tx(failed_logins_24h=5)) == 20   # +20
    assert score_transaction(_tx(failed_logins_24h=2)) == 10   # +10
    assert score_transaction(_tx(failed_logins_24h=1)) == 0    # no contribution


def test_prior_chargebacks_add_risk():
    assert score_transaction(_tx(prior_chargebacks=2)) == 20   # +20
    assert score_transaction(_tx(prior_chargebacks=1)) == 5    # +5
    assert score_transaction(_tx(prior_chargebacks=0)) == 0    # no contribution


def test_high_risk_merchant_adds_risk():
    assert score_transaction(_tx(merchant_category="gift_cards")) == 20
    assert score_transaction(_tx(merchant_category="crypto")) == 20
    assert score_transaction(_tx(merchant_category="gaming")) == 10
    assert score_transaction(_tx(merchant_category="grocery")) == 0
    assert score_transaction(_tx(merchant_category="travel")) == 0


# --- score caps ---

def test_score_capped_at_100():
    worst_case = _tx(device_risk_score=90, is_international=1, amount_usd=5000,
                     velocity_24h=10, failed_logins_24h=8, prior_chargebacks=5,
                     merchant_category="crypto")
    assert score_transaction(worst_case) == 100


def test_score_minimum_zero():
    assert score_transaction(_tx()) == 0


# --- real transaction profiles pinned against known outcomes ---

def test_confirmed_fraud_profiles_score_high():
    """All eight transactions that resulted in chargebacks should land in the high tier."""
    fraud_profiles = [
        # tx 50003: gift_cards, PH, device 81, $1250, vel 6, logins 5, 1 prior CB → 130 → 100
        _tx(merchant_category="gift_cards", is_international=1, device_risk_score=81,
            amount_usd=1250, velocity_24h=6, failed_logins_24h=5, prior_chargebacks=1),
        # tx 50006: electronics, NG, device 77, $400, vel 7, logins 6, 2 prior CBs → 100
        _tx(merchant_category="electronics", is_international=1, device_risk_score=77,
            amount_usd=399.99, velocity_24h=7, failed_logins_24h=6, prior_chargebacks=2),
        # tx 50008: gift_cards, IN, device 68, $620, vel 5, logins 3, 1 prior CB → 75
        _tx(merchant_category="gift_cards", is_international=1, device_risk_score=68,
            amount_usd=620, velocity_24h=5, failed_logins_24h=3, prior_chargebacks=1),
        # tx 50011: crypto, RU, device 85, $1400, vel 8, logins 7, 3 prior CBs → 145 → 100
        _tx(merchant_category="crypto", is_international=1, device_risk_score=85,
            amount_usd=1400, velocity_24h=8, failed_logins_24h=7, prior_chargebacks=3),
        # tx 50013: gift_cards, PH, device 79, $150, vel 7, logins 5, 1 prior CB → 105 → 100
        _tx(merchant_category="gift_cards", is_international=1, device_risk_score=79,
            amount_usd=150, velocity_24h=7, failed_logins_24h=5, prior_chargebacks=1),
        # tx 50014: gaming, NG, device 72, $50, vel 9, logins 7, 2 prior CBs → 110 → 100
        _tx(merchant_category="gaming", is_international=1, device_risk_score=72,
            amount_usd=49.99, velocity_24h=9, failed_logins_24h=7, prior_chargebacks=2),
        # tx 50015: electronics, IN, device 71, $910, vel 6, logins 4, 1 prior CB → 85
        _tx(merchant_category="electronics", is_international=1, device_risk_score=71,
            amount_usd=910, velocity_24h=6, failed_logins_24h=4, prior_chargebacks=1),
        # tx 50019: gaming, RU, device 83, $75, vel 10, logins 8, 3 prior CBs → 110 → 100
        _tx(merchant_category="gaming", is_international=1, device_risk_score=83,
            amount_usd=75, velocity_24h=10, failed_logins_24h=8, prior_chargebacks=3),
    ]
    for tx in fraud_profiles:
        score = score_transaction(tx)
        assert label_risk(score) == "high", (
            f"Expected high risk but got score={score} for {tx}"
        )


def test_clean_transaction_profiles_score_low():
    """Transactions with no chargeback and benign signals should score low."""
    clean_profiles = [
        # tx 50001: grocery, US, device 8, $45, vel 1, logins 0, 0 CBs → 0
        _tx(merchant_category="grocery", device_risk_score=8, amount_usd=45.2),
        # tx 50004: streaming, CA, device 12, $15, vel 1, logins 0, 0 CBs → 0
        _tx(merchant_category="streaming", device_risk_score=12, amount_usd=14.99),
        # tx 50009: food_delivery, US, device 6, $18, vel 1, logins 0, 0 CBs → 0
        _tx(merchant_category="food_delivery", device_risk_score=6, amount_usd=18.4),
        # tx 50016: grocery, US, device 9, $35, vel 1, logins 0, 0 CBs → 0
        _tx(merchant_category="grocery", device_risk_score=9, amount_usd=35.0),
    ]
    for tx in clean_profiles:
        score = score_transaction(tx)
        assert label_risk(score) == "low", (
            f"Expected low risk but got score={score} for {tx}"
        )


def test_pinned_scores():
    """Exact score values for representative profiles. Update intentionally if weights change."""
    # Borderline fraud catch: gift_cards + intl + mid device + mid amount + some vel/login pressure
    assert score_transaction(_tx(
        merchant_category="gift_cards", is_international=1, device_risk_score=68,
        amount_usd=620, velocity_24h=5, failed_logins_24h=3, prior_chargebacks=1,
    )) == 75

    # High-value domestic travel (no CB in data, should be medium not high)
    assert score_transaction(_tx(
        merchant_category="travel", is_international=0, device_risk_score=52,
        amount_usd=2200, velocity_24h=1, failed_logins_24h=0, prior_chargebacks=0,
    )) == 35

    # Pure signal isolation: international only
    assert score_transaction(_tx(is_international=1)) == 15

    # Pure signal isolation: high device + high amount
    assert score_transaction(_tx(device_risk_score=75, amount_usd=1500)) == 50
