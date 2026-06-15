from __future__ import annotations

import re

import markdown as md
import nh3

SAFE_ALIGN_VALUES = {"center", "justify", "left", "right"}
SAFE_CLASS_RE = re.compile(r"^[A-Za-z0-9_-]+$")
SAFE_CLASS_TAGS = {"code", "pre"}
SAFE_URL_SCHEMES = {"http", "https", "mailto"}
# Images stay out of the allowlist unless src proxying or stricter URL validation is added.
SAFE_TAGS = {
    "a",
    "blockquote",
    "br",
    "code",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
}
SAFE_ATTRIBUTES = {
    "a": {"href"},
    "code": {"class"},
    "pre": {"class"},
    "td": {"align"},
    "th": {"align"},
}


def _filter_attribute(tag: str, attr: str, value: str) -> str | None:
    if tag in SAFE_CLASS_TAGS and attr == "class":
        safe_classes = [
            class_name for class_name in value.split() if SAFE_CLASS_RE.fullmatch(class_name)
        ]
        return " ".join(safe_classes) or None
    if tag in {"td", "th"} and attr == "align":
        align = value.lower()
        return align if align in SAFE_ALIGN_VALUES else None
    return value


def render_blog_markdown(markdown_text: str) -> str:
    rendered = md.Markdown(extensions=["tables"]).convert(markdown_text or "")
    return nh3.clean(
        rendered,
        tags=SAFE_TAGS,
        clean_content_tags={"script", "style"},
        attributes=SAFE_ATTRIBUTES,
        attribute_filter=_filter_attribute,
        url_schemes=SAFE_URL_SCHEMES,
    )
