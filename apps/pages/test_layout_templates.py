import re

import pytest
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string


@pytest.mark.parametrize("template_name", ["base_landing.html", "base_app.html"])
def test_side_ad_sponsor_checkout_form_includes_csrf_token(template_name):
    content = render_to_string(template_name, {"csrf_token": "csrf-test-token"})

    assert re.search(
        r'<form\b(?=[^>]*\bmethod="post")(?=[^>]*\baction="/sponsor/checkout/")[^>]*>'
        r"[\s\S]*?"
        r'<input\b(?=[^>]*\btype="hidden")'
        r'(?=[^>]*\bname="csrfmiddlewaretoken")(?=[^>]*\bvalue="csrf-test-token")[^>]*>',
        content,
    ), "Sponsor checkout form should render the forwarded CSRF token."


def test_side_ad_rails_use_current_products_and_assets():
    context = {"external_marketing_assets_enabled": False}

    left_rail = render_to_string(
        "components/side_ad_rail.html",
        {**context, "side": "left", "position": "Left"},
    )
    right_rail = render_to_string(
        "components/side_ad_rail.html",
        {**context, "side": "right", "position": "Right"},
    )

    assert "https://rowset.lvtd.dev/" in left_rail
    assert "utm_content=rowset" in left_rail
    assert "Rowset" in left_rail
    assert "/static/ads/rowset-favicon.7805a29f93f8.ico" in left_rail
    assert "FileBridge" not in left_rail
    assert "filebridge.lvtd.dev" not in left_rail

    assert "/static/ads/djass-logo.dbc6395ed338.svg" in left_rail
    assert "/static/ads/lvtd-fire-heart.png" in left_rail
    assert left_rail.count("<img ") == 3
    assert finders.find("ads/rowset-favicon.7805a29f93f8.ico")
    assert finders.find("ads/djass-logo.dbc6395ed338.svg")
    assert finders.find("ads/lvtd-fire-heart.png")

    assert "cleanapp.dev" not in right_rail
    assert "osig.app" not in right_rail
    assert right_rail.count("Your company could be here") == 1
    assert right_rail.count("data-ad-empty-slot=") == 1


def test_side_ad_rail_keeps_paid_sponsor_beside_product_ads():
    right_rail = render_to_string(
        "components/side_ad_rail.html",
        {
            "side": "right",
            "position": "Right",
            "awesome_sponsor_ad": {
                "startup_name": "Paid sponsor",
                "short_description": "Sponsor description",
                "logo_url": "https://example.com/logo.png",
            },
        },
    )

    assert "Paid sponsor" in right_rail
    assert right_rail.count("Your company could be here") == 0
    assert right_rail.count("data-ad-empty-slot=") == 0


@pytest.mark.parametrize("external_assets", [False, True])
def test_updated_ad_products_and_destinations(external_assets):
    content = "".join(
        render_to_string(
            "components/side_ad_rail.html",
            {"side": side, "external_marketing_assets_enabled": external_assets},
        )
        for side in ("left", "right")
    )
    for name, domain in (
        ("ShipRust", "shiprust.com"),
        ("TastefulKit", "tastefulkit.com"),
        ("nitpick", "nitpick.sh"),
        ("PGSandbox", "pgsandbox-mcp.lvtd.dev"),
        ("CiteGuild", "citeguild.com"),
        ("Staleaway", "staleaway.com"),
    ):
        assert name in content
        assert f"https://{domain}/?ref=awesome_repos" in content
        assert f"utm_content={name.lower()}" in content
    for removed in ("askhndigests.com", "gettjalerts.com", "gettalentleads.com"):
        assert removed not in content
    slots = re.findall(r'data-ad-slot="([^"]+)"', content)
    assert len(slots) == len(set(slots)) == 11
    assert 'data-ad-empty-slot="global-right-5"' in content
