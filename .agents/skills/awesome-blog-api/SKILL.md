---
name: awesome-blog-posts
description: >
  Add, inspect, update, or remove Awesome blog posts as checked-in Markdown
  files. Use this whenever an agent needs to work on Awesome blog content.
---

# Awesome Blog Posts

Awesome publishes blog posts from Markdown files in `apps/blog/posts`. There is
no database-backed authoring path and no `/api/blog` management API. Every
`*.md` file in that directory is public after deployment.

## Workflow

1. Create or edit a Markdown file in `apps/blog/posts`.
2. Use the lowercase filename slug as the URL slug, for example
   `best-django-repositories.md` publishes at `/blog/best-django-repositories/`.
3. Keep unfinished drafts outside `apps/blog/posts`.
4. Run the blog tests and Django checks before finishing.

## Required Frontmatter

```yaml
---
title: Best Django repositories
description: A concise search snippet for the article.
published_at: 2026-07-03
---
```

## Optional Frontmatter

```yaml
updated_at: 2026-07-04
author: Rasul Kireev
seo_title: Best Django Repositories - Awesome
meta_description: Find maintained Django repositories from awesome lists.
keywords:
  - Django
  - repository discovery
categories:
  - Django
tags:
  - pSEO
canonical_url: https://awesome.lvtd.dev/blog/best-django-repositories/
image: /static/brand/awesome-repos-social.png
image_alt: Awesome repository discovery preview
robots: index, follow
```

## Content Rules

- Write article body content below the closing frontmatter delimiter.
- Use Markdown for headings, links, lists, code blocks, and tables.
- Do not send or store raw generated HTML; the server renders and sanitizes
  Markdown at request time.
- Use `description` for the visible post summary and default search snippet.
- Use `meta_description` only when the search/social snippet should differ from
  the visible summary.
- Use `seo_title` only when the browser/search title should differ from the
  visible article title.
- Use absolute canonical URLs only when intentionally consolidating with another
  page. Otherwise omit `canonical_url` and the server will use the post URL.

## Validation

Run focused checks after changing posts:

```bash
make test apps/blog -q
make manage check
```

The `blog.E001` Django system check reports invalid frontmatter before deploy.
