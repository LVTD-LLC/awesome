from datetime import UTC, datetime, timedelta
from io import BytesIO

import pytest
from django.core.cache import cache
from django.urls import reverse
from PIL import Image, ImageDraw

from apps.repos.models import AwesomeList, AwesomeListItem, Repository, RepositorySnapshot
from apps.repos.og_images import (
    _font,
    _format_growth_annotation,
    _text_width,
    _wrap_description,
    build_repository_og_image_data,
)

pytestmark = pytest.mark.django_db


def create_repository(**overrides):
    values = {
        "full_name": "openclaw/openclaw",
        "owner": "openclaw",
        "name": "openclaw",
        "url": "https://github.com/openclaw/openclaw",
        "description": "Your own personal AI assistant. Any OS. Any Platform.",
    }
    values.update(overrides)
    return Repository.objects.create(**values)


def add_snapshot(repository, captured_at, *, stars, commits):
    return RepositorySnapshot.objects.create(
        repository=repository,
        captured_at=captured_at,
        stars=stars,
        commit_count=commits,
    )


def test_repository_og_data_uses_the_snapshot_at_the_30_day_cutoff():
    latest_at = datetime(2026, 8, 17, 10, 0, tzinfo=UTC)
    repository = create_repository(github_updated_at=latest_at)
    baseline = add_snapshot(
        repository,
        latest_at - timedelta(days=30, minutes=2),
        stars=1_000,
        commits=200,
    )
    add_snapshot(
        repository,
        latest_at - timedelta(days=15),
        stars=1_250,
        commits=230,
    )
    latest = add_snapshot(repository, latest_at, stars=1_500, commits=250)
    for index in range(2):
        awesome_list = AwesomeList.objects.create(
            name=f"List {index}",
            slug=f"list-{index}",
            source_url=f"https://github.com/example/list-{index}",
        )
        AwesomeListItem.objects.create(awesome_list=awesome_list, repository=repository)

    data = build_repository_og_image_data(repository)

    assert data.has_30_day_history is True
    assert data.baseline_captured_at == baseline.captured_at
    assert data.latest_captured_at == latest.captured_at
    assert data.star_delta == 500
    assert data.star_growth_percent == pytest.approx(50.0)
    assert data.commit_delta == 50
    assert data.commit_growth_percent == pytest.approx(25.0)
    assert data.awesome_list_count == 2
    assert [point.stars for point in data.points] == [1_000, 1_250, 1_500]


def test_repository_og_data_does_not_invent_growth_without_30_days_of_history():
    captured_at = datetime(2026, 8, 17, 10, 0, tzinfo=UTC)
    repository = create_repository()
    add_snapshot(repository, captured_at, stars=2_117, commits=107)

    data = build_repository_og_image_data(repository)

    assert data.has_30_day_history is False
    assert data.star_delta is None
    assert data.star_growth_percent is None
    assert data.commit_delta is None
    assert data.commit_growth_percent is None
    assert data.points == ()


def test_repository_og_growth_annotation_handles_a_zero_baseline_truthfully():
    latest_at = datetime(2026, 8, 17, 10, 0, tzinfo=UTC)
    repository = create_repository()
    add_snapshot(
        repository,
        latest_at - timedelta(days=31),
        stars=0,
        commits=0,
    )
    add_snapshot(repository, latest_at, stars=12, commits=4)

    data = build_repository_og_image_data(repository)

    assert data.has_30_day_history is True
    assert data.star_delta == 12
    assert data.star_growth_percent is None
    assert data.commit_delta == 4
    assert data.commit_growth_percent is None
    assert (
        _format_growth_annotation(
            data.star_growth_percent,
            has_30_day_history=data.has_30_day_history,
            delta=data.star_delta,
        )
        == "(from 0)"
    )
    assert (
        _format_growth_annotation(
            data.commit_growth_percent,
            has_30_day_history=data.has_30_day_history,
            delta=data.commit_delta,
        )
        == "(from 0)"
    )


def test_repository_og_growth_annotation_handles_missing_commit_counts_truthfully():
    latest_at = datetime(2026, 8, 17, 10, 0, tzinfo=UTC)
    repository = create_repository()
    add_snapshot(
        repository,
        latest_at - timedelta(days=31),
        stars=100,
        commits=None,
    )
    add_snapshot(repository, latest_at, stars=120, commits=None)

    data = build_repository_og_image_data(repository)

    assert data.has_30_day_history is True
    assert data.commit_delta is None
    assert data.commit_growth_percent is None
    assert (
        _format_growth_annotation(
            data.commit_growth_percent,
            has_30_day_history=data.has_30_day_history,
            delta=data.commit_delta,
        )
        == "(not available)"
    )


def test_repository_og_image_endpoint_returns_a_cacheable_png(client):
    latest_at = datetime(2026, 8, 17, 10, 0, tzinfo=UTC)
    repository = create_repository(
        full_name="msitarzewski/agency-agents",
        owner="msitarzewski",
        name="agency-agents",
        url="https://github.com/msitarzewski/agency-agents",
        description=(
            "A complete AI agency at your fingertips. From frontend wizards to community "
            "experts, each agent has a specialized process and proven deliverables."
        ),
        github_updated_at=latest_at,
    )
    add_snapshot(
        repository,
        latest_at - timedelta(days=31),
        stars=132_406,
        commits=391,
    )
    add_snapshot(repository, latest_at, stars=145_872, commits=395)

    response = client.get(
        reverse(
            "repos:repo_og_image",
            kwargs={"owner": repository.owner, "name": repository.name},
        )
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "image/png"
    assert response["Cache-Control"] == "public, max-age=21600"
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")
    with Image.open(BytesIO(response.content)) as image:
        assert image.size == (1200, 630)
        assert image.mode == "RGB"


def test_repository_og_image_endpoint_caches_rendered_bytes(client, monkeypatch):
    cache.clear()
    repository = create_repository()
    rendered = b"\x89PNG\r\n\x1a\nrendered"
    render_calls = []

    def fake_render(data):
        render_calls.append(data.full_name)
        return rendered

    monkeypatch.setattr("apps.repos.views.render_repository_og_image", fake_render)
    url = reverse(
        "repos:repo_og_image",
        kwargs={"owner": repository.owner, "name": repository.name},
    )

    first_response = client.get(url)
    second_response = client.get(url)

    assert first_response.content == rendered
    assert second_response.content == rendered
    assert render_calls == [repository.full_name]


def test_repository_og_image_cache_changes_for_a_new_snapshot_within_30_days(client, monkeypatch):
    cache.clear()
    first_at = datetime(2026, 8, 16, 10, 0, tzinfo=UTC)
    repository = create_repository(github_updated_at=first_at)
    add_snapshot(repository, first_at, stars=100, commits=25)
    render_calls = []

    def fake_render(data):
        render_calls.append((data.latest_captured_at, data.cache_key))
        return b"\x89PNG\r\n\x1a\nrendered"

    monkeypatch.setattr("apps.repos.views.render_repository_og_image", fake_render)
    url = reverse(
        "repos:repo_og_image",
        kwargs={"owner": repository.owner, "name": repository.name},
    )

    client.get(url)
    second_at = first_at + timedelta(days=1)
    add_snapshot(repository, second_at, stars=110, commits=25)
    client.get(url)

    assert [captured_at for captured_at, _ in render_calls] == [first_at, second_at]
    assert render_calls[0][1] != render_calls[1][1]


def test_repository_og_description_is_limited_to_three_lines():
    draw = ImageDraw.Draw(Image.new("RGB", (1200, 630)))
    font = _font(23)

    lines = _wrap_description(draw, "descriptive repository text " * 100, font)

    assert len(lines) == 3
    assert lines[-1].endswith("...")
    assert all(_text_width(draw, line, font) <= 560 for line in lines)


def test_repository_og_description_truncates_an_overlong_word():
    draw = ImageDraw.Draw(Image.new("RGB", (1200, 630)))
    font = _font(23)

    lines = _wrap_description(draw, "x" * 500, font)

    assert len(lines) == 1
    assert lines[0].endswith("...")
    assert _text_width(draw, lines[0], font) <= 560
