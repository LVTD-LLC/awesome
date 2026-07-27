import os

import pytest
from django.conf import settings

from apps.core.payments import (
    create_ads_checkout_session,
    create_highlighted_repo_checkout_session,
    create_remove_ads_checkout_session,
    expire_checkout_session,
    retrieve_checkout_session,
    retrieve_checkout_session_line_items,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("STRIPE_SMOKE_TEST") != "1",
    reason="Set STRIPE_SMOKE_TEST=1 with Stripe test-mode credentials to run.",
)


@pytest.mark.parametrize(
    ("create_session", "price_setting", "kind", "expected_amount"),
    [
        (create_ads_checkout_session, "STRIPE_AWESOME_ADS_PRICE_ID", "sponsor_ads", 100000),
        (
            create_highlighted_repo_checkout_session,
            "STRIPE_AWESOME_HIGHLIGHTED_REPO_PRICE_ID",
            "highlighted_repo",
            50000,
        ),
        (
            create_remove_ads_checkout_session,
            "STRIPE_AWESOME_REMOVE_ADS_PRICE_ID",
            "remove_ads",
            400,
        ),
    ],
)
def test_stripe_test_mode_checkout_contract(
    create_session,
    price_setting,
    kind,
    expected_amount,
):
    assert settings.STRIPE_SECRET_KEY.startswith("sk_test_"), (
        "Stripe smoke tests refuse to run with a non-test secret key."
    )
    expected_price_id = getattr(settings, price_setting)
    assert expected_price_id.startswith("price_")

    session = create_session(
        success_url="https://example.com/payment-success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://example.com/payment-cancelled",
        client_reference_id="stripe-smoke-test",
    )

    try:
        retrieved = retrieve_checkout_session(session["id"])
        line_items = retrieve_checkout_session_line_items(session["id"])
        item = line_items["data"][0]

        assert retrieved["livemode"] is False
        assert retrieved["mode"] == "payment"
        assert retrieved["payment_status"] == "unpaid"
        assert retrieved["metadata"]["app"] == "awesome"
        assert retrieved["metadata"]["kind"] == kind
        assert item["price"]["id"] == expected_price_id
        assert item["price"]["unit_amount"] == expected_amount
        assert item["quantity"] == 1
    finally:
        expire_checkout_session(session["id"])
