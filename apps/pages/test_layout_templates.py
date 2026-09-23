import re
from html.parser import HTMLParser

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
    assert right_rail.count("Your company could be here") == 3
    assert right_rail.count("data-ad-empty-slot=") == 3


def test_side_ad_rail_keeps_paid_sponsor_beside_two_open_slots():
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
    assert right_rail.count("Your company could be here") == 2
    assert right_rail.count("data-ad-empty-slot=") == 2


class AdLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.append(dict(attrs))


@pytest.mark.parametrize(
    ("template_name", "context", "expected_links"),
    [
        ("side_ad_rail.html", {"side": "left"}, 5),
        ("side_ad_rail.html", {"side": "right"}, 2),
        (
            "side_ad_rail.html",
            {
                "side": "right",
                "awesome_sponsor_ad": {
                    "startup_name": "Paid sponsor",
                    "destination_url": "https://sponsor.example/",
                },
            },
            3,
        ),
        ("highlighted_repo_slot.html", {}, 1),
        ("landing_highlighted_repo.html", {}, 1),
    ],
)
def test_all_ad_destination_links_are_sponsored(template_name, context, expected_links):
    content = render_to_string(
        f"components/{template_name}",
        {
            "awesome_highlighted_repo": {
                "repo_url": "https://github.com/example/promoted",
                "repo_full_name": "example/promoted",
            },
            **context,
        },
    )
    parser = AdLinkParser()
    parser.feed(content)

    assert len(parser.links) == expected_links
    for link in parser.links:
        assert "sponsored" in link.get("rel", "").split(), link
