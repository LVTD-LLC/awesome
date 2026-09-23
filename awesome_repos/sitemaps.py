from types import SimpleNamespace
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib import sitemaps
from django.db.models import Max, Q
from django.template.response import TemplateResponse
from django.urls import reverse

from apps.blog.services import list_blog_posts
from apps.repos.models import AwesomeList, Repository, RepositoryNewsletterIssue


class ConfiguredDomainSitemap(sitemaps.Sitemap):
    protocol = "https"
    # Keep individual XML documents quick to generate and download. The sitemap
    # index advertises every page, so crawlers still discover the full catalog.
    limit = 2_000

    def get_latest_lastmod(self):
        # Django's default implementation materializes every item in a section.
        # That makes the lightweight sitemap index as expensive as rendering the
        # full catalog. Section documents still expose per-URL lastmod values.
        return None

    def get_urls(self, page=1, site=None, protocol=None):
        parsed_site_url = urlsplit(settings.SITE_URL)
        configured_site = SimpleNamespace(domain=parsed_site_url.netloc)
        configured_protocol = parsed_site_url.scheme or protocol or self.protocol
        return super().get_urls(
            page=page,
            site=configured_site,
            protocol=configured_protocol,
        )


def configured_sitemap_index(request, sitemaps, sitemap_url_name):
    """Render a sitemap index using SITE_URL instead of the django_site row."""
    base_url = settings.SITE_URL.rstrip("/")
    sitemap_entries = []

    for section, sitemap_class in sitemaps.items():
        sitemap_instance = sitemap_class() if callable(sitemap_class) else sitemap_class
        section_path = reverse(sitemap_url_name, kwargs={"section": section})
        section_url = f"{base_url}{section_path}"

        for page in range(1, sitemap_instance.paginator.num_pages + 1):
            page_suffix = f"?p={page}" if page > 1 else ""
            sitemap_entries.append(
                SimpleNamespace(
                    location=f"{section_url}{page_suffix}",
                    last_mod=None,
                )
            )

    response = TemplateResponse(
        request,
        "sitemap_index.xml",
        {"sitemaps": sitemap_entries},
        content_type="application/xml",
    )
    response.headers["X-Robots-Tag"] = "noindex, noodp, noarchive"
    return response


class StaticViewSitemap(ConfiguredDomainSitemap):
    """Generate a sitemap for public static and index pages."""

    priority = 0.9
    changefreq = "daily"

    def items(self):
        return [
            "landing",
            "repos:search",
            "repos:updates_index",
            "repos:list",
            "repos:request_list",
            "blog:post_list",
            "uses",
            "privacy_policy",
            "terms_of_service",
        ]

    def location(self, item):
        return reverse(item)


class RepositorySitemap(ConfiguredDomainSitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        active_list_source_repositories = (
            AwesomeList.objects.filter(is_active=True)
            .exclude(repo_full_name="")
            .values("repo_full_name")
        )
        return (
            Repository.objects.filter(is_archived=False, is_disabled=False)
            .exclude(is_awesome_list_candidate=True)
            .exclude(full_name__in=active_list_source_repositories)
            .only(
                "id",
                "owner",
                "name",
                "github_pushed_at",
                "last_synced_at",
                "updated_at",
            )
            .order_by("id")
        )

    def lastmod(self, item):
        return item.github_pushed_at or item.last_synced_at or item.updated_at


class AwesomeListSitemap(ConfiguredDomainSitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return (
            AwesomeList.objects.filter(is_active=True)
            .only(
                "id",
                "slug",
                "last_scanned_at",
                "github_pushed_at",
                "updated_at",
            )
            .order_by("id")
        )

    def lastmod(self, item):
        return item.last_scanned_at or item.github_pushed_at or item.updated_at


class BlogPostSitemap(ConfiguredDomainSitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return list_blog_posts()

    def lastmod(self, item):
        return item.updated_at


class RepositoryUpdatesSitemap(ConfiguredDomainSitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        published_issues = Q(newsletter_issues__published_at__isnull=False)
        return (
            Repository.objects.filter(published_issues, is_archived=False, is_disabled=False)
            .exclude(is_awesome_list_candidate=True)
            .annotate(
                latest_update_published_at=Max(
                    "newsletter_issues__published_at",
                    filter=published_issues,
                ),
                latest_update_modified_at=Max(
                    "newsletter_issues__updated_at",
                    filter=published_issues,
                ),
            )
            .only("id", "owner", "name", "updated_at")
            .order_by("id")
        )

    def location(self, item):
        return reverse(
            "repos:newsletter_issue_list",
            kwargs={"owner": item.owner, "name": item.name},
        )

    def lastmod(self, item):
        return max(
            (
                value
                for value in (
                    item.latest_update_published_at,
                    item.latest_update_modified_at,
                )
                if value is not None
            ),
            default=item.updated_at,
        )


class RepositoryNewsletterIssueSitemap(ConfiguredDomainSitemap):
    changefreq = "monthly"
    priority = 0.55

    def items(self):
        return (
            RepositoryNewsletterIssue.objects.filter(
                published_at__isnull=False,
                repository__is_archived=False,
                repository__is_disabled=False,
                repository__is_awesome_list_candidate=False,
            )
            .select_related("repository")
            .only(
                "id",
                "slug",
                "cadence",
                "published_at",
                "updated_at",
                "repository__id",
                "repository__owner",
                "repository__name",
            )
            .order_by("id")
        )

    def lastmod(self, item):
        return max(item.published_at, item.updated_at)


sitemaps = {
    "static": StaticViewSitemap,
    "repositories": RepositorySitemap,
    "awesome_lists": AwesomeListSitemap,
    "blog_posts": BlogPostSitemap,
    "repository_updates": RepositoryUpdatesSitemap,
    "repository_update_issues": RepositoryNewsletterIssueSitemap,
}
