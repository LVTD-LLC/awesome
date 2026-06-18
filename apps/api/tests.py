import json
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from django.http import HttpRequest
from django.test import SimpleTestCase
from django.utils import timezone

from apps.repos.models import AwesomeList, AwesomeListItem, Repository, RepositorySnapshot


class PlaceholderApiTests(SimpleTestCase):
    def test_placeholder(self):
        assert True


class UserInfoApiUnitTests(SimpleTestCase):
    def test_get_user_info_returns_safe_profile_data(self):
        from apps.api.views import get_user_info

        user = SimpleNamespace(
            id=7,
            email="ada@example.com",
            username="ada",
            first_name="Ada",
            last_name="Lovelace",
            date_joined="2026-05-14T00:00:00Z",
            get_full_name=lambda: "Ada Lovelace",
        )
        profile = SimpleNamespace(
            id=11,
            user=user,
            state="signed_up",
        )
        request = HttpRequest()
        request.auth = profile

        response = get_user_info(request)

        assert response["email"] == "ada@example.com"
        assert response["full_name"] == "Ada Lovelace"
        assert response["profile"] == {
            "id": 11,
            "state": "signed_up",
            "has_active_subscription": False,
        }
        assert "key" not in response


def test_openapi_schema_advertises_catalog_endpoints_without_refresh_actions():
    from apps.api.views import api

    paths = api.get_openapi_schema()["paths"]

    assert "/api/repositories" in paths
    assert "/api/repositories/{owner}/{name}" in paths
    assert "/api/awesome-lists" in paths
    assert "/api/awesome-lists/{slug}" in paths
    assert "/api/awesome-lists/{slug}/repositories" in paths
    assert "/api/awesome-lists/{slug}/repository-options" in paths
    assert "get" in paths["/api/awesome-lists"]
    assert "post" not in paths["/api/awesome-lists"]
    assert not any("rescan" in path for path in paths)
    assert not any("discover-missing" in path for path in paths)
    assert not any(path.startswith("/api/blog") for path in paths)


def test_api_key_auth_returns_profile_for_valid_key():
    from apps.api.auth import APIKeyHeaderAuth, BearerAPIKeyAuth
    from apps.core.models import Profile

    api_key = "ak_public.secret"

    for auth_class in [APIKeyHeaderAuth, BearerAPIKeyAuth]:
        profile = SimpleNamespace(id=11, check_api_key=Mock(return_value=True))
        with patch("apps.core.api_keys.Profile.objects") as objects:
            objects.select_related.return_value.get.return_value = profile
            response = auth_class().authenticate(HttpRequest(), api_key)

        assert response is profile
        objects.select_related.assert_called_once_with("user")
        objects.select_related.return_value.get.assert_called_once_with(api_key_prefix="ak_public")
        profile.check_api_key.assert_called_once_with(api_key)

    with patch("apps.core.api_keys.Profile.objects") as objects:
        objects.select_related.return_value.get.side_effect = Profile.DoesNotExist
        response = APIKeyHeaderAuth().authenticate(HttpRequest(), "ak_missing.secret")

    assert response is None

    with patch("apps.core.api_keys.Profile.objects") as objects:
        response = APIKeyHeaderAuth().authenticate(HttpRequest(), "bad-key")

    assert response is None
    objects.select_related.assert_not_called()


def _api_key_header(profile):
    return {"HTTP_X_API_KEY": profile.rotate_api_key()}


@pytest.mark.django_db
def test_repository_search_api_uses_existing_filters(client, profile):
    awesome_list = AwesomeList.objects.create(
        name="Awesome Django",
        slug="awesome-django",
        source_url="https://github.com/wsvincent/awesome-django",
        repo_full_name="wsvincent/awesome-django",
        stars=1200,
        first_commit_at=timezone.now() - timedelta(days=365 * 12),
    )
    django_repo = Repository.objects.create(
        full_name="django/django",
        owner="django",
        name="django",
        url="https://github.com/django/django",
        description="Python web framework",
        language="Python",
        stars=90000,
        commit_count=150,
        first_commit_at=timezone.now() - timedelta(days=365 * 12),
        github_pushed_at=timezone.now() - timedelta(days=400),
        topics=["django", "web"],
        generated_tags=["web-framework"],
        detected_stacks=["django"],
        package_managers=["poetry"],
        uses_ai_for_development=True,
        ai_development_signals=[
            {
                "path": "AGENTS.md",
                "kind": "file",
                "tool": "Agent instructions",
                "signal": "agent_instructions",
            }
        ],
        dependency_ecosystems=["python"],
        stack_signals=[
            {
                "slug": "django",
                "label": "Django",
                "category": "web framework",
                "confidence": "high",
                "evidence": [{"path": "pyproject.toml", "dependency": "django"}],
            }
        ],
    )
    RepositorySnapshot.objects.create(
        repository=django_repo,
        captured_at=timezone.now() - timedelta(days=6),
        stars=60000,
        commit_count=100,
    )
    RepositorySnapshot.objects.create(
        repository=django_repo,
        captured_at=timezone.now() - timedelta(days=1),
        stars=88000,
        commit_count=140,
    )
    Repository.objects.create(
        full_name="expressjs/express",
        owner="expressjs",
        name="express",
        url="https://github.com/expressjs/express",
        description="Node web framework",
        language="JavaScript",
        stars=65000,
        topics=["node", "web"],
    )
    AwesomeListItem.objects.create(awesome_list=awesome_list, repository=django_repo)

    response = client.get(
        "/api/repositories",
        {
            "q": "framework",
            "language": "Python",
            "min_stars": "100",
            "min_age_years": "10",
            "min_velocity_percent": "40",
            "min_star_growth_percent": "40",
            "unmaintained_days": "365",
            "topic": "django",
            "framework": "django",
            "package_manager": "poetry",
            "has_file": ["AGENTS.md"],
            "sort": "stars",
            "sort_direction": "desc",
        },
        **_api_key_header(profile),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"]["count"] == 1
    assert payload["results"][0]["full_name"] == "django/django"
    assert payload["results"][0]["first_commit_at"] is not None
    assert payload["results"][0]["detected_stacks"] == ["django"]
    assert payload["results"][0]["package_managers"] == ["poetry"]
    assert payload["results"][0]["stack_signals"][0]["label"] == "Django"
    assert payload["results"][0]["awesome_count"] == 1
    assert payload["results"][0]["awesome_lists"][0]["slug"] == "awesome-django"
    assert payload["results"][0]["stars_since_recent"] == 30000
    assert payload["results"][0]["commits_since_recent"] == 50
    assert payload["results"][0]["stars_growth_percent"] == 50
    assert payload["results"][0]["commits_growth_percent"] == 50


@pytest.mark.django_db
def test_repository_detail_api_includes_history(client, profile):
    repository = Repository.objects.create(
        full_name="django/django",
        owner="django",
        name="django",
        url="https://github.com/django/django",
        description="Python web framework",
        language="Python",
        stars=90000,
        forks=32000,
        watchers=500,
        commit_count=100,
        readme="# Django",
        ai_development_signals=[{"tool": "Codex", "path": "AGENTS.md"}],
        uses_ai_for_development=True,
        dependency_files=[{"path": "pyproject.toml", "dependency_count": 1}],
        detected_stacks=["django"],
        package_managers=["poetry"],
        stack_signals=[{"slug": "django", "label": "Django"}],
    )
    RepositorySnapshot.objects.create(
        repository=repository,
        captured_at=timezone.now() - timedelta(days=2),
        stars=89900,
        forks=31900,
        watchers=490,
        commit_count=95,
    )
    RepositorySnapshot.objects.create(
        repository=repository,
        captured_at=timezone.now() - timedelta(days=1),
        stars=90000,
        forks=32000,
        watchers=500,
        commit_count=100,
    )

    response = client.get(
        "/api/repositories/django/django",
        **_api_key_header(profile),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["full_name"] == "django/django"
    assert payload["readme"] == "# Django"
    assert payload["performance"]["has_history"] is True
    assert payload["performance"]["stars_since_first"] == 100
    assert [point["stars"] for point in payload["history"]] == [89900, 90000]
    assert payload["ai_development_signals"] == [{"tool": "Codex", "path": "AGENTS.md"}]
    assert payload["dependency_files"] == [{"path": "pyproject.toml", "dependency_count": 1}]
    assert payload["detected_stacks"] == ["django"]


@pytest.mark.django_db
def test_awesome_list_api_search_detail_and_repository_filters(client, profile):
    awesome_list = AwesomeList.objects.create(
        name="Awesome Django",
        slug="awesome-django",
        source_url="https://github.com/wsvincent/awesome-django",
        repo_full_name="wsvincent/awesome-django",
        description="Curated Django resources",
        topics=["django", "awesome-list"],
        stars=1200,
        readme_repository_count=20,
        first_commit_at=timezone.now() - timedelta(days=365 * 12),
        last_scanned_at=timezone.now(),
    )
    AwesomeList.objects.create(
        name="Inactive List",
        slug="inactive-list",
        source_url="https://github.com/example/inactive-list",
        is_active=False,
    )
    django_repo = Repository.objects.create(
        full_name="django/django",
        owner="django",
        name="django",
        url="https://github.com/django/django",
        description="Python web framework",
        language="Python",
        stars=90000,
        forks=32000,
        first_commit_at=timezone.now() - timedelta(days=365 * 12),
        detected_stacks=["django"],
        package_managers=["poetry"],
    )
    node_repo = Repository.objects.create(
        full_name="expressjs/express",
        owner="expressjs",
        name="express",
        url="https://github.com/expressjs/express",
        description="Node web framework",
        language="JavaScript",
        stars=65000,
        forks=12000,
        first_commit_at=timezone.now() - timedelta(days=365 * 2),
    )
    AwesomeListItem.objects.create(awesome_list=awesome_list, repository=django_repo)
    AwesomeListItem.objects.create(awesome_list=awesome_list, repository=node_repo)

    search_response = client.get(
        "/api/awesome-lists",
        {"q": "django", "min_age_years": "10", "sort": "oldest"},
        **_api_key_header(profile),
    )

    assert search_response.status_code == 200
    search_payload = search_response.json()
    assert search_payload["pagination"]["count"] == 1
    assert search_payload["totals"]["total_lists"] == 1
    assert search_payload["results"][0]["indexed_repo_count"] == 2
    assert search_payload["results"][0]["first_commit_at"] is not None

    detail_response = client.get(
        "/api/awesome-lists/awesome-django",
        **_api_key_header(profile),
    )

    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["awesome_list"]["slug"] == "awesome-django"
    assert detail_payload["repo_stats"]["total_stars"] == 155000
    assert detail_payload["language_counts"] == [
        {"name": "JavaScript", "count": 1},
        {"name": "Python", "count": 1},
    ]

    repos_response = client.get(
        "/api/awesome-lists/awesome-django/repositories",
        {
            "language": "Python",
            "min_age_years": "10",
            "stack": "django",
            "package_manager": "poetry",
        },
        **_api_key_header(profile),
    )

    assert repos_response.status_code == 200
    repos_payload = repos_response.json()
    assert repos_payload["pagination"]["count"] == 1
    assert repos_payload["results"][0]["full_name"] == "django/django"


@pytest.mark.django_db
def test_superuser_api_can_create_lists_and_queue_refreshes(client, django_user_model, monkeypatch):
    admin = django_user_model.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password123",
    )
    admin_api_key = admin.profile.rotate_api_key()
    headers = {"HTTP_X_API_KEY": admin_api_key}
    queued = []

    def fake_async_task(func_path, *args, **kwargs):
        queued.append((func_path, args, kwargs))
        return "task-1"

    monkeypatch.setattr("apps.api.views.async_task", fake_async_task)
    monkeypatch.setattr("apps.api.views.transaction.on_commit", lambda callback: callback())

    create_response = client.post(
        "/api/awesome-lists",
        data=json.dumps(
            {
                "source_url": "https://github.com/wsvincent/awesome-django",
                "queue_scan": True,
            }
        ),
        content_type="application/json",
        **headers,
    )

    assert create_response.status_code == 201
    awesome_list = AwesomeList.objects.get(slug="awesome-django")
    assert create_response.json()["awesome_list"]["repo_full_name"] == "wsvincent/awesome-django"
    assert queued == [
        (
            "apps.repos.tasks.sync_awesome_list_task",
            (awesome_list.id,),
            {"group": "Scan awesome list"},
        )
    ]

    repo = Repository.objects.create(
        full_name="django/django",
        owner="django",
        name="django",
        url="https://github.com/django/django",
    )

    list_rescan_response = client.post(
        "/api/awesome-lists/awesome-django/rescan",
        **headers,
    )
    discover_response = client.post(
        "/api/awesome-lists/awesome-django/discover-missing",
        **headers,
    )
    repo_rescan_response = client.post(
        "/api/repositories/django/django/rescan",
        **headers,
    )

    assert list_rescan_response.status_code == 200
    assert list_rescan_response.json()["queued"] is True
    assert discover_response.status_code == 200
    assert repo_rescan_response.status_code == 200
    assert queued[-3:] == [
        (
            "apps.repos.tasks.sync_awesome_list_task",
            (awesome_list.id,),
            {"group": "Scan awesome list"},
        ),
        (
            "apps.repos.tasks.enqueue_missing_repositories_for_awesome_list_task",
            (awesome_list.id,),
            {"group": "Manual awesome-list missing repo discovery"},
        ),
        (
            "apps.repos.tasks.refresh_repository_task",
            (repo.id, repo.full_name),
            {"group": "Refresh repositories"},
        ),
    ]


def test_superuser_api_key_auth_eager_loads_user_and_requires_superuser():
    from apps.api.auth import SuperuserAPIKeyHeaderAuth, SuperuserBearerAPIKeyAuth
    from apps.core.models import Profile

    api_key = "ak_public.secret"

    for auth_class in [SuperuserAPIKeyHeaderAuth, SuperuserBearerAPIKeyAuth]:
        superuser_profile = SimpleNamespace(
            id=11,
            user=SimpleNamespace(id=21, is_superuser=True),
            check_api_key=Mock(return_value=True),
        )
        regular_profile = SimpleNamespace(
            id=12,
            user=SimpleNamespace(id=22, is_superuser=False),
            check_api_key=Mock(return_value=True),
        )

        with patch("apps.core.api_keys.Profile.objects") as objects:
            objects.select_related.return_value.get.return_value = superuser_profile
            response = auth_class().authenticate(HttpRequest(), api_key)

        assert response is superuser_profile
        objects.select_related.assert_called_once_with("user")
        objects.select_related.return_value.get.assert_called_once_with(api_key_prefix="ak_public")
        superuser_profile.check_api_key.assert_called_once_with(api_key)

        with patch("apps.core.api_keys.Profile.objects") as objects:
            objects.select_related.return_value.get.return_value = regular_profile
            response = auth_class().authenticate(HttpRequest(), api_key)

        assert response is None
        regular_profile.check_api_key.assert_called_once_with(api_key)

        with patch("apps.core.api_keys.Profile.objects") as objects:
            objects.select_related.return_value.get.side_effect = Profile.DoesNotExist
            response = auth_class().authenticate(HttpRequest(), "ak_missing.secret")

        assert response is None


def test_staff_api_auth_accepts_staff_and_superuser_profiles():
    from apps.api.auth import StaffAPIKeyHeaderAuth, StaffBearerAPIKeyAuth

    api_key = "ak_public.secret"

    for auth_class in [StaffAPIKeyHeaderAuth, StaffBearerAPIKeyAuth]:
        staff_profile = SimpleNamespace(
            id=11,
            user=SimpleNamespace(id=21, is_staff=True, is_superuser=False),
            check_api_key=Mock(return_value=True),
        )
        superuser_profile = SimpleNamespace(
            id=12,
            user=SimpleNamespace(id=22, is_staff=False, is_superuser=True),
            check_api_key=Mock(return_value=True),
        )
        regular_profile = SimpleNamespace(
            id=13,
            user=SimpleNamespace(id=23, is_staff=False, is_superuser=False),
            check_api_key=Mock(return_value=True),
        )

        with patch("apps.core.api_keys.Profile.objects") as objects:
            objects.select_related.return_value.get.return_value = staff_profile
            response = auth_class().authenticate(HttpRequest(), api_key)
        assert response is staff_profile

        with patch("apps.core.api_keys.Profile.objects") as objects:
            objects.select_related.return_value.get.return_value = superuser_profile
            response = auth_class().authenticate(HttpRequest(), api_key)
        assert response is superuser_profile

        with patch("apps.core.api_keys.Profile.objects") as objects:
            objects.select_related.return_value.get.return_value = regular_profile
            response = auth_class().authenticate(HttpRequest(), api_key)
        assert response is None


@pytest.mark.django_db
def test_staff_api_key_can_manage_blog_posts(client, django_user_model):
    from apps.blog.models import BlogCategory, BlogPost, BlogTag
    from apps.repos.search_services import MAX_API_PAGE_SIZE

    staff = django_user_model.objects.create_user(
        username="staff",
        email="staff@example.com",
        password="password123",
        is_staff=True,
    )
    second_staff = django_user_model.objects.create_user(
        username="second-staff",
        email="second-staff@example.com",
        password="password123",
        is_staff=True,
    )
    headers = {"HTTP_X_API_KEY": staff.profile.rotate_api_key()}
    second_headers = {"HTTP_X_API_KEY": second_staff.profile.rotate_api_key()}

    create_response = client.post(
        "/api/blog/posts",
        data=json.dumps(
            {
                "title": "Best Django repositories",
                "excerpt": "A curated guide to Django repositories.",
                "content_markdown": (
                    "## Start here\n"
                    "[Good link](https://example.com)\n"
                    "<script>alert('x')</script>\n"
                    "[Bad link](javascript:alert('x'))"
                ),
                "category_slugs": ["django"],
                "tag_slugs": ["pseo", "repository-discovery"],
                "target_keyword": "best django repositories",
                "template_key": "repo-roundup",
                "source_data": {"seed": "django"},
            }
        ),
        content_type="application/json",
        **headers,
    )

    assert create_response.status_code == 201
    create_payload = create_response.json()
    assert create_payload["slug"] == "best-django-repositories"
    assert create_payload["status"] == BlogPost.Status.DRAFT
    assert create_payload["author_username"] == "staff"
    assert create_payload["categories"][0]["slug"] == "django"
    assert {tag["slug"] for tag in create_payload["tags"]} == {
        "pseo",
        "repository-discovery",
    }
    assert "<script>" not in create_payload["content_html"]
    assert "javascript:alert" not in create_payload["content_html"]
    assert 'href="https://example.com" rel="noopener noreferrer"' in create_payload["content_html"]

    clear_author_response = client.patch(
        "/api/blog/posts/best-django-repositories",
        data=json.dumps({"author_id": None}),
        content_type="application/json",
        **headers,
    )
    patch_response = client.patch(
        "/api/blog/posts/best-django-repositories",
        data=json.dumps(
            {
                "seo_title": "Best Django Repositories · Awesome",
                "meta_description": "Find maintained Django repositories from awesome lists.",
                "category_slugs": ["django", "python"],
                "tag_slugs": ["pseo"],
            }
        ),
        content_type="application/json",
        **headers,
    )
    review_response = client.post(
        "/api/blog/posts/best-django-repositories/review",
        **headers,
    )
    publish_response = client.post(
        "/api/blog/posts/best-django-repositories/publish",
        **headers,
    )
    review_published_response = client.post(
        "/api/blog/posts/best-django-repositories/review",
        **second_headers,
    )
    put_response = client.put(
        "/api/blog/posts/best-django-repositories",
        data=json.dumps(
            {
                "title": "Best Django repositories",
                "content_markdown": "Updated body.",
            }
        ),
        content_type="application/json",
        **headers,
    )
    list_response = client.get("/api/blog/posts", {"status": "published"}, **headers)
    large_page_response = client.get("/api/blog/posts", {"page_size": "10000"}, **headers)
    categories_response = client.get("/api/blog/categories", **headers)
    limited_categories_response = client.get("/api/blog/categories", {"limit": "1"}, **headers)
    tags_response = client.get("/api/blog/tags", **headers)
    limited_tags_response = client.get("/api/blog/tags", {"limit": "1"}, **headers)

    assert clear_author_response.status_code == 200
    assert clear_author_response.json()["author_id"] is None
    assert clear_author_response.json()["author_username"] == ""
    assert patch_response.status_code == 200
    assert {category["slug"] for category in patch_response.json()["categories"]} == {
        "django",
        "python",
    }
    assert review_response.status_code == 200
    assert review_response.json()["status"] == BlogPost.Status.REVIEW
    assert review_response.json()["reviewed_by_username"] == "staff"
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == BlogPost.Status.PUBLISHED
    assert publish_response.json()["published_at"] is not None
    assert review_published_response.status_code == 200
    assert review_published_response.json()["status"] == BlogPost.Status.PUBLISHED
    assert review_published_response.json()["reviewed_by_username"] == "staff"
    assert put_response.status_code == 200
    assert put_response.json()["status"] == BlogPost.Status.PUBLISHED
    assert put_response.json()["content_html"] == "<p>Updated body.</p>"
    assert list_response.status_code == 200
    assert list_response.json()["pagination"]["count"] == 1
    assert large_page_response.status_code == 200
    assert large_page_response.json()["pagination"]["page_size"] == MAX_API_PAGE_SIZE
    assert {category["slug"] for category in categories_response.json()} == {"django", "python"}
    assert len(limited_categories_response.json()) == 1
    assert {tag["slug"] for tag in tags_response.json()} == {"pseo", "repository-discovery"}
    assert len(limited_tags_response.json()) == 1
    assert BlogCategory.objects.filter(slug="python").exists()
    assert BlogTag.objects.filter(slug="pseo").exists()

    public_response = client.get("/blog/best-django-repositories/")
    delete_response = client.delete("/api/blog/posts/best-django-repositories", **headers)
    missing_response = client.get("/api/blog/posts/best-django-repositories", **headers)

    assert public_response.status_code == 200
    assert delete_response.status_code == 204
    assert missing_response.status_code == 404


@pytest.mark.django_db
def test_blog_post_create_rejects_unknown_author_id(client, django_user_model):
    from apps.blog.models import BlogPost

    staff = django_user_model.objects.create_user(
        username="staff-author",
        email="staff-author@example.com",
        password="password123",
        is_staff=True,
    )
    headers = {"HTTP_X_API_KEY": staff.profile.rotate_api_key()}

    response = client.post(
        "/api/blog/posts",
        data=json.dumps({"title": "Bad author", "author_id": 999999}),
        content_type="application/json",
        **headers,
    )

    assert response.status_code == 400
    assert "Unknown author_id" in response.json()["detail"]
    assert not BlogPost.objects.filter(slug="bad-author").exists()


@pytest.mark.django_db
def test_blog_post_create_rolls_back_when_taxonomy_write_fails(
    client,
    django_user_model,
    monkeypatch,
):
    from django.db import IntegrityError

    from apps.blog.models import BlogPost

    staff = django_user_model.objects.create_user(
        username="staff-rollback",
        email="staff-rollback@example.com",
        password="password123",
        is_staff=True,
    )
    headers = {"HTTP_X_API_KEY": staff.profile.rotate_api_key()}

    def fail_taxonomy(*_args, **_kwargs):
        raise IntegrityError("taxonomy write failed")

    monkeypatch.setattr("apps.blog.api._set_taxonomy", fail_taxonomy)

    response = client.post(
        "/api/blog/posts",
        data=json.dumps({"title": "Rollback me", "category_slugs": ["django"]}),
        content_type="application/json",
        **headers,
    )

    assert response.status_code == 409
    assert not BlogPost.objects.filter(slug="rollback-me").exists()


@pytest.mark.django_db
def test_staff_session_can_create_blog_post_without_api_key(client, django_user_model):
    staff = django_user_model.objects.create_user(
        username="staff-session",
        email="staff-session@example.com",
        password="password123",
        is_staff=True,
    )
    client.force_login(staff)

    response = client.post(
        "/api/blog/posts",
        data=json.dumps({"title": "Session-created blog post"}),
        content_type="application/json",
    )

    assert response.status_code == 201
    assert response.json()["author_username"] == "staff-session"


@pytest.mark.django_db
def test_superuser_api_key_can_create_blog_post(client, django_user_model):
    superuser = django_user_model.objects.create_user(
        username="blog-superuser",
        email="blog-superuser@example.com",
        password="password123",
        is_superuser=True,
    )

    response = client.post(
        "/api/blog/posts",
        data=json.dumps({"title": "Superuser-created blog post"}),
        content_type="application/json",
        **{"HTTP_X_API_KEY": superuser.profile.rotate_api_key()},
    )

    assert response.status_code == 201
    assert response.json()["author_username"] == "blog-superuser"


@pytest.mark.django_db
def test_blog_management_endpoints_reject_regular_and_anonymous_users(client, profile):
    from apps.blog.models import BlogPost

    post = BlogPost.objects.create(
        title="Protected post",
        slug="protected-post",
        content_markdown="Original body.",
    )
    request_specs = [
        ("get", "/api/blog/posts", None),
        ("post", "/api/blog/posts", {"title": "Unauthorized post"}),
        ("get", "/api/blog/posts/protected-post", None),
        ("put", "/api/blog/posts/protected-post", {"title": "Unauthorized replacement"}),
        ("patch", "/api/blog/posts/protected-post", {"title": "Unauthorized patch"}),
        ("delete", "/api/blog/posts/protected-post", None),
        ("post", "/api/blog/posts/protected-post/review", None),
        ("post", "/api/blog/posts/protected-post/publish", None),
        ("get", "/api/blog/categories", None),
        ("get", "/api/blog/tags", None),
    ]

    callers = [
        ("anonymous", {}),
        ("regular API key", _api_key_header(profile)),
    ]

    for caller_name, headers in callers:
        for method, path, payload in request_specs:
            request_kwargs = dict(headers)
            if payload is not None:
                request_kwargs["data"] = json.dumps(payload)
                request_kwargs["content_type"] = "application/json"

            response = getattr(client, method)(path, **request_kwargs)

            assert response.status_code in {401, 403}, (
                f"{caller_name} {method.upper()} {path} returned "
                f"{response.status_code}"
            )

    post.refresh_from_db()
    assert post.title == "Protected post"
    assert post.status == BlogPost.Status.DRAFT
    assert BlogPost.objects.filter(slug="protected-post").exists()
    assert not BlogPost.objects.filter(slug="unauthorized-post").exists()
