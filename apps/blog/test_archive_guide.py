import json
import re
from datetime import datetime
from html import unescape
from xml.etree import ElementTree

import pytest
from django.template.loader import render_to_string
from django.test import override_settings
from django.urls import reverse
from django.utils.html import strip_tags

from apps.blog.services import get_blog_post


def normalized_text(value):
    return " ".join(unescape(strip_tags(value)).split())


@pytest.mark.django_db
@override_settings(SITE_URL="https://browseawesome.com")
def test_archive_guide_renders_metadata_and_schema_matching_visible_article(client):
    post = get_blog_post("test-saved-webpages-offline")
    response = client.get(post.get_absolute_url())

    assert response.status_code == 200
    content = response.content.decode()
    assert f'<link rel="canonical" href="{post.canonical_url}"' in content
    assert f'<meta property="og:url" content="{post.canonical_url}"' in content
    assert '<meta name="robots" content="index, follow"' in content
    assert "How to test saved web pages offline</h1>" in content
    assert 'aria-labelledby="archive-test-title archive-test-desc"' in content
    assert 'href="/lists/awesome-selfhosted/' in content
    schemas = [
        json.loads(value)
        for value in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL
        )
    ]
    article = next(item for item in schemas if item.get("@type") == "BlogPosting")
    assert article["author"] == {
        "@type": "Organization",
        "name": "Browse Awesome editorial team",
    }
    assert article["mainEntityOfPage"]["@id"] == post.canonical_url
    assert article["dateModified"] == post.updated_at.isoformat()
    graph = next(item["@graph"] for item in schemas if "@graph" in item)
    how_to = next(item for item in graph if item["@type"] == "HowTo")
    headings = re.findall(r"<h2>([1-4])\. (.*?)</h2>", post.html)
    assert len(headings) == 4
    assert [(step["position"], step["name"]) for step in how_to["step"]] == [
        (int(position), normalized_text(heading)) for position, heading in headings
    ]
    faq = next(item for item in graph if item["@type"] == "FAQPage")
    body = normalized_text(post.html)
    assert len(faq["mainEntity"]) == 3
    for question in faq["mainEntity"]:
        assert normalized_text(question["name"]) in body
        assert normalized_text(question["acceptedAnswer"]["text"]) in body
    breadcrumbs = next(item for item in graph if item["@type"] == "BreadcrumbList")
    assert [item["item"] for item in breadcrumbs["itemListElement"]] == [
        "https://browseawesome.com/",
        "https://browseawesome.com/blog/",
        post.canonical_url,
    ]


@pytest.mark.django_db
@override_settings(SITE_URL="https://browseawesome.com")
def test_archive_guide_is_discoverable_in_blog_and_sitemap(client):
    post = get_blog_post("test-saved-webpages-offline")
    listing = client.get(reverse("blog:post_list"))
    sitemap = client.get(reverse("sitemap_section", kwargs={"section": "blog_posts"}))

    assert listing.status_code == sitemap.status_code == 200
    assert f'href="{post.get_absolute_url()}"' in listing.content.decode()
    root = ElementTree.fromstring(sitemap.content)
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    entries = {
        item.find("s:loc", ns).text: item.find("s:lastmod", ns).text
        for item in root.findall("s:url", ns)
    }
    assert datetime.fromisoformat(entries[post.canonical_url]) == post.updated_at


def test_archive_guide_diagram_has_accessible_name_description_and_caption():
    figure = ElementTree.fromstring(render_to_string("blog/includes/archive_test_process.html"))
    diagram = figure.find("svg")

    assert diagram is not None
    assert diagram.attrib["role"] == "img"
    labels = [
        diagram.find(f".//*[@id='{value}']") for value in diagram.attrib["aria-labelledby"].split()
    ]
    assert len(labels) == 2
    assert all(label is not None and "".join(label.itertext()).strip() for label in labels)
    assert {label.tag for label in labels} == {"title", "desc"}
    caption = figure.find("figcaption")
    assert caption is not None and "".join(caption.itertext()).strip()


def test_archive_fixture_keeps_external_image_and_link_as_explicit_boundaries():
    from pathlib import Path

    from django.conf import settings

    fixture_root = Path(settings.BASE_DIR) / "frontend/static/archive-test"
    page = (fixture_root / "page.html").read_text()
    linked = (fixture_root / "linked-page.html").read_text()
    assert 'src="picture.svg"' in page
    assert 'href="linked-page.html"' in page
    assert "The copper heron keeps a paper map." in page
    for document in (page, linked):
        assert '<meta name="robots" content="noindex, follow">' in document
        assert "<script" not in document
        assert "<form" not in document
    image = ElementTree.fromstring((fixture_root / "picture.svg").read_text())
    assert image.attrib["viewBox"] == "0 0 480 180"
