from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from urllib.parse import urlsplit

import yaml
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.html import strip_tags

from apps.blog.markdown import render_blog_markdown

BLOG_TITLE = "Awesome Blog"
BLOG_DESCRIPTION = "Research notes, repository discovery guides, and product updates from Awesome."
BLOG_DEFAULT_AUTHOR = "Rasul Kireev"
BLOG_PUBLISHER_NAME = "LVTD LLC"
BLOG_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
BLOG_REQUIRED_FRONTMATTER = ("title", "description", "published_at")


class BlogPostNotFound(Exception):
    pass


class BlogPostValidationError(ValueError):
    pass


@dataclass(frozen=True)
class BlogPost:
    slug: str
    title: str
    description: str
    content: str
    html: str
    published_at: datetime
    updated_at: datetime
    author: str
    seo_title: str
    meta_description: str
    keywords: tuple[str, ...]
    categories: tuple[str, ...]
    tags: tuple[str, ...]
    canonical_url: str
    image_url: str
    image_alt: str
    robots: str
    reading_time_minutes: int
    source_path: Path

    def get_absolute_url(self):
        return reverse("blog:post_detail", kwargs={"slug": self.slug})

    @property
    def display_title(self) -> str:
        return self.seo_title or self.title

    @property
    def seo_description(self) -> str:
        return self.meta_description or self.description

    @property
    def metadata_keywords(self) -> tuple[str, ...]:
        return self.keywords or (*self.categories, *self.tags)


def get_blog_posts_dir() -> Path:
    return Path(getattr(settings, "BLOG_POSTS_DIR", settings.BASE_DIR / "apps" / "blog" / "posts"))


def build_absolute_public_url(path: str) -> str:
    parsed = urlsplit(path)
    if parsed.scheme in {"http", "https"}:
        return path
    return f"{settings.SITE_URL.rstrip('/')}/{path.lstrip('/')}"


def default_blog_image_url() -> str:
    return build_absolute_public_url(static("brand/awesome-repos-social.png"))


def is_blog_slug(value: str) -> bool:
    return bool(BLOG_SLUG_PATTERN.fullmatch(value))


def _coerce_string(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _ensure_aware_datetime(value: datetime) -> datetime:
    if timezone.is_naive(value):
        return timezone.make_aware(value, timezone.get_default_timezone())
    return value


def _coerce_datetime(value, field_name: str, source_path: Path) -> datetime:
    if isinstance(value, datetime):
        return _ensure_aware_datetime(value)
    if isinstance(value, date):
        return _ensure_aware_datetime(datetime.combine(value, time.min))
    if isinstance(value, str):
        parsed_datetime = parse_datetime(value)
        if parsed_datetime:
            return _ensure_aware_datetime(parsed_datetime)
        parsed_date = parse_date(value)
        if parsed_date:
            return _ensure_aware_datetime(datetime.combine(parsed_date, time.min))
    raise BlogPostValidationError(
        f"{source_path}: frontmatter field '{field_name}' must be a date or datetime."
    )


def _coerce_list(value) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        values = value.split(",")
    elif isinstance(value, list | tuple | set):
        values = value
    else:
        values = [value]
    return tuple(item for item in (_coerce_string(item) for item in values) if item)


def _absolute_public_url(value: str) -> str:
    url = _coerce_string(value)
    if not url:
        return default_blog_image_url()
    return build_absolute_public_url(url)


def _reading_time_minutes(rendered_html: str) -> int:
    word_count = len(re.findall(r"\w+", _plain_text_from_html(rendered_html)))
    return max(1, round(word_count / 220))


def _plain_text_from_html(html: str) -> str:
    return re.sub(r"\s+", " ", strip_tags(html)).strip()


def _validate_source_path(source_path: Path, content_dir: Path) -> None:
    if not source_path.is_relative_to(content_dir):
        raise BlogPostNotFound
    if source_path.suffix != ".md" or not source_path.exists():
        raise BlogPostNotFound
    if not is_blog_slug(source_path.stem):
        raise BlogPostValidationError(
            f"{source_path}: filename must be a lowercase URL slug like 'best-django-repos.md'."
        )


def _split_frontmatter(source_path: Path) -> tuple[dict, str]:
    try:
        text = source_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise BlogPostNotFound from exc
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise BlogPostValidationError(f"{source_path}: missing YAML frontmatter block.")

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            metadata_text = "\n".join(lines[1:index])
            body = "\n".join(lines[index + 1 :]).strip()
            try:
                metadata = yaml.safe_load(metadata_text) or {}
            except yaml.YAMLError as exc:
                raise BlogPostValidationError(f"{source_path}: invalid YAML frontmatter.") from exc
            if not isinstance(metadata, dict):
                raise BlogPostValidationError(f"{source_path}: frontmatter must be a mapping.")
            return metadata, body

    raise BlogPostValidationError(f"{source_path}: frontmatter block is not closed.")


def load_blog_post(source_path: Path, content_dir: Path | None = None) -> BlogPost:
    content_dir = (content_dir or get_blog_posts_dir()).resolve()
    source_path = source_path.resolve()
    _validate_source_path(source_path, content_dir)

    metadata, content = _split_frontmatter(source_path)
    missing_fields = [
        field for field in BLOG_REQUIRED_FRONTMATTER if not _coerce_string(metadata.get(field))
    ]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise BlogPostValidationError(f"{source_path}: missing required frontmatter: {missing}.")

    slug = source_path.stem
    published_at = _coerce_datetime(metadata.get("published_at"), "published_at", source_path)
    updated_at = (
        _coerce_datetime(metadata.get("updated_at"), "updated_at", source_path)
        if metadata.get("updated_at")
        else published_at
    )
    canonical_url = _coerce_string(metadata.get("canonical_url")) or reverse(
        "blog:post_detail",
        kwargs={"slug": slug},
    )

    html = render_blog_markdown(content)

    return BlogPost(
        slug=slug,
        title=_coerce_string(metadata.get("title")),
        description=_coerce_string(metadata.get("description")),
        content=content,
        html=html,
        published_at=published_at,
        updated_at=updated_at,
        author=_coerce_string(metadata.get("author")) or BLOG_DEFAULT_AUTHOR,
        seo_title=_coerce_string(metadata.get("seo_title")),
        meta_description=_coerce_string(metadata.get("meta_description")),
        keywords=_coerce_list(metadata.get("keywords")),
        categories=_coerce_list(metadata.get("categories")),
        tags=_coerce_list(metadata.get("tags")),
        canonical_url=build_absolute_public_url(canonical_url),
        image_url=_absolute_public_url(metadata.get("image")),
        image_alt=_coerce_string(metadata.get("image_alt"))
        or "Awesome repository discovery preview",
        robots=_coerce_string(metadata.get("robots")) or "index, follow",
        reading_time_minutes=_reading_time_minutes(html),
        source_path=source_path,
    )


def list_blog_posts() -> list[BlogPost]:
    content_dir = get_blog_posts_dir().resolve()
    if not content_dir.exists():
        return []

    posts = []
    for path in content_dir.glob("*.md"):
        try:
            posts.append(load_blog_post(path, content_dir=content_dir))
        except (BlogPostNotFound, BlogPostValidationError):
            # The blog.E001 system check reports invalid posts before deploy.
            pass
    return sorted(posts, key=lambda post: (post.published_at, post.slug), reverse=True)


def get_blog_post(slug: str) -> BlogPost:
    if not is_blog_slug(slug):
        raise BlogPostNotFound

    content_dir = get_blog_posts_dir().resolve()
    source_path = (content_dir / f"{slug}.md").resolve()
    return load_blog_post(source_path, content_dir=content_dir)


def iter_blog_post_validation_errors() -> list[BlogPostValidationError]:
    errors = []
    content_dir = get_blog_posts_dir().resolve()
    if not content_dir.exists():
        return errors

    for source_path in content_dir.glob("*.md"):
        try:
            load_blog_post(source_path, content_dir=content_dir)
        except BlogPostValidationError as exc:
            errors.append(exc)
        except BlogPostNotFound:
            pass
    return errors


def blog_index_url() -> str:
    return build_absolute_public_url(reverse("blog:post_list"))


def blog_post_schema(post: BlogPost) -> dict:
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post.title,
        "description": post.seo_description,
        "image": post.image_url,
        "url": post.canonical_url,
        "datePublished": post.published_at.isoformat(),
        "dateModified": post.updated_at.isoformat(),
        "author": {"@type": "Person", "name": post.author},
        "publisher": {
            "@type": "Organization",
            "name": BLOG_PUBLISHER_NAME,
            "logo": {"@type": "ImageObject", "url": default_blog_image_url()},
        },
        "articleBody": _plain_text_from_html(post.html),
        "mainEntityOfPage": {"@type": "WebPage", "@id": post.canonical_url},
    }
    keywords = post.metadata_keywords
    if keywords:
        schema["keywords"] = list(keywords)
    if post.categories:
        schema["articleSection"] = list(post.categories)
    return schema


def blog_index_schema(posts: list[BlogPost]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": BLOG_TITLE,
        "description": BLOG_DESCRIPTION,
        "url": blog_index_url(),
        "publisher": {
            "@type": "Organization",
            "name": BLOG_PUBLISHER_NAME,
            "logo": {"@type": "ImageObject", "url": default_blog_image_url()},
        },
        "blogPost": [
            {
                "@type": "BlogPosting",
                "headline": post.title,
                "description": post.seo_description,
                "url": post.canonical_url,
                "datePublished": post.published_at.isoformat(),
            }
            for post in posts
        ],
    }


def json_ld(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
