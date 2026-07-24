import re
from datetime import datetime, timedelta
from html.parser import HTMLParser

import pytest
from allauth.socialaccount.models import SocialAccount, SocialToken
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.core.admin_dashboard import repository_monitoring_context
from apps.core.views import build_absolute_public_url
from apps.repos.models import (
    AwesomeList,
    Repository,
    RepositorySnapshot,
    UserStarredRepository,
)


class TableRowsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self._current_row = None
        self._current_cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._current_row = []
        elif tag in {"td", "th"} and self._current_row is not None:
            self._current_cell = []

    def handle_data(self, data):
        if self._current_cell is not None:
            self._current_cell.append(data)

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self._current_cell is not None:
            cell_text = " ".join(" ".join(self._current_cell).split())
            self._current_row.append(cell_text)
            self._current_cell = None
        elif tag == "tr" and self._current_row is not None:
            self.rows.append(self._current_row)
            self._current_row = None


def table_row_for_text(content, text):
    parser = TableRowsParser()
    parser.feed(content)
    return next(row for row in parser.rows if text in row)


@pytest.mark.django_db
class TestHomeView:
    def test_home_view_status_code(self, auth_client):
        url = reverse("home")
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_home_view_uses_correct_template(self, auth_client):
        url = reverse("home")
        response = auth_client.get(url)
        assert "pages/home.html" in [t.name for t in response.templates]

    def test_github_starred_import_defaults_off(self, profile):
        assert profile.github_starred_repos_import_enabled is False

    def test_settings_shows_clear_import_cta_when_github_connected_and_import_off(
        self,
        auth_client,
        profile,
    ):
        account = SocialAccount.objects.create(
            user=profile.user,
            provider="github",
            uid="github-user",
        )
        SocialToken.objects.create(account=account, token="user-token")

        response = auth_client.get(reverse("settings"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "Import starred repos" in content
        assert "Manual import" in content
        assert "Starts when you import" in content
        assert "Daily refresh enabled" not in content

    def test_settings_does_not_show_github_account_without_token(
        self,
        auth_client,
        profile,
    ):
        SocialAccount.objects.create(
            user=profile.user,
            provider="github",
            uid="github-user",
            extra_data={"login": "missing-token"},
        )

        response = auth_client.get(reverse("settings"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "Not connected" in content
        assert "@missing-token" not in content
        assert "Import starred repos" not in content

    def test_settings_does_not_show_expired_github_token_as_connected(
        self,
        auth_client,
        profile,
    ):
        account = SocialAccount.objects.create(
            user=profile.user,
            provider="github",
            uid="github-user",
            extra_data={"login": "expired-token"},
        )
        SocialToken.objects.create(
            account=account,
            token="expired-token",
            expires_at=timezone.now() - timedelta(days=1),
        )

        response = auth_client.get(reverse("settings"))
        content = response.content.decode()

        assert response.status_code == 200
        assert "Not connected" in content
        assert "@expired-token" not in content
        assert "Import starred repos" not in content

    def test_import_starred_repositories_enables_profile_and_queues_task(
        self,
        auth_client,
        profile,
        monkeypatch,
    ):
        account = SocialAccount.objects.create(
            user=profile.user,
            provider="github",
            uid="github-user",
        )
        SocialToken.objects.create(account=account, token="user-token")
        queued = []

        def fake_async_task(func_path, profile_id, **kwargs):
            queued.append((func_path, profile_id, kwargs))

        monkeypatch.setattr("apps.core.views.async_task", fake_async_task)
        monkeypatch.setattr("apps.core.views.transaction.on_commit", lambda callback: callback())

        response = auth_client.post(reverse("import_starred_repositories"), follow=True)

        profile.refresh_from_db()
        assert response.status_code == 200
        assert profile.github_starred_repos_import_enabled is True
        assert profile.github_starred_repos_last_error == ""
        assert queued == [
            (
                "apps.repos.tasks.import_starred_repositories_task",
                profile.id,
                {
                    "refresh_existing": True,
                    "group": "Import GitHub starred repositories",
                },
            )
        ]
        assert (
            "Enabled daily GitHub starred repository refresh and queued your first import."
            in response.content.decode()
        )

    def test_import_starred_repositories_shows_refresh_message_when_already_enabled(
        self,
        auth_client,
        profile,
        monkeypatch,
    ):
        account = SocialAccount.objects.create(
            user=profile.user,
            provider="github",
            uid="github-user",
        )
        SocialToken.objects.create(account=account, token="user-token")
        profile.github_starred_repos_import_enabled = True
        profile.save(update_fields=["github_starred_repos_import_enabled", "updated_at"])
        queued = []

        def fake_async_task(func_path, profile_id, **kwargs):
            queued.append((func_path, profile_id, kwargs))

        monkeypatch.setattr("apps.core.views.async_task", fake_async_task)
        monkeypatch.setattr("apps.core.views.transaction.on_commit", lambda callback: callback())

        response = auth_client.post(reverse("import_starred_repositories"), follow=True)

        profile.refresh_from_db()
        assert response.status_code == 200
        assert profile.github_starred_repos_import_enabled is True
        assert queued == [
            (
                "apps.repos.tasks.import_starred_repositories_task",
                profile.id,
                {
                    "refresh_existing": True,
                    "group": "Import GitHub starred repositories",
                },
            )
        ]
        content = response.content.decode()
        assert "Queued your GitHub starred repository refresh." in content
        assert "queued your first import" not in content

    def test_disable_starred_repositories_import_turns_off_daily_refresh(
        self,
        auth_client,
        profile,
    ):
        profile.github_starred_repos_import_enabled = True
        profile.github_starred_repos_last_error = "Previous sync error"
        profile.save(
            update_fields=[
                "github_starred_repos_import_enabled",
                "github_starred_repos_last_error",
                "updated_at",
            ]
        )

        response = auth_client.post(reverse("disable_starred_repository_import"), follow=True)

        profile.refresh_from_db()
        assert response.status_code == 200
        assert profile.github_starred_repos_import_enabled is False
        assert profile.github_starred_repos_last_error == ""
        assert "Disabled daily GitHub starred repository refresh." in response.content.decode()


@pytest.mark.django_db
def test_admin_panel_can_add_awesome_list_and_queue_scan(
    client,
    monkeypatch,
    sync_state_transitions,
):
    user = get_user_model().objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password123",
    )
    client.force_login(user)

    queued = []

    def fake_async_task(func_path, awesome_list_id, **kwargs):
        queued.append((func_path, awesome_list_id, kwargs))

    monkeypatch.setattr("apps.core.views.async_task", fake_async_task)
    monkeypatch.setattr("apps.core.views.transaction.on_commit", lambda callback: callback())

    response = client.post(
        reverse("admin_panel"),
        data={
            "source_url": "https://github.com/wsvincent/awesome-django",
        },
        follow=True,
    )

    assert response.status_code == 200
    awesome_list = AwesomeList.objects.get(source_url="https://github.com/wsvincent/awesome-django")
    assert awesome_list.name == "Awesome Django"
    assert queued == [
        (
            "apps.repos.tasks.sync_awesome_list_task",
            awesome_list.id,
            {"group": "Scan awesome list"},
        )
    ]
    assert "Added Awesome Django and queued a scan." in response.content.decode()


@pytest.mark.django_db
def test_admin_panel_can_retry_awesome_list_scan(
    client,
    monkeypatch,
    sync_state_transitions,
):
    user = get_user_model().objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password123",
    )
    client.force_login(user)
    awesome_list = AwesomeList.objects.create(
        name="Awesome Django",
        slug="awesome-django",
        source_url="https://github.com/wsvincent/awesome-django",
        repo_full_name="wsvincent/awesome-django",
        last_error="Previous scan failed.",
    )
    queued = []

    def fake_async_task(func_path, awesome_list_id, **kwargs):
        queued.append((func_path, awesome_list_id, kwargs))

    monkeypatch.setattr("apps.core.views.async_task", fake_async_task)
    monkeypatch.setattr("apps.core.views.transaction.on_commit", lambda callback: callback())

    response = client.post(
        reverse("admin_panel"),
        data={
            "action": "retry_awesome_list",
            "awesome_list_id": awesome_list.id,
        },
        follow=True,
    )

    assert response.status_code == 200
    assert queued == [
        (
            "apps.repos.tasks.sync_awesome_list_task",
            awesome_list.id,
            {"group": "Scan awesome list"},
        )
    ]
    assert "Queued a retry scan for Awesome Django." in response.content.decode()


@pytest.mark.django_db
def test_admin_panel_shows_github_rate_limit_card(client, monkeypatch, sync_state_transitions):
    user = get_user_model().objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password123",
    )
    client.force_login(user)
    monkeypatch.setattr(
        "apps.core.views.github_rate_limit_status",
        lambda: {
            "ok": True,
            "token_configured": True,
            "core": {
                "limit": 5000,
                "used": 125,
                "remaining": 4875,
                "reset_at": None,
            },
            "error": "",
        },
    )

    response = client.get(reverse("admin_panel"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "GitHub API status" in content
    assert "4875" in content
    assert "5000" in content


@pytest.mark.django_db
def test_admin_panel_shows_profile_starred_repo_counts_and_import_status(
    client,
    django_user_model,
    monkeypatch,
    sync_state_transitions,
):
    admin = get_user_model().objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password123",
    )
    enabled_user = django_user_model.objects.create_user(
        username="enabled",
        email="enabled@example.com",
        password="password123",
    )
    django_user_model.objects.create_user(
        username="disabled",
        email="disabled@example.com",
        password="password123",
    )
    enabled_user.profile.github_starred_repos_import_enabled = True
    enabled_user.profile.save(update_fields=["github_starred_repos_import_enabled", "updated_at"])
    first_repo = Repository.objects.create(
        full_name="django/django",
        owner="django",
        name="django",
        url="https://github.com/django/django",
    )
    second_repo = Repository.objects.create(
        full_name="encode/django-rest-framework",
        owner="encode",
        name="django-rest-framework",
        url="https://github.com/encode/django-rest-framework",
    )
    UserStarredRepository.objects.create(profile=enabled_user.profile, repository=first_repo)
    UserStarredRepository.objects.create(profile=enabled_user.profile, repository=second_repo)
    monkeypatch.setattr(
        "apps.core.views.github_rate_limit_status",
        lambda: {
            "ok": False,
            "error": "",
        },
    )
    client.force_login(admin)

    response = client.get(reverse("admin_panel"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Starred repos" in content
    assert "Starred import" in content
    enabled_row = table_row_for_text(content, "enabled@example.com")
    disabled_row = table_row_for_text(content, "disabled@example.com")
    assert enabled_row[:4] == ["enabled@example.com", "enabled", "2", "Enabled"]
    assert disabled_row[:4] == ["disabled@example.com", "disabled", "0", "Disabled"]


@pytest.mark.django_db
def test_admin_panel_bounds_recent_awesome_lists_height(
    client,
    monkeypatch,
    sync_state_transitions,
):
    user = get_user_model().objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password123",
    )
    client.force_login(user)
    for index in range(3):
        AwesomeList.objects.create(
            name=f"Awesome List {index}",
            slug=f"awesome-list-{index}",
            source_url=f"https://github.com/example/awesome-list-{index}",
            repo_full_name=f"example/awesome-list-{index}",
        )
    monkeypatch.setattr(
        "apps.core.views.github_rate_limit_status",
        lambda: {
            "ok": False,
            "error": "",
        },
    )

    response = client.get(reverse("admin_panel"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Recent awesome lists" in content
    assert "max-h-96 space-y-4 overflow-y-auto pr-2" in content


@pytest.mark.django_db
def test_admin_panel_nav_links_to_repository_and_list_pages(
    client,
    monkeypatch,
    sync_state_transitions,
):
    user = get_user_model().objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password123",
    )
    client.force_login(user)
    monkeypatch.setattr(
        "apps.core.views.github_rate_limit_status",
        lambda: {
            "ok": False,
            "error": "",
        },
    )

    response = client.get(reverse("admin_panel"))
    content = response.content.decode()

    assert response.status_code == 200
    repos_link = rf'<a href="{re.escape(reverse("repos:search"))}"[^>]*>\s*Repos\s*</a>'
    lists_link = rf'<a href="{re.escape(reverse("repos:list"))}"[^>]*>\s*Lists\s*</a>'
    settings_link = rf'<a href="{re.escape(reverse("settings"))}"[^>]*>\s*Settings\s*</a>'
    assert re.search(repos_link, content)
    assert re.search(lists_link, content)
    assert re.search(settings_link, content)
    assert not re.search(r"<a\b[^>]*>\s*Dashboard\s*</a>", content)
    assert not re.search(r"<a\b[^>]*>\s*Request list\s*</a>", content)


@pytest.mark.django_db
def test_admin_panel_shows_repository_analysis_health(
    client,
    monkeypatch,
    sync_state_transitions,
):
    admin = get_user_model().objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password123",
    )
    client.force_login(admin)
    monkeypatch.setattr(
        "apps.core.views.github_rate_limit_status",
        lambda: {
            "ok": False,
            "error": "",
        },
    )
    now = timezone.now()

    low_star_repo = Repository.objects.create(
        full_name="example/new-low-star-repo",
        owner="example",
        name="new-low-star-repo",
        url="https://github.com/example/new-low-star-repo",
        stars=40,
        language="Python",
    )
    medium_star_repo = Repository.objects.create(
        full_name="example/medium-star-repo",
        owner="example",
        name="medium-star-repo",
        url="https://github.com/example/medium-star-repo",
        stars=400,
    )
    high_star_repo = Repository.objects.create(
        full_name="example/high-star-repo",
        owner="example",
        name="high-star-repo",
        url="https://github.com/example/high-star-repo",
        stars=40_000,
    )
    stale_repo = Repository.objects.create(
        full_name="example/stale-repo",
        owner="example",
        name="stale-repo",
        url="https://github.com/example/stale-repo",
        stars=4_000,
    )
    Repository.objects.filter(pk=low_star_repo.pk).update(created_at=now - timedelta(hours=1))
    Repository.objects.filter(pk=medium_star_repo.pk).update(created_at=now - timedelta(days=3))
    Repository.objects.filter(pk=high_star_repo.pk).update(created_at=now - timedelta(days=20))
    Repository.objects.filter(pk=stale_repo.pk).update(created_at=now - timedelta(days=40))

    for captured_at in (now - timedelta(hours=12), now - timedelta(hours=6)):
        RepositorySnapshot.objects.create(
            repository=low_star_repo,
            captured_at=captured_at,
            stars=low_star_repo.stars,
        )
    RepositorySnapshot.objects.create(
        repository=medium_star_repo,
        captured_at=now - timedelta(days=3),
        stars=medium_star_repo.stars,
    )
    RepositorySnapshot.objects.create(
        repository=high_star_repo,
        captured_at=now - timedelta(days=20),
        stars=high_star_repo.stars,
    )
    RepositorySnapshot.objects.create(
        repository=stale_repo,
        captured_at=now - timedelta(days=40),
        stars=stale_repo.stars,
    )

    response = client.get(reverse("admin_panel"))
    content = response.content.decode()

    assert response.status_code == 200
    assert response.context["repositories_analyzed"]["day"] == 1
    assert response.context["repositories_analyzed"]["week"] == 2
    assert response.context["repositories_analyzed"]["month"] == 3
    assert response.context["analysis_runs_month"] == 4
    assert response.context["analysis_coverage_month"] == 75
    assert len(response.context["analysis_activity"]) == 30

    low_star_band = next(
        band for band in response.context["analysis_distribution"] if band["label"] == "0–99"
    )
    assert low_star_band["repository_count"] == 1
    assert low_star_band["analyzed_repository_count"] == 1
    assert low_star_band["analysis_run_count"] == 2
    assert low_star_band["coverage_percent"] == 100

    assert "Repository analysis" in content
    assert "30-day analysis activity" in content
    assert "Analysis distribution by stars" in content
    assert "Recently added repositories" in content
    recent_repo_row = table_row_for_text(content, "example/new-low-star-repo")
    assert recent_repo_row[:3] == ["example/new-low-star-repo", "Python", "40"]
    assert 'hx-select="#admin-monitoring"' in content


@pytest.mark.django_db
def test_admin_panel_marks_missing_star_band_coverage(
    client,
    monkeypatch,
    sync_state_transitions,
):
    admin = get_user_model().objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password123",
    )
    client.force_login(admin)
    monkeypatch.setattr(
        "apps.core.views.github_rate_limit_status",
        lambda: {
            "ok": False,
            "error": "",
        },
    )
    low_star_repo = Repository.objects.create(
        full_name="example/low-star-repo",
        owner="example",
        name="low-star-repo",
        url="https://github.com/example/low-star-repo",
        stars=20,
    )
    high_star_repo = Repository.objects.create(
        full_name="example/popular-repo",
        owner="example",
        name="popular-repo",
        url="https://github.com/example/popular-repo",
        stars=80_000,
    )
    RepositorySnapshot.objects.create(
        repository=high_star_repo,
        captured_at=timezone.now() - timedelta(days=1),
        stars=high_star_repo.stars,
    )

    response = client.get(reverse("admin_panel"))

    assert response.status_code == 200
    assert response.context["analysis_distribution_status"] == "Coverage gaps"
    assert response.context["analysis_distribution_status_tone"] == "warning"
    assert response.context["analysis_distribution_gap_count"] == 1
    low_star_band = next(
        band for band in response.context["analysis_distribution"] if band["label"] == "0–99"
    )
    assert low_star_band["repository_count"] == 1
    assert low_star_band["analysis_run_count"] == 0
    assert low_star_repo.full_name in response.content.decode()


@pytest.mark.django_db
def test_repository_monitoring_chart_matches_30_day_total():
    current_tz = timezone.get_current_timezone()
    now = timezone.make_aware(datetime(2026, 7, 24, 12), current_tz)
    first_day_start = timezone.make_aware(datetime(2026, 6, 25), current_tz)
    repository = Repository.objects.create(
        full_name="example/window-boundary",
        owner="example",
        name="window-boundary",
        url="https://github.com/example/window-boundary",
        stars=10,
    )
    RepositorySnapshot.objects.create(
        repository=repository,
        captured_at=first_day_start,
        stars=repository.stars,
    )
    RepositorySnapshot.objects.create(
        repository=repository,
        captured_at=first_day_start - timedelta(seconds=1),
        stars=repository.stars,
    )

    context = repository_monitoring_context(now=now)

    assert len(context["analysis_activity"]) == 30
    assert context["analysis_runs_month"] == 1
    assert sum(day["run_count"] for day in context["analysis_activity"]) == 1


@override_settings(SITE_URL="http://example.com")
def test_build_absolute_public_url_upgrades_non_local_http():
    assert build_absolute_public_url("/api/user") == "https://example.com/api/user"


@override_settings(SITE_URL="http://notlocalhost.example")
def test_build_absolute_public_url_does_not_treat_hostname_substrings_as_local():
    assert build_absolute_public_url("/api/user") == "https://notlocalhost.example/api/user"


@override_settings(SITE_URL="http://localhost:8000")
def test_build_absolute_public_url_preserves_localhost_http():
    assert build_absolute_public_url("/api/user") == "http://localhost:8000/api/user"
