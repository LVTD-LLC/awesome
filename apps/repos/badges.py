from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from xml.sax.saxutils import escape as xml_escape

if TYPE_CHECKING:
    from apps.repos.models import Repository


BADGE_WIDTH = 640
BADGE_HEIGHT = 200
BADGE_HISTORY_LIMIT = 60
CHART_X = 300
CHART_Y = 56
CHART_WIDTH = 296
CHART_HEIGHT = 88
FONT_FAMILY = "Inter, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"


@dataclass(frozen=True)
class BadgeMetric:
    key: str
    value_attr: str
    snapshot_attr: str
    singular_label: str
    plural_label: str
    title: str


BADGE_METRICS = {
    "stars": BadgeMetric(
        key="stars",
        value_attr="stars",
        snapshot_attr="stars",
        singular_label="star",
        plural_label="stars",
        title="Star history",
    ),
    "commits": BadgeMetric(
        key="commits",
        value_attr="commit_count",
        snapshot_attr="commit_count",
        singular_label="commit",
        plural_label="commits",
        title="Commit history",
    ),
}

BADGE_THEMES = {
    "light": {
        "background": "#ffffff",
        "border": "#dbe5d3",
        "text": "#0f172a",
        "muted": "#475569",
        "soft": "#f8fafc",
        "grid": "#e2e8f0",
        "accent": "#15803d",
        "accent_soft": "#dcfce7",
        "accent_text": "#166534",
    },
    "dark": {
        "background": "#020617",
        "border": "#1e293b",
        "text": "#f8fafc",
        "muted": "#cbd5e1",
        "soft": "#0f172a",
        "grid": "#1e293b",
        "accent": "#22c55e",
        "accent_soft": "#052e16",
        "accent_text": "#bbf7d0",
    },
}


def repository_badge_svg(
    repository: Repository,
    *,
    metric: str = "stars",
    theme: str = "light",
) -> str:
    metric_config = BADGE_METRICS.get(metric, BADGE_METRICS["stars"])
    colors = BADGE_THEMES.get(theme, BADGE_THEMES["light"])
    history_values = _metric_history_values(repository, metric_config)
    current_value = _current_metric_value(repository, metric_config)
    current_label = _format_compact_number(current_value)
    metric_label = _metric_label(metric_config, current_value)
    awesome_list_count = _awesome_list_count(repository)
    secondary_parts = [f"{awesome_list_count} awesome {_pluralize('list', awesome_list_count)}"]
    if repository.language:
        secondary_parts.append(repository.language)
    if repository.is_archived:
        secondary_parts.append("archived")

    line_path = _sparkline_path(history_values)
    area_path = _sparkline_area_path(line_path)
    minimum = min(history_values)
    maximum = max(history_values)
    range_label = _format_range(minimum, maximum)
    history_label = (
        f"{len(history_values)} captures" if len(history_values) > 1 else "current catalog snapshot"
    )
    full_name = _truncate_text(repository.full_name, 34)
    title = _escape_text(f"Awesome badge for {repository.full_name}")
    description = _escape_text(
        f"{repository.full_name} has {_format_full_number(current_value)} {metric_label} "
        f"and appears in {awesome_list_count} awesome {_pluralize('list', awesome_list_count)}."
    )
    last_x = _sparkline_last_x(history_values)
    last_y = _sparkline_last_y(history_values)
    mid_y = CHART_Y + CHART_HEIGHT / 2
    chart_right = CHART_X + CHART_WIDTH

    background = colors["background"]
    border = colors["border"]
    text = colors["text"]
    muted = colors["muted"]
    soft = colors["soft"]
    grid = colors["grid"]
    accent = colors["accent"]
    accent_soft = colors["accent_soft"]
    accent_text = colors["accent_text"]

    svg_lines = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{BADGE_WIDTH}" '
            f'height="{BADGE_HEIGHT}" viewBox="0 0 {BADGE_WIDTH} {BADGE_HEIGHT}" '
            'role="img" aria-labelledby="title desc">'
        ),
        f'  <title id="title">{title}</title>',
        f'  <desc id="desc">{description}</desc>',
        f'  <rect width="{BADGE_WIDTH}" height="{BADGE_HEIGHT}" rx="20" fill="{background}" />',
        (
            f'  <rect x="0.5" y="0.5" width="{BADGE_WIDTH - 1}" '
            f'height="{BADGE_HEIGHT - 1}" rx="19.5" fill="none" stroke="{border}" />'
        ),
        f'  <g font-family="{FONT_FAMILY}">',
        f'    <rect x="28" y="24" width="88" height="28" rx="14" fill="{accent_soft}" />',
        (
            '    <text x="72" y="43" text-anchor="middle" font-size="13" '
            f'font-weight="700" fill="{accent_text}">Awesome</text>'
        ),
        (
            '    <text x="28" y="80" font-size="25" font-weight="800" '
            f'fill="{text}">{_escape_text(full_name)}</text>'
        ),
        (
            '    <text x="28" y="112" font-size="37" font-weight="800" '
            f'fill="{text}">{_escape_text(current_label)}</text>'
        ),
        (
            '    <text x="28" y="138" font-size="15" font-weight="700" '
            f'fill="{muted}">{_escape_text(metric_label)}</text>'
        ),
        (
            '    <text x="28" y="168" font-size="13" font-weight="600" '
            f'fill="{muted}">{_escape_text(" - ".join(secondary_parts))}</text>'
        ),
        (
            f'    <text x="{CHART_X}" y="34" font-size="14" font-weight="800" '
            f'fill="{text}">{_escape_text(metric_config.title)}</text>'
        ),
        (
            f'    <text x="{CHART_X}" y="160" font-size="12" font-weight="600" '
            f'fill="{muted}">{_escape_text(history_label)}</text>'
        ),
        (
            f'    <text x="{chart_right}" y="160" text-anchor="end" font-size="12" '
            f'font-weight="600" fill="{muted}">{_escape_text(range_label)}</text>'
        ),
        (
            f'    <rect x="{CHART_X}" y="{CHART_Y}" width="{CHART_WIDTH}" '
            f'height="{CHART_HEIGHT}" rx="12" fill="{soft}" />'
        ),
        (
            f'    <path d="M {CHART_X} {mid_y:.1f} H {chart_right}" fill="none" '
            f'stroke="{grid}" stroke-width="1" />'
        ),
        f'    <path d="{area_path}" fill="{accent_soft}" opacity="0.75" />',
        (
            f'    <path d="{line_path}" fill="none" stroke="{accent}" '
            'stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />'
        ),
        f'    <circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="5" fill="{accent}" />',
        "  </g>",
        "</svg>",
        "",
    ]
    return "\n".join(svg_lines)


def _metric_history_values(repository: Repository, metric: BadgeMetric) -> list[int]:
    snapshots = list(
        repository.snapshots.order_by("-captured_at", "-id").only(
            "stars",
            "commit_count",
            "captured_at",
        )[:BADGE_HISTORY_LIMIT]
    )
    values = [
        int(value)
        for snapshot in reversed(snapshots)
        if (value := getattr(snapshot, metric.snapshot_attr)) is not None
    ]
    current_value = _current_metric_value(repository, metric)
    if not values:
        return [current_value]
    if values[-1] != current_value:
        values.append(current_value)
    return values


def _current_metric_value(repository: Repository, metric: BadgeMetric) -> int:
    return int(getattr(repository, metric.value_attr) or 0)


def _awesome_list_count(repository: Repository) -> int:
    annotated_count = getattr(repository, "awesome_count", None)
    if annotated_count is not None:
        return int(annotated_count)
    return repository.awesome_items.count()


def _metric_label(metric: BadgeMetric, value: int) -> str:
    return metric.singular_label if value == 1 else metric.plural_label


def _pluralize(label: str, value: int) -> str:
    return label if value == 1 else f"{label}s"


def _format_compact_number(value: int) -> str:
    absolute = abs(value)
    if absolute >= 1_000_000:
        return f"{_format_compact_decimal(value / 1_000_000)}M"
    if absolute >= 1_000:
        return f"{_format_compact_decimal(value / 1_000)}k"
    return str(value)


def _format_compact_decimal(value: float) -> str:
    rounded = round(value, 1)
    if rounded.is_integer():
        return str(int(rounded))
    return f"{rounded:.1f}"


def _format_full_number(value: int) -> str:
    return f"{value:,}"


def _format_range(minimum: int, maximum: int) -> str:
    if minimum == maximum:
        return _format_full_number(maximum)
    return f"{_format_full_number(minimum)} to {_format_full_number(maximum)}"


def _sparkline_path(values: list[int]) -> str:
    points = _sparkline_points(values)
    first_x, first_y = points[0]
    commands = [f"M {first_x:.1f} {first_y:.1f}"]
    commands.extend(f"L {x:.1f} {y:.1f}" for x, y in points[1:])
    return " ".join(commands)


def _sparkline_area_path(line_path: str) -> str:
    return (
        f"{line_path} L {CHART_X + CHART_WIDTH:.1f} {CHART_Y + CHART_HEIGHT:.1f} "
        f"L {CHART_X:.1f} {CHART_Y + CHART_HEIGHT:.1f} Z"
    )


def _sparkline_last_x(values: list[int]) -> float:
    return _sparkline_points(values)[-1][0]


def _sparkline_last_y(values: list[int]) -> float:
    return _sparkline_points(values)[-1][1]


def _sparkline_points(values: list[int]) -> list[tuple[float, float]]:
    if len(values) == 1:
        return [
            (float(CHART_X), CHART_Y + CHART_HEIGHT / 2),
            (float(CHART_X + CHART_WIDTH), CHART_Y + CHART_HEIGHT / 2),
        ]

    minimum = min(values)
    maximum = max(values)
    spread = maximum - minimum
    points = []
    for index, value in enumerate(values):
        x = CHART_X + (CHART_WIDTH * index / (len(values) - 1))
        if spread == 0:
            y = CHART_Y + CHART_HEIGHT / 2
        else:
            y = CHART_Y + CHART_HEIGHT - (CHART_HEIGHT * (value - minimum) / spread)
        points.append((x, y))
    return points


def _escape_text(value: str) -> str:
    return xml_escape(str(value), {'"': "&quot;", "'": "&apos;"})


def _truncate_text(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return f"{value[: max_length - 3]}..."
