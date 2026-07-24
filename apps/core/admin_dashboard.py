from datetime import datetime, time, timedelta

from django.db.models import (
    Count,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Value,
)
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from apps.repos.models import AwesomeListItem, Repository, RepositorySnapshot

STAR_BANDS = (
    {"label": "0–99", "minimum": 0, "maximum": 100},
    {"label": "100–999", "minimum": 100, "maximum": 1_000},
    {"label": "1k–9.9k", "minimum": 1_000, "maximum": 10_000},
    {"label": "10k–49.9k", "minimum": 10_000, "maximum": 50_000},
    {"label": "50k+", "minimum": 50_000, "maximum": None},
)


def _percentage(value, total):
    if not total:
        return 0
    return round((value / total) * 100)


def _star_filter(band, *, field="stars"):
    filters = Q(**{f"{field}__gte": band["minimum"]})
    if band["maximum"] is not None:
        filters &= Q(**{f"{field}__lt": band["maximum"]})
    return filters


def _analysis_activity(first_day_start):
    current_tz = timezone.get_current_timezone()
    first_day = timezone.localtime(first_day_start, current_tz).date()
    daily_rows = (
        RepositorySnapshot.objects.filter(captured_at__gte=first_day_start)
        .annotate(day=TruncDate("captured_at", tzinfo=current_tz))
        .values("day")
        .annotate(
            run_count=Count("id"),
            repository_count=Count("repository_id", distinct=True),
        )
        .order_by("day")
    )
    daily_counts = {row["day"]: row for row in daily_rows}
    max_run_count = max((row["run_count"] for row in daily_rows), default=0)

    activity = []
    for offset in range(30):
        day = first_day + timedelta(days=offset)
        row = daily_counts.get(day, {})
        run_count = row.get("run_count", 0)
        activity.append(
            {
                "date": day,
                "run_count": run_count,
                "repository_count": row.get("repository_count", 0),
                "bar_height": (
                    max(4, round((run_count / max_run_count) * 100))
                    if max_run_count and run_count
                    else 0
                ),
            }
        )
    return activity


def repository_monitoring_context(*, now=None):
    now = now or timezone.now()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    current_tz = timezone.get_current_timezone()
    first_month_day = timezone.localtime(now, current_tz).date() - timedelta(days=29)
    month_ago = timezone.make_aware(
        datetime.combine(first_month_day, time.min),
        current_tz,
    )

    snapshot_aggregates = {
        "day": Count(
            "repository_id",
            filter=Q(captured_at__gte=day_ago),
            distinct=True,
        ),
        "week": Count(
            "repository_id",
            filter=Q(captured_at__gte=week_ago),
            distinct=True,
        ),
        "month": Count("repository_id", distinct=True),
        "month_runs": Count("id"),
    }
    repository_aggregates = {
        "total": Count("id"),
        "added_day": Count("id", filter=Q(created_at__gte=day_ago)),
        "added_week": Count("id", filter=Q(created_at__gte=week_ago)),
        "added_month": Count("id", filter=Q(created_at__gte=month_ago)),
    }
    for index, band in enumerate(STAR_BANDS):
        repository_aggregates[f"repositories_{index}"] = Count(
            "id",
            filter=_star_filter(band),
        )
        snapshot_star_filter = _star_filter(band, field="repository__stars")
        snapshot_aggregates[f"analyzed_{index}"] = Count(
            "repository_id",
            filter=snapshot_star_filter,
            distinct=True,
        )
        snapshot_aggregates[f"runs_{index}"] = Count(
            "id",
            filter=snapshot_star_filter,
        )

    recent_snapshots = RepositorySnapshot.objects.filter(captured_at__gte=month_ago)
    snapshot_totals = recent_snapshots.aggregate(**snapshot_aggregates)
    latest_analysis_at = (
        RepositorySnapshot.objects.order_by("-captured_at")
        .values_list("captured_at", flat=True)
        .first()
    )
    repository_totals = Repository.objects.aggregate(**repository_aggregates)

    total_repositories = repository_totals["total"]
    analysis_runs_month = snapshot_totals["month_runs"]
    distribution = []
    for index, band in enumerate(STAR_BANDS):
        repository_count = repository_totals[f"repositories_{index}"]
        analyzed_repository_count = snapshot_totals[f"analyzed_{index}"]
        analysis_run_count = snapshot_totals[f"runs_{index}"]
        catalog_share = _percentage(repository_count, total_repositories)
        analysis_share = _percentage(analysis_run_count, analysis_runs_month)
        distribution.append(
            {
                "label": band["label"],
                "repository_count": repository_count,
                "analyzed_repository_count": analyzed_repository_count,
                "analysis_run_count": analysis_run_count,
                "coverage_percent": _percentage(
                    analyzed_repository_count,
                    repository_count,
                ),
                "catalog_share_percent": catalog_share,
                "analysis_share_percent": analysis_share,
                "catalog_bar_width": max(2, catalog_share) if repository_count else 0,
                "analysis_bar_width": max(2, analysis_share) if analysis_run_count else 0,
                "runs_per_repository": (
                    round(analysis_run_count / repository_count, 1) if repository_count else 0
                ),
            }
        )

    gap_count = sum(
        band["repository_count"] > 0 and band["analyzed_repository_count"] == 0
        for band in distribution
    )
    if not analysis_runs_month:
        distribution_status = "No recent data"
        distribution_status_tone = "empty"
    elif gap_count:
        distribution_status = "Coverage gaps"
        distribution_status_tone = "warning"
    else:
        distribution_status = "All star bands represented"
        distribution_status_tone = "ok"

    source_list_count = (
        AwesomeListItem.objects.filter(repository_id=OuterRef("pk"))
        .values("repository_id")
        .annotate(total=Count("id"))
        .values("total")[:1]
    )
    latest_repository_analysis = (
        RepositorySnapshot.objects.filter(repository_id=OuterRef("pk"))
        .order_by("-captured_at")
        .values("captured_at")[:1]
    )
    recent_repositories = (
        Repository.objects.annotate(
            source_list_count=Coalesce(
                Subquery(source_list_count),
                Value(0),
                output_field=IntegerField(),
            ),
            latest_analysis_at=Subquery(latest_repository_analysis),
        )
        .only("id", "owner", "name", "full_name", "language", "stars", "created_at")
        .order_by("-created_at", "-id")[:10]
    )

    return {
        "total_repositories": total_repositories,
        "repositories_analyzed": {
            "day": snapshot_totals["day"],
            "week": snapshot_totals["week"],
            "month": snapshot_totals["month"],
        },
        "analysis_runs_month": analysis_runs_month,
        "analysis_coverage_month": _percentage(
            snapshot_totals["month"],
            total_repositories,
        ),
        "repositories_not_analyzed_month": max(
            total_repositories - snapshot_totals["month"],
            0,
        ),
        "latest_analysis_at": latest_analysis_at,
        "repositories_added": {
            "day": repository_totals["added_day"],
            "week": repository_totals["added_week"],
            "month": repository_totals["added_month"],
        },
        "analysis_activity": _analysis_activity(month_ago),
        "analysis_distribution": distribution,
        "analysis_distribution_status": distribution_status,
        "analysis_distribution_status_tone": distribution_status_tone,
        "analysis_distribution_gap_count": gap_count,
        "recent_repositories": recent_repositories,
    }
