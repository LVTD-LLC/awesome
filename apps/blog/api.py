from __future__ import annotations

from datetime import datetime
from typing import Any

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.responses import Status
from pydantic import Field

from apps.api.auth import staff_api_auth
from apps.api.schemas import PaginationOut
from apps.blog.models import BlogCategory, BlogPost, BlogTag
from apps.repos.search_services import DEFAULT_API_PAGE_SIZE, MAX_API_PAGE_SIZE, paginate_queryset

router = Router(tags=["blog"])
BLOG_POST_PAGE_SIZE = DEFAULT_API_PAGE_SIZE


class BlogCategoryOut(Schema):
    id: int
    name: str
    slug: str
    description: str


class BlogTagOut(Schema):
    id: int
    name: str
    slug: str


class BlogPostOut(Schema):
    id: int
    title: str
    slug: str
    excerpt: str
    content_markdown: str
    content_html: str
    status: str
    url: str
    author_id: int | None
    author_username: str
    reviewed_by_id: int | None
    reviewed_by_username: str
    reviewed_at: datetime | None
    published_at: datetime | None
    categories: list[BlogCategoryOut]
    tags: list[BlogTagOut]
    seo_title: str
    meta_description: str
    canonical_url: str
    og_image_url: str
    target_keyword: str
    template_key: str
    source_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class BlogPostSearchOut(Schema):
    pagination: PaginationOut
    results: list[BlogPostOut]


class BlogPostWriteIn(Schema):
    title: str
    slug: str = ""
    excerpt: str = ""
    content_markdown: str = ""
    status: str = BlogPost.Status.DRAFT
    author_id: int | None = None
    category_slugs: list[str] = Field(default_factory=list)
    tag_slugs: list[str] = Field(default_factory=list)
    seo_title: str = ""
    meta_description: str = ""
    canonical_url: str = ""
    og_image_url: str = ""
    target_keyword: str = ""
    template_key: str = ""
    source_data: dict[str, Any] = Field(default_factory=dict)


class BlogPostPatchIn(Schema):
    title: str | None = None
    slug: str | None = None
    excerpt: str | None = None
    content_markdown: str | None = None
    status: str | None = None
    author_id: int | None = None
    category_slugs: list[str] | None = None
    tag_slugs: list[str] | None = None
    seo_title: str | None = None
    meta_description: str | None = None
    canonical_url: str | None = None
    og_image_url: str | None = None
    target_keyword: str | None = None
    template_key: str | None = None
    source_data: dict[str, Any] | None = None


def _taxonomy_name_from_slug(slug: str) -> str:
    return slug.replace("-", " ").strip().title() or slug


def _normalize_slug(value: str) -> str:
    return slugify((value or "").strip())


def _validate_status(status: str) -> str:
    if status not in BlogPost.Status.values:
        raise HttpError(400, f"Unknown blog post status: {status}.")
    return status


def _validate_author_id(author_id: int | None) -> int | None:
    if author_id is None:
        return None
    if not get_user_model().objects.filter(pk=author_id).exists():
        raise HttpError(400, f"Unknown author_id: {author_id}.")
    return author_id


def _unique_post_slug(title: str, requested_slug: str = "", post: BlogPost | None = None) -> str:
    base_slug = _normalize_slug(requested_slug) or _normalize_slug(title)
    if not base_slug:
        raise HttpError(400, "Blog post slug could not be generated.")

    queryset = BlogPost.objects.all()
    if post is not None:
        queryset = queryset.exclude(pk=post.pk)
    if requested_slug and queryset.filter(slug=base_slug).exists():
        raise HttpError(409, f"Blog post slug already exists: {base_slug}.")
    if requested_slug:
        return base_slug

    slug = base_slug
    suffix = 2
    while queryset.filter(slug=slug).exists():
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    return slug


def _set_taxonomy(post: BlogPost, category_slugs: list[str] | None, tag_slugs: list[str] | None):
    if category_slugs is not None:
        categories = []
        for value in category_slugs:
            slug = _normalize_slug(value)
            if not slug:
                continue
            category, _created = BlogCategory.objects.get_or_create(
                slug=slug,
                defaults={"name": _taxonomy_name_from_slug(slug)},
            )
            categories.append(category)
        post.categories.set(categories)

    if tag_slugs is not None:
        tags = []
        for value in tag_slugs:
            slug = _normalize_slug(value)
            if not slug:
                continue
            tag, _created = BlogTag.objects.get_or_create(
                slug=slug,
                defaults={"name": _taxonomy_name_from_slug(slug)},
            )
            tags.append(tag)
        post.tags.set(tags)


def _serialize_category(category: BlogCategory) -> dict:
    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "description": category.description,
    }


def _serialize_tag(tag: BlogTag) -> dict:
    return {
        "id": tag.id,
        "name": tag.name,
        "slug": tag.slug,
    }


def serialize_blog_post(post: BlogPost) -> dict:
    author = post.author
    reviewed_by = post.reviewed_by
    return {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "excerpt": post.excerpt,
        "content_markdown": post.content_markdown,
        "content_html": post.content_html,
        "status": post.status,
        "url": post.get_absolute_url(),
        "author_id": author.id if author else None,
        "author_username": author.get_username() if author else "",
        "reviewed_by_id": reviewed_by.id if reviewed_by else None,
        "reviewed_by_username": reviewed_by.get_username() if reviewed_by else "",
        "reviewed_at": post.reviewed_at,
        "published_at": post.published_at,
        "categories": [_serialize_category(category) for category in post.categories.all()],
        "tags": [_serialize_tag(tag) for tag in post.tags.all()],
        "seo_title": post.seo_title,
        "meta_description": post.meta_description,
        "canonical_url": post.canonical_url,
        "og_image_url": post.og_image_url,
        "target_keyword": post.target_keyword,
        "template_key": post.template_key,
        "source_data": post.source_data,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
    }


def _post_queryset():
    return (
        BlogPost.objects.select_related("author", "reviewed_by")
        .prefetch_related("categories", "tags")
        .order_by("-updated_at")
    )


BLOG_POST_TEXT_FIELDS = [
    "excerpt",
    "content_markdown",
    "seo_title",
    "meta_description",
    "canonical_url",
    "og_image_url",
    "target_keyword",
    "template_key",
]


def _apply_post_identity(post: BlogPost, data: dict, request: HttpRequest, *, create: bool):
    title = data.get("title")
    requested_slug = data.get("slug")

    if create:
        post.title = title.strip()
        post.slug = _unique_post_slug(post.title, requested_slug)
        post.author = request.auth.user
        return

    if title is not None:
        post.title = title.strip()
    if requested_slug is not None:
        post.slug = _unique_post_slug(post.title, requested_slug, post=post)


def _apply_post_metadata(post: BlogPost, data: dict):
    for field_name in BLOG_POST_TEXT_FIELDS:
        if field_name in data:
            setattr(post, field_name, data[field_name] or "")

    if "status" in data:
        post.status = _validate_status(data["status"])

    if "source_data" in data:
        post.source_data = data["source_data"] or {}

    if "author_id" in data:
        post.author_id = _validate_author_id(data["author_id"])


def _apply_post_data(post: BlogPost, data: dict, request: HttpRequest, *, create: bool):
    _apply_post_identity(post, data, request, create=create)
    if not post.title:
        raise HttpError(400, "Blog post title is required.")
    _apply_post_metadata(post, data)

    try:
        with transaction.atomic():
            post.save()
            _set_taxonomy(post, data.get("category_slugs"), data.get("tag_slugs"))
    except IntegrityError as exc:
        raise HttpError(409, "Blog post slug, category, or tag already exists.") from exc
    return post


def _write_payload(data: BlogPostWriteIn) -> dict:
    return data.model_dump(exclude_unset=True)


@router.get(
    "/posts",
    response=BlogPostSearchOut,
    auth=staff_api_auth,
    include_in_schema=False,
)
def list_blog_posts(
    request: HttpRequest,
    q: str = "",
    status: str = "",
    category: str = "",
    tag: str = "",
    page: int = 1,
    page_size: int = BLOG_POST_PAGE_SIZE,
):
    queryset = _post_queryset()
    if q:
        queryset = queryset.filter(
            Q(title__icontains=q)
            | Q(slug__icontains=q)
            | Q(excerpt__icontains=q)
            | Q(content_markdown__icontains=q)
            | Q(target_keyword__icontains=q)
        )
    if status:
        queryset = queryset.filter(status=_validate_status(status))
    if category:
        queryset = queryset.filter(categories__slug=_normalize_slug(category))
    if tag:
        queryset = queryset.filter(tags__slug=_normalize_slug(tag))

    page_size = min(max(page_size, 1), MAX_API_PAGE_SIZE)
    return paginate_queryset(
        queryset.distinct(),
        page=page,
        page_size=page_size,
        serializer=serialize_blog_post,
    )


@router.post(
    "/posts",
    response={201: BlogPostOut},
    auth=staff_api_auth,
    include_in_schema=False,
)
def create_blog_post(request: HttpRequest, data: BlogPostWriteIn):
    payload = _write_payload(data)
    post = _apply_post_data(BlogPost(), payload, request, create=True)
    return Status(201, serialize_blog_post(post))


@router.get(
    "/posts/{slug}",
    response=BlogPostOut,
    auth=staff_api_auth,
    include_in_schema=False,
)
def get_blog_post(request: HttpRequest, slug: str):
    post = get_object_or_404(_post_queryset(), slug=slug)
    return serialize_blog_post(post)


@router.put(
    "/posts/{slug}",
    response=BlogPostOut,
    auth=staff_api_auth,
    include_in_schema=False,
)
def update_blog_post(request: HttpRequest, slug: str, data: BlogPostWriteIn):
    post = get_object_or_404(_post_queryset(), slug=slug)
    payload = _write_payload(data)
    post = _apply_post_data(post, payload, request, create=False)
    return serialize_blog_post(post)


@router.patch(
    "/posts/{slug}",
    response=BlogPostOut,
    auth=staff_api_auth,
    include_in_schema=False,
)
def patch_blog_post(request: HttpRequest, slug: str, data: BlogPostPatchIn):
    post = get_object_or_404(_post_queryset(), slug=slug)
    payload = data.model_dump(exclude_unset=True)
    post = _apply_post_data(post, payload, request, create=False)
    return serialize_blog_post(post)


@router.delete(
    "/posts/{slug}",
    response={204: None},
    auth=staff_api_auth,
    include_in_schema=False,
)
def delete_blog_post(request: HttpRequest, slug: str):
    post = get_object_or_404(BlogPost, slug=slug)
    post.delete()
    return Status(204, None)


@router.post(
    "/posts/{slug}/review",
    response=BlogPostOut,
    auth=staff_api_auth,
    include_in_schema=False,
)
def review_blog_post(request: HttpRequest, slug: str):
    post = get_object_or_404(_post_queryset(), slug=slug)
    update_fields = ["updated_at"]
    if post.status != BlogPost.Status.PUBLISHED:
        post.status = BlogPost.Status.REVIEW
        post.reviewed_by = request.auth.user
        post.reviewed_at = timezone.now()
        update_fields = ["status", "reviewed_by", "reviewed_at", *update_fields]
    post.save(update_fields=update_fields)
    return serialize_blog_post(post)


@router.post(
    "/posts/{slug}/publish",
    response=BlogPostOut,
    auth=staff_api_auth,
    include_in_schema=False,
)
def publish_blog_post(request: HttpRequest, slug: str):
    post = get_object_or_404(_post_queryset(), slug=slug)
    post.status = BlogPost.Status.PUBLISHED
    post.reviewed_by = post.reviewed_by or request.auth.user
    post.reviewed_at = post.reviewed_at or timezone.now()
    post.published_at = post.published_at or timezone.now()
    post.save(
        update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
            "published_at",
            "updated_at",
        ]
    )
    return serialize_blog_post(post)


@router.get(
    "/categories",
    response=list[BlogCategoryOut],
    auth=staff_api_auth,
    include_in_schema=False,
)
def list_blog_categories(request: HttpRequest, limit: int = MAX_API_PAGE_SIZE):
    limit = min(max(limit, 1), MAX_API_PAGE_SIZE)
    return [_serialize_category(category) for category in BlogCategory.objects.all()[:limit]]


@router.get(
    "/tags",
    response=list[BlogTagOut],
    auth=staff_api_auth,
    include_in_schema=False,
)
def list_blog_tags(request: HttpRequest, limit: int = MAX_API_PAGE_SIZE):
    limit = min(max(limit, 1), MAX_API_PAGE_SIZE)
    return [_serialize_tag(tag) for tag in BlogTag.objects.all()[:limit]]
