"""Policy for the restricted one-time live gateway test.

Pure rules only. This module never initiates a payment.
"""

TEST_USER = "sisu.student.test+institute.admin@gmail.com"
AMOUNT_MINOR = 5000
CURRENCY = "LKR"


def eligible(user, config):
    """Require every production test protection to be enabled."""
    gateway = config.get("il_cybersource") or {}

    return (
        user == TEST_USER
        and config.get("il_live_gateway_test_enabled") is True
        and gateway.get("enabled") is True
        and gateway.get("mode") == "live"
        and gateway.get("live_checkout_approved") is True
        and config.get("il_payments_paused") is True
        and config.get("il_cybersource_test_users") == [TEST_USER]
    )


def validate_amount(amount_minor, currency):
    """Reject modified amounts, currencies and boolean values."""
    if type(amount_minor) is not int or amount_minor != AMOUNT_MINOR:
        raise ValueError("Invalid live test payment amount")
    if currency != CURRENCY:
        raise ValueError("Invalid live test payment currency")
    return True
