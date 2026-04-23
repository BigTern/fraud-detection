from risk_rules import label_risk, score_transaction


def _tx(**kwargs) -> dict:
    base = {
        "device_risk_score": 5,
        "is_international": 0,
        "amount_usd": 50,
        "velocity_24h": 1,
        "failed_logins_24h": 0,
        "prior_chargebacks": 0,
    }
    return {**base, **kwargs}


def test_label_risk_thresholds():
    assert label_risk(10) == "low"
    assert label_risk(35) == "medium"
    assert label_risk(75) == "high"


def test_label_risk_boundaries():
    assert label_risk(29) == "low"
    assert label_risk(30) == "medium"
    assert label_risk(59) == "medium"
    assert label_risk(60) == "high"


def test_large_amount_adds_risk():
    assert score_transaction(_tx(amount_usd=1200)) >= 25
    assert score_transaction(_tx(amount_usd=600)) >= 10
    assert score_transaction(_tx(amount_usd=1200)) > score_transaction(_tx(amount_usd=600))


def test_high_device_risk_adds_risk():
    high = score_transaction(_tx(device_risk_score=75))
    mid = score_transaction(_tx(device_risk_score=45))
    low = score_transaction(_tx(device_risk_score=5))
    assert high > mid > low


def test_international_adds_risk():
    assert score_transaction(_tx(is_international=1)) > score_transaction(_tx(is_international=0))


def test_high_velocity_adds_risk():
    assert score_transaction(_tx(velocity_24h=8)) > score_transaction(_tx(velocity_24h=2))
    assert score_transaction(_tx(velocity_24h=4)) > score_transaction(_tx(velocity_24h=2))


def test_failed_logins_add_risk():
    assert score_transaction(_tx(failed_logins_24h=6)) > score_transaction(_tx(failed_logins_24h=3))
    assert score_transaction(_tx(failed_logins_24h=3)) > score_transaction(_tx(failed_logins_24h=0))


def test_prior_chargebacks_add_risk():
    assert score_transaction(_tx(prior_chargebacks=3)) > score_transaction(_tx(prior_chargebacks=1))
    assert score_transaction(_tx(prior_chargebacks=1)) > score_transaction(_tx(prior_chargebacks=0))


def test_score_capped_at_100():
    worst_case = _tx(device_risk_score=90, is_international=1, amount_usd=5000,
                     velocity_24h=10, failed_logins_24h=8, prior_chargebacks=5)
    assert score_transaction(worst_case) == 100


def test_score_minimum_zero():
    clean = _tx(device_risk_score=0, amount_usd=5, velocity_24h=1)
    assert score_transaction(clean) == 0


def test_confirmed_fraud_scores_high():
    """Profile matching tx 50011 (confirmed chargeback): device 85, intl, $1400, vel 8, logins 7, 3 prior CBs."""
    tx_50011 = _tx(device_risk_score=85, is_international=1, amount_usd=1400,
                   velocity_24h=8, failed_logins_24h=7, prior_chargebacks=3)
    assert score_transaction(tx_50011) == 100
    assert label_risk(score_transaction(tx_50011)) == "high"


def test_clean_transaction_scores_low():
    tx_50001 = _tx(device_risk_score=8, is_international=0, amount_usd=45,
                   velocity_24h=1, failed_logins_24h=0, prior_chargebacks=0)
    assert label_risk(score_transaction(tx_50001)) == "low"
