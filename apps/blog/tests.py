import json

import pytest
from django.apps import apps as django_apps
from django.core.checks import run_checks
from django.test import override_settings
from django.urls import reverse

from apps.blog.markdown import render_blog_markdown
from apps.blog.services import blog_post_schema, get_blog_post, json_ld, list_blog_posts
from awesome_repos.sitemaps import BlogPostSitemap

pytestmark = pytest.mark.django_db


@pytest.fixture
def blog_posts_dir(tmp_path, settings):
    settings.BLOG_POSTS_DIR = tmp_path
    settings.SITE_URL = "https://awesome.example"
    return tmp_path


def response_text(response):
    return response.content.decode()


def write_post(blog_posts_dir, slug, frontmatter, body):
    fields = "\n".join(f"{key}: {value}" for key, value in frontmatter.items())
    path = blog_posts_dir / f"{slug}.md"
    path.write_text(f"---\n{fields}\n---\n\n{body}\n", encoding="utf-8")
    return path


def test_render_blog_markdown_preserves_safe_code_and_table_attrs():
    rendered = render_blog_markdown(
        '<pre class="language-python hljs invalid$class" onclick="bad()">'
        '<code class="language-python" style="color:red">print("hi")</code>'
        "</pre>"
        '<table><tbody><tr><td align="center" onclick="bad()">Cell</td>'
        '<th align="diagonal">Head</th></tr></tbody></table>'
    )

    assert '<pre class="language-python hljs">' in rendered
    assert '<code class="language-python">' in rendered
    assert '<td align="center">' in rendered
    assert "<th>" in rendered
    assert "invalid$class" not in rendered
    assert "onclick" not in rendered
    assert "style=" not in rendered

    rendered_structure = render_blog_markdown("##### Deep\n\n###### Deeper\n\n---")
    assert "<h5>Deep</h5>" in rendered_structure
    assert "<h6>Deeper</h6>" in rendered_structure
    assert "<hr>" in rendered_structure


def test_blog_index_renders_empty_state(client, blog_posts_dir):
    response = client.get(reverse("blog:post_list"))

    assert response.status_code == 200
    content = response_text(response)
    assert "No blog posts have been published yet." in content
    assert 'href="https://awesome.example/blog/"' in content


def test_blog_post_renders_markdown_and_frontmatter_metadata(client, blog_posts_dir):
    write_post(
        blog_posts_dir,
        "best-django-repositories",
        {
            "title": "Best Django repositories",
            "description": "A curated guide to Django repositories.",
            "published_at": "2026-07-03",
            "updated_at": "2026-07-04",
            "author": "Rasul Kireev",
            "seo_title": "Best Django Repositories - Awesome",
            "meta_description": "Find maintained Django repositories from awesome lists.",
            "keywords": "[Django, repository discovery]",
            "categories": "[Django]",
            "tags": "[pSEO, repository-discovery]",
            "image": "/static/brand/awesome-repos-social.png",
            "image_alt": "Awesome repository discovery preview",
        },
        "## Start here\n[Visit](https://example.com)\n<script>alert('x')</script>",
    )

    response = client.get(reverse("blog:post_detail", kwargs={"slug": "best-django-repositories"}))

    assert response.status_code == 200
    content = response_text(response)
    assert "<title>Best Django Repositories - Awesome</title>" in content
    assert (
        '<meta name="description" content="Find maintained Django repositories from awesome lists."'
        in content
    )
    assert (
        '<link rel="canonical" href="https://awesome.example/blog/best-django-repositories/"'
        in content
    )
    assert "<h2>Start here</h2>" in content
    assert 'href="https://example.com" rel="noopener noreferrer"' in content
    assert "alert('x')" not in content
    assert 'property="article:published_time" content="2026-07-03T00:00:00+00:00"' in content
    assert (
        'property="og:image" content="https://awesome.example/static/brand/awesome-repos-social.png"'
        in content
    )
    assert 'property="og:image:type"' not in content
    assert "Awesome repository discovery preview" in content
    assert '"@type": "BlogPosting"' in content
    assert '"datePublished": "2026-07-03T00:00:00+00:00"' in content
    assert "Django" in content
    assert "pSEO" in content


def test_blog_posts_are_sorted_by_publication_date(blog_posts_dir):
    write_post(
        blog_posts_dir,
        "older-post",
        {
            "title": "Older post",
            "description": "Older description.",
            "published_at": "2026-07-01",
        },
        "Older body.",
    )
    write_post(
        blog_posts_dir,
        "newer-post",
        {
            "title": "Newer post",
            "description": "Newer description.",
            "published_at": "2026-07-03",
        },
        "Newer body.",
    )

    assert [post.slug for post in list_blog_posts()] == ["newer-post", "older-post"]


def test_blog_index_skips_invalid_markdown_files(client, blog_posts_dir):
    write_post(
        blog_posts_dir,
        "valid-post",
        {
            "title": "Valid post",
            "description": "Valid description.",
            "published_at": "2026-07-03",
        },
        "Valid body.",
    )
    (blog_posts_dir / "invalid-post.md").write_text(
        "---\ntitle: Missing description\npublished_at: 2026-07-03\n---\n\nInvalid body.\n",
        encoding="utf-8",
    )

    response = client.get(reverse("blog:post_list"))

    assert response.status_code == 200
    content = response_text(response)
    assert "Valid post" in content
    assert "Invalid body" not in content


def test_blog_scans_skip_symlinks_outside_posts_dir(blog_posts_dir):
    write_post(
        blog_posts_dir,
        "valid-post",
        {
            "title": "Valid post",
            "description": "Valid description.",
            "published_at": "2026-07-03",
        },
        "Valid body.",
    )
    outside_dir = blog_posts_dir.parent / "outside"
    outside_dir.mkdir()
    outside_post = outside_dir / "outside-post.md"
    outside_post.write_text(
        "---\n"
        "title: Outside\n"
        "description: Outside description.\n"
        "published_at: 2026-07-03\n"
        "---\n\n"
        "Body.\n",
        encoding="utf-8",
    )
    (blog_posts_dir / "outside-post.md").symlink_to(outside_post)

    assert [post.slug for post in list_blog_posts()] == ["valid-post"]
    assert run_checks() == []


def test_blog_post_404s_when_markdown_file_is_missing(client, blog_posts_dir):
    response = client.get(reverse("blog:post_detail", kwargs={"slug": "missing-post"}))

    assert response.status_code == 404


def test_blog_post_404s_when_frontmatter_is_invalid(client, blog_posts_dir):
    (blog_posts_dir / "invalid-post.md").write_text(
        "---\n"
        "title: Invalid post\n"
        "description: Invalid description.\n"
        "published_at: not-a-date\n"
        "---\n\n"
        "Body.\n",
        encoding="utf-8",
    )

    response = client.get(reverse("blog:post_detail", kwargs={"slug": "invalid-post"}))

    assert response.status_code == 404


def test_blog_frontmatter_check_reports_missing_seo_fields(blog_posts_dir):
    (blog_posts_dir / "missing-description.md").write_text(
        "---\ntitle: Missing description\npublished_at: 2026-07-03\n---\n\nBody.\n",
        encoding="utf-8",
    )

    errors = run_checks()

    assert len(errors) == 1
    assert errors[0].id == "blog.E001"
    assert "missing required frontmatter: description" in errors[0].msg


def test_blog_frontmatter_check_respects_app_configs(blog_posts_dir):
    (blog_posts_dir / "missing-description.md").write_text(
        "---\ntitle: Missing description\npublished_at: 2026-07-03\n---\n\nBody.\n",
        encoding="utf-8",
    )

    assert run_checks(app_configs=[django_apps.get_app_config("pages")]) == []

    errors = run_checks(app_configs=[django_apps.get_app_config("blog")])
    assert len(errors) == 1
    assert errors[0].id == "blog.E001"


@override_settings(SITE_URL="https://awesome.example")
def test_blog_sitemap_uses_markdown_posts(blog_posts_dir):
    write_post(
        blog_posts_dir,
        "sitemap-post",
        {
            "title": "Sitemap post",
            "description": "Sitemap description.",
            "published_at": "2026-07-03",
            "updated_at": "2026-07-04",
        },
        "Sitemap body.",
    )

    sitemap = BlogPostSitemap()
    post = sitemap.items()[0]

    assert sitemap.location(post) == "/blog/sitemap-post/"
    assert sitemap.lastmod(post).isoformat() == "2026-07-04T00:00:00+00:00"


def test_blog_post_schema_uses_checked_in_markdown_content(blog_posts_dir):
    write_post(
        blog_posts_dir,
        "schema-post",
        {
            "title": "Schema post",
            "description": "Schema description.",
            "published_at": "2026-07-03",
        },
        "The article body comes from markdown.",
    )

    post = get_blog_post("schema-post")
    schema = json.loads(json_ld(blog_post_schema(post)))

    assert schema["headline"] == "Schema post"
    assert schema["url"] == "https://awesome.example/blog/schema-post/"
    assert schema["articleBody"] == "The article body comes from markdown."


def test_blog_post_reading_time_uses_rendered_plain_text(blog_posts_dir):
    noisy_url = "https://example.com/" + "/".join(f"token-{index}" for index in range(350))
    write_post(
        blog_posts_dir,
        "reading-time-post",
        {
            "title": "Reading time post",
            "description": "Reading time description.",
            "published_at": "2026-07-03",
        },
        f"[One visible word]({noisy_url})",
    )

    post = get_blog_post("reading-time-post")

    assert post.reading_time_minutes == 1
