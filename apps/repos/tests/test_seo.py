from datetime import date, timedelta

import pytest
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.repos.models import (
    AwesomeList,
    AwesomeListItem,
    NewsletterCadence,
    Repository,
    RepositoryNewsletterIssue,
)
from awesome_repos.sitemaps import RepositoryNewsletterIssueSitemap

pytestmark = pytest.mark.django_db


def response_text(response):
    return response.content.decode()


@override_settings(SITE_URL="https://testserver")
def test_public_search_page_has_complete_seo_metadata(client):
    response = client.get(reverse("repos:search"))

    assert response.status_code == 200
    content = response_text(response)
    assert "<title>Search Awesome Repositories · Awesome</title>" in content
    assert (
        '<meta name="description" content="Search names, descriptions, topics, tags, and '
        'stacks, then tune results by ecosystem, freshness, health, and cross-list signal." />'
        in content
    )
    assert '<meta name="robots" content="index, follow" />' in content
    assert '<link rel="canonical" href="https://testserver/repos/" />' in content
    assert '<meta property="og:title" content="Search Awesome Repositories · Awesome" />' in content
    assert '<meta name="twitter:card" content="summary_large_image" />' in content
    assert '<meta name="keywords"' not in content


@override_settings(SITE_URL="https://testserver")
def test_repository_detail_has_page_specific_metadata_and_schema(client):
    repository = Repository.objects.create(
        full_name="django/django",
        owner="django",
        name="django",
        url="https://github.com/django/django",
        description="The Web framework for perfectionists with deadlines.",
        language="Python",
    )

    response = client.get(repository.get_absolute_url())

    assert response.status_code == 200
    content = response_text(response)
    assert "<title>django/django · Awesome</title>" in content
    assert (
        '<meta name="description" content="The Web framework for perfectionists with deadlines." />'
        in content
    )
    assert '<link rel="canonical" href="https://testserver/repos/django/django/" />' in content
    assert '<meta property="og:type" content="article" />' in content
    assert (
        '<meta property="og:image" '
        'content="https://testserver/repos/django/django/og.png" />' in content
    )
    assert (
        '<meta property="og:image:alt"\n'
        '      content="django/django repository activity on Awesome" />' in content
    )
    assert (
        '<meta name="twitter:image" '
        'content="https://testserver/repos/django/django/og.png" />' in content
    )
    assert '"@type": "SoftwareSourceCode"' in content
    assert '"codeRepository": "https://github.com/django/django"' in content
    assert '"url": "https://testserver/repos/django/django/"' in content


@pytest.mark.parametrize(
    ("archived", "synced", "status_label", "metadata_label"),
    [
        (False, True, "Not archived", "No"),
        (True, True, "Archived", "Yes"),
        (False, False, "Archive status not checked", "Not checked"),
        (True, False, "Archive status not checked", "Not checked"),
    ],
)
def test_repository_archive_status_does_not_assert_maintenance(
    client, archived, synced, status_label, metadata_label
):
    # Even stale, high-star records must not imply current maintenance.
    repository = Repository.objects.create(
        full_name="example/project",
        owner="example",
        name="project",
        url="https://github.com/example/project",
        stars=100_000,
        is_archived=archived,
        last_synced_at=timezone.now() - timedelta(days=180) if synced else None,
        github_pushed_at=timezone.now() - timedelta(days=365),
    )

    response = client.get(repository.get_absolute_url())
    content = response_text(response)

    assert response.status_code == 200
    assert f">{status_label}</span>" in content
    assert f">{metadata_label}</dd>" in content
    assert "Actively maintained" not in content
    assert "not a maintenance assessment" in content
    checklist_path = reverse(
        "blog:post_detail", kwargs={"slug": "how-to-shortlist-github-repositories"}
    )
    assert f'href="{checklist_path}"' in content
    assert client.get(checklist_path).status_code == 200


@override_settings(SITE_URL="https://testserver")
def test_awesome_list_detail_has_page_specific_metadata_and_schema(client):
    awesome_list = AwesomeList.objects.create(
        name="Awesome Django",
        slug="awesome-django",
        source_url="https://github.com/wsvincent/awesome-django",
        description="Curated Django packages and resources.",
    )

    response = client.get(awesome_list.get_absolute_url())

    assert response.status_code == 200
    content = response_text(response)
    assert "<title>Awesome Django · Awesome</title>" in content
    assert '<meta name="description" content="Curated Django packages and resources." />' in content
    assert '<link rel="canonical" href="https://testserver/lists/awesome-django/" />' in content
    assert '"@type": "CollectionPage"' in content
    assert '"url": "https://testserver/lists/awesome-django/"' in content


def test_selfhosted_bookmark_discovery_uses_current_list_route_and_scoped_search(client):
    awesome_list = AwesomeList.objects.create(
        name="Awesome Selfhosted",
        slug="selfhosted-current-slug",
        source_url="https://github.com/awesome-selfhosted/awesome-selfhosted",
        repo_full_name="awesome-selfhosted/awesome-selfhosted",
    )
    for name, description, in_list in (
        ("bookmarks", "A bookmark manager", True),
        ("calendar", "A calendar server", True),
        ("other-bookmarks", "A bookmark manager outside this list", False),
    ):
        repository = Repository.objects.create(
            full_name=f"example/{name}",
            owner="example",
            name=name,
            url=f"https://github.com/example/{name}",
            description=description,
        )
        if in_list:
            AwesomeListItem.objects.create(awesome_list=awesome_list, repository=repository)

    list_path = awesome_list.get_absolute_url()
    response = client.get(list_path)

    assert response.status_code == 200
    content = response_text(response)
    assert "Looking for a bookmark manager?" in content
    assert 'data-discovery-action="selfhosted_bookmarks"' in content
    assert 'data-discovery-action="selfhosted_checklist"' in content
    assert f'href="{list_path}?q=bookmark"' in content
    assert 'href="/blog/how-to-shortlist-github-repositories/"' in content
    assert 'href="/blog/test-saved-webpages-offline/"' in content
    assert 'data-discovery-action="selfhosted_offline_test"' in content

    search_response = client.get(list_path, {"q": "bookmark"})

    assert search_response.status_code == 200
    assert [repo.full_name for repo in search_response.context["page_obj"]] == ["example/bookmarks"]
    assert "Looking for a bookmark manager?" not in response_text(search_response)
    assert 'href="/blog/test-saved-webpages-offline/"' not in response_text(search_response)


@pytest.mark.parametrize(
    "params",
    [
        {"language": "Python"},
        {"topic": "bookmarks"},
        {"mode": "semantic"},
        {"sort": "recent"},
        {"page": "2"},
        {"page": "last"},
    ],
)
def test_selfhosted_bookmark_discovery_does_not_interrupt_refined_browsing(client, params):
    awesome_list = AwesomeList.objects.create(
        name="Awesome Selfhosted",
        slug="awesome-selfhosted",
        source_url="https://github.com/awesome-selfhosted/awesome-selfhosted",
        repo_full_name="awesome-selfhosted/awesome-selfhosted",
    )

    response = client.get(awesome_list.get_absolute_url(), params)

    assert response.status_code == 200
    assert "Looking for a bookmark manager?" not in response_text(response)
    assert 'href="/blog/test-saved-webpages-offline/"' not in response_text(response)


def test_bookmark_discovery_matches_list_source_not_reused_slug(client):
    awesome_list = AwesomeList.objects.create(
        name="Another list",
        slug="awesome-selfhosted",
        source_url="https://github.com/example/another-list",
        repo_full_name="example/another-list",
    )

    response = client.get(awesome_list.get_absolute_url())

    assert response.status_code == 200
    assert "Looking for a bookmark manager?" not in response_text(response)
    assert 'href="/blog/test-saved-webpages-offline/"' not in response_text(response)


@override_settings(SITE_URL="https://testserver")
def test_repository_update_list_has_repository_specific_seo_description(client):
    repository = Repository.objects.create(
        full_name="django/django",
        owner="django",
        name="django",
        url="https://github.com/django/django",
        description="The Web framework for perfectionists with deadlines.",
    )

    response = client.get(
        reverse(
            "repos:newsletter_issue_list",
            kwargs={"owner": repository.owner, "name": repository.name},
        )
    )

    assert response.status_code == 200
    content = response_text(response)
    assert "<title>django/django updates · Awesome</title>" in content
    assert (
        '<meta name="description" content="django/django development updates with generated '
        'weekly and monthly commit summaries, RSS feeds, and email subscriptions." />' in content
    )
    assert (
        '<link rel="canonical" href="https://testserver/repos/django/django/updates/" />' in content
    )
    assert '"@type": "CollectionPage"' in content
    assert "weekly updates" in content


@override_settings(SITE_URL="https://testserver")
def test_repository_update_detail_has_unique_seo_description(client):
    repository = Repository.objects.create(
        full_name="django/django",
        owner="django",
        name="django",
        url="https://github.com/django/django",
        description="The Web framework for perfectionists with deadlines.",
    )
    issue = RepositoryNewsletterIssue.objects.create(
        repository=repository,
        cadence=NewsletterCadence.WEEKLY,
        period_start=date(2026, 5, 25),
        period_end=date(2026, 5, 31),
        slug="2026-05-25",
        title="Django weekly update",
        content_markdown="## Changes\n- Added tracking.",
        content_html="<h2>Changes</h2><ul><li>Added tracking.</li></ul>",
        commit_count=3,
        published_at=timezone.now(),
    )

    response = client.get(issue.get_absolute_url())

    assert response.status_code == 200
    content = response_text(response)
    assert "<title>Django weekly update · Awesome</title>" in content
    assert (
        '<meta name="description" content="Read the django/django weekly development update '
        'for 2026-05-25 to 2026-05-31, summarizing 3 commits." />' in content
    )
    assert (
        '<link rel="canonical" '
        'href="https://testserver/repos/django/django/updates/weekly/2026-05-25/" />' in content
    )
    assert '"@type": "Article"' in content
    assert '"about": {' in content


@override_settings(SITE_URL="https://awesome.example")
def test_robots_txt_allows_crawling_and_advertises_sitemap(client):
    response = client.get("/robots.txt")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/plain")
    assert response_text(response) == (
        "User-agent: *\nAllow: /\nSitemap: https://awesome.example/sitemap.xml\n"
    )


@override_settings(
    SITE_URL="https://awesome.example",
    ALLOWED_HOSTS=["awesome.example", "testserver"],
)
def test_sitemap_index_links_paginated_sections(client):
    repository = Repository.objects.create(
        full_name="django/django",
        owner="django",
        name="django",
        url="https://github.com/django/django",
        description="The Web framework for perfectionists with deadlines.",
    )
    Repository.objects.create(
        full_name="django/channels",
        owner="django",
        name="channels",
        url="https://github.com/django/channels",
        description="Archived Django Channels repository.",
        is_archived=True,
    )
    archived_repository = Repository.objects.get(full_name="django/channels")
    disabled_repository = Repository.objects.create(
        full_name="django/disabled",
        owner="django",
        name="disabled",
        url="https://github.com/django/disabled",
        description="Disabled Django repository.",
        is_disabled=True,
    )
    AwesomeList.objects.create(
        name="Awesome Django",
        slug="awesome-django",
        source_url="https://github.com/wsvincent/awesome-django",
        description="Curated Django packages and resources.",
    )
    issue = RepositoryNewsletterIssue.objects.create(
        repository=repository,
        cadence=NewsletterCadence.WEEKLY,
        period_start=date(2026, 5, 25),
        period_end=date(2026, 5, 31),
        slug="2026-05-25",
        title="Django weekly update",
        content_markdown="## Changes\n- Added tracking.",
        content_html="<h2>Changes</h2><ul><li>Added tracking.</li></ul>",
        commit_count=3,
        published_at=timezone.now() - timedelta(days=1),
    )
    archived_issue = RepositoryNewsletterIssue.objects.create(
        repository=archived_repository,
        cadence=NewsletterCadence.WEEKLY,
        period_start=date(2026, 5, 25),
        period_end=date(2026, 5, 31),
        slug="2026-05-25",
        title="Archived weekly update",
        content_markdown="## Changes\n- Hidden.",
        content_html="<h2>Changes</h2><ul><li>Hidden.</li></ul>",
        commit_count=1,
        published_at=timezone.now(),
    )
    RepositoryNewsletterIssue.objects.create(
        repository=disabled_repository,
        cadence=NewsletterCadence.WEEKLY,
        period_start=date(2026, 5, 25),
        period_end=date(2026, 5, 31),
        slug="2026-05-25",
        title="Disabled weekly update",
        content_markdown="## Changes\n- Hidden.",
        content_html="<h2>Changes</h2><ul><li>Hidden.</li></ul>",
        commit_count=1,
        published_at=timezone.now(),
    )

    response = client.get("/sitemap.xml", headers={"host": "awesome.example"})

    assert response.status_code == 200
    content = response_text(response)
    assert "<sitemapindex" in content
    assert "<loc>https://awesome.example/sitemap-static.xml</loc>" in content
    assert "<loc>https://awesome.example/sitemap-repositories.xml</loc>" in content
    assert "<loc>https://awesome.example/sitemap-awesome_lists.xml</loc>" in content
    assert "<loc>https://awesome.example/repos/django/django/</loc>" not in content

    static_content = response_text(client.get("/sitemap-static.xml"))
    repository_content = response_text(client.get("/sitemap-repositories.xml"))
    list_content = response_text(client.get("/sitemap-awesome_lists.xml"))
    updates_content = response_text(client.get("/sitemap-repository_updates.xml"))
    issues_content = response_text(client.get("/sitemap-repository_update_issues.xml"))

    assert "<loc>https://awesome.example/</loc>" in static_content
    assert "<loc>https://awesome.example/updates/</loc>" in static_content
    assert "<loc>https://awesome.example/lists/</loc>" in static_content
    assert "<loc>https://awesome.example/repos/django/django/</loc>" in repository_content
    assert "<loc>https://awesome.example/repos/django/channels/</loc>" not in repository_content
    assert "<loc>https://awesome.example/repos/django/disabled/</loc>" not in repository_content
    assert "<loc>https://awesome.example/lists/awesome-django/</loc>" in list_content
    assert "<loc>https://awesome.example/repos/django/django/updates/</loc>" in updates_content
    assert f"<loc>https://awesome.example{issue.get_absolute_url()}</loc>" in issues_content
    assert (
        "<loc>https://awesome.example/repos/django/channels/updates/</loc>" not in updates_content
    )
    assert (
        f"<loc>https://awesome.example{archived_issue.get_absolute_url()}</loc>"
        not in issues_content
    )
    assert (
        "<loc>https://awesome.example/repos/django/disabled/updates/</loc>" not in updates_content
    )
    assert RepositoryNewsletterIssueSitemap().lastmod(issue) == issue.updated_at
