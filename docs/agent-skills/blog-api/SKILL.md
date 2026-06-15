---
name: awesome-blog-api
description: Use the private Awesome blog API to create, review, publish, update, list, and delete blog posts.
---

# Awesome Blog API

Use this skill when an agent needs to manage Awesome blog posts programmatically.

## Access

These endpoints are intentionally hidden from `/api/docs`.

Authenticate as a staff or superuser account using one of:

- `X-API-Key: <staff-or-superuser-api-key>`
- `Authorization: Bearer <staff-or-superuser-api-key>`
- an authenticated staff/superuser Django session

The API base path is `/api/blog`.

## Post Workflow

1. Create a draft with `POST /api/blog/posts`.
2. Patch SEO, taxonomy, or body fields with `PATCH /api/blog/posts/{slug}`.
3. Mark it reviewed with `POST /api/blog/posts/{slug}/review`.
4. Publish it with `POST /api/blog/posts/{slug}/publish`.
5. Verify the public URL returned as `url`, usually `/blog/{slug}/`.

Published posts appear publicly only when `status` is `published` and `published_at` is set.

## Create

`POST /api/blog/posts`

```json
{
  "title": "Best Django repositories",
  "slug": "best-django-repositories",
  "excerpt": "A short summary for list pages.",
  "content_markdown": "## Start here\nBody copy in Markdown.",
  "category_slugs": ["django"],
  "tag_slugs": ["pseo", "repository-discovery"],
  "seo_title": "Best Django Repositories · Awesome",
  "meta_description": "Find maintained Django repositories from curated awesome lists.",
  "target_keyword": "best django repositories",
  "template_key": "repo-roundup",
  "source_data": {
    "seed": "django"
  }
}
```

Notes:

- `title` is required.
- `slug` is optional. If omitted, it is generated from `title`.
- `category_slugs` and `tag_slugs` are optional. Missing categories and tags are created automatically.
- `content_html` is rendered and sanitized by the server from `content_markdown`; do not send HTML directly.
- `status` defaults to `draft`. Valid values are `draft`, `review`, `published`, and `archived`.

## Read And List

`GET /api/blog/posts`

Optional query params:

- `q`
- `status`
- `category`
- `tag`
- `page`
- `page_size` (capped at 100)

`GET /api/blog/posts/{slug}`

Returns the full post payload, including markdown, sanitized HTML, taxonomy, SEO fields, source data, timestamps, and public `url`.

## Update

Use replacement-style updates with:

`PUT /api/blog/posts/{slug}`

Use partial updates with:

`PATCH /api/blog/posts/{slug}`

For both `PUT` and `PATCH`, omitted optional fields are left unchanged. Send an
empty string, empty list, or `null` explicitly when you want to clear a field
that accepts that value.

Patch example:

```json
{
  "meta_description": "Updated search description.",
  "category_slugs": ["django", "python"],
  "tag_slugs": ["pseo"]
}
```

Passing `category_slugs` or `tag_slugs` replaces the existing set. Omit the field to leave it unchanged.

## Review, Publish, Delete

`POST /api/blog/posts/{slug}/review`

Sets `status` to `review`, records `reviewed_by`, and sets `reviewed_at`.

`POST /api/blog/posts/{slug}/publish`

Sets `status` to `published`, fills review fields if missing, and sets `published_at` if missing.

`DELETE /api/blog/posts/{slug}`

Deletes the post and returns `204`.

## Taxonomy

`GET /api/blog/categories`

`GET /api/blog/tags`

Optional query param:

- `limit` (default and maximum: 100)

These list currently known categories and tags up to the bounded limit. Create missing taxonomy by including slugs in post create/update payloads.

## Curl Example

```bash
curl -X POST "$SITE_URL/api/blog/posts" \
  -H "X-API-Key: $AWESOME_STAFF_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Best Django repositories",
    "content_markdown": "## Start here\nUse Awesome to compare Django projects.",
    "category_slugs": ["django"],
    "tag_slugs": ["pseo"]
  }'
```
