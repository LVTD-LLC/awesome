import pytest
from django.urls import reverse

from apps.repos.discovery import awesome_list_starting_points
from apps.repos.models import AwesomeList


@pytest.mark.django_db
def test_starting_points_use_current_slug_and_skip_unavailable_sources(django_assert_num_queries):
    python_list = AwesomeList.objects.create(
        name="Python tools",
        slug="python-tools",
        repo_full_name="vinta/awesome-python",
        source_url="https://github.com/vinta/awesome-python",
    )
    AwesomeList.objects.create(
        name="Inactive",
        slug="inactive",
        repo_full_name="agarrharr/awesome-cli-apps",
        source_url="https://github.com/agarrharr/awesome-cli-apps",
        is_active=False,
    )
    AwesomeList.objects.create(
        name="Archived",
        slug="archived",
        repo_full_name="public-apis/public-apis",
        source_url="https://github.com/public-apis/public-apis",
        is_archived=True,
    )
    with django_assert_num_queries(1):
        entries = awesome_list_starting_points()
        assert len(entries) == 1
        assert entries[0]["awesome_list"].get_absolute_url() == python_list.get_absolute_url()
        assert entries[0]["awesome_list"].name == "Python tools"

    python_list.is_disabled = True
    python_list.save()
    assert awesome_list_starting_points() == []


@pytest.mark.django_db
def test_directory_starting_points_do_not_displace_search_results(client):
    AwesomeList.objects.create(
        name="Python tools",
        slug="python-tools",
        repo_full_name="vinta/awesome-python",
        source_url="https://github.com/vinta/awesome-python",
        stars=100,
    )
    for index in range(30):
        AwesomeList.objects.create(
            name=f"Other list {index}",
            slug=f"other-{index}",
            source_url=f"https://github.com/example/list-{index}",
        )
    response = client.get(reverse("repos:list"))
    assert response.status_code == 200
    assert b"Start with what you want to do" in response.content
    assert b'href="/lists/python-tools/"' in response.content
    assert b'data-discovery-action="vinta/awesome-python"' in response.content
    assert b'data-discovery-action="directory_checklist"' in response.content
    assert b'href="/blog/how-to-shortlist-github-repositories/"' in response.content
    assert response.content.index(b"Search lists") < response.content.index(b"Start with what")

    for params in ({"q": "Python"}, {"sort": "recent"}, {"page": "2"}):
        filtered = client.get(reverse("repos:list"), params)
        assert filtered.status_code == 200
        assert b"Start with what you want to do" not in filtered.content
        assert filtered.context["list_starting_points"] == []


@pytest.mark.django_db
def test_directory_omits_chooser_when_no_starting_points_exist(client):
    response = client.get(reverse("repos:list"))
    assert response.status_code == 200
    assert b"Start with what you want to do" not in response.content
