# Blog Posts

Published blog posts live in `apps/blog/posts` as Markdown files. Every `*.md`
file in that directory is public on deploy at `/blog/{filename-slug}/`.

Required frontmatter:

```yaml
---
title: Best Django repositories
description: A concise search snippet for the article.
published_at: 2026-07-03
---
```

Optional frontmatter:

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

Use lowercase filename slugs such as `best-django-repositories.md`. There is no
draft status or database sync path; keep unfinished posts outside this folder.
