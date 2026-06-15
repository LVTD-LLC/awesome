import pytest
from django.test import override_settings

from apps.blog.markdown import render_blog_markdown
from apps.blog.models import BlogCategory, BlogPost, BlogTag


def response_text(response):
    return response.content.decode()


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


@pytest.mark.django_db
def test_blog_post_status_update_does_not_rerender_markdown(monkeypatch):
    post = BlogPost.objects.create(
        title="Render once",
        slug="render-once",
        content_markdown="Original body.",
    )
    original_html = post.content_html

    monkeypatch.setattr("apps.blog.models.render_blog_markdown", lambda _value: "<p>Changed.</p>")
    post.status = BlogPost.Status.REVIEW
    post.save(update_fields=["status"])

    post.refresh_from_db()
    assert post.content_html == original_html


@pytest.mark.django_db
@override_settings(SITE_URL="https://awesome.example")
def test_public_blog_pages_and_sitemap_only_show_published_posts(client):
    category = BlogCategory.objects.create(name="Django", slug="django")
    tag = BlogTag.objects.create(name="pSEO", slug="pseo")
    published = BlogPost.objects.create(
        title="Best Django repositories",
        slug="best-django-repositories",
        excerpt="A curated guide to Django repositories.",
        content_markdown="## Start here\n[Visit](https://example.com)",
        status=BlogPost.Status.PUBLISHED,
        meta_description="A curated guide to Django repositories on Awesome.",
    )
    published.categories.add(category)
    published.tags.add(tag)
    draft = BlogPost.objects.create(
        title="Draft guide",
        slug="draft-guide",
        content_markdown="Not public yet.",
        status=BlogPost.Status.DRAFT,
    )

    list_response = client.get("/blog/")
    detail_response = client.get(published.get_absolute_url())
    draft_response = client.get(draft.get_absolute_url())
    sitemap_response = client.get("/sitemap.xml")

    assert list_response.status_code == 200
    list_content = response_text(list_response)
    assert "Best Django repositories" in list_content
    assert "Draft guide" not in list_content
    assert detail_response.status_code == 200
    detail_content = response_text(detail_response)
    assert "<h2>Start here</h2>" in detail_content
    assert 'href="https://example.com" rel="noopener noreferrer"' in detail_content
    assert draft_response.status_code == 404
    assert sitemap_response.status_code == 200
    sitemap_content = response_text(sitemap_response)
    assert "<loc>https://awesome.example/blog/</loc>" in sitemap_content
    assert "<loc>https://awesome.example/blog/best-django-repositories/</loc>" in sitemap_content
    assert "<loc>https://awesome.example/blog/draft-guide/</loc>" not in sitemap_content
