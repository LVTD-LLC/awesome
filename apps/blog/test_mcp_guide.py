import re
from html import unescape
from xml.etree import ElementTree

from django.template.loader import render_to_string
from django.test import override_settings
from django.utils.html import strip_tags

from apps.blog.services import get_blog_post, mcp_discovery_schema


def normalized_text(value):
    return " ".join(unescape(strip_tags(value)).split())


@override_settings(SITE_URL="https://browseawesome.com")
def test_mcp_guide_structured_steps_and_faq_match_visible_article():
    post = get_blog_post("search-awesome-lists-with-mcp")
    graph = mcp_discovery_schema(post)["@graph"]
    how_to = next(item for item in graph if item["@type"] == "HowTo")
    headings = re.findall(r"<h2>([1-5])\. (.*?)</h2>", post.html)

    assert len(headings) == 5
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


def test_mcp_guide_diagram_has_accessible_name_description_and_caption():
    figure = ElementTree.fromstring(render_to_string("blog/includes/mcp_discovery_process.html"))
    diagram = figure.find("svg")

    assert diagram is not None
    assert diagram.attrib["role"] == "img"
    label_ids = diagram.attrib["aria-labelledby"].split()
    assert len(label_ids) == 2
    labels = [diagram.find(f".//*[@id='{label_id}']") for label_id in label_ids]
    assert all(label is not None and "".join(label.itertext()).strip() for label in labels)
    assert {label.tag for label in labels} == {"title", "desc"}
    caption = figure.find("figcaption")
    assert caption is not None and "".join(caption.itertext()).strip()
