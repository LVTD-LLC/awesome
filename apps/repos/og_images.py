from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import cache
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from apps.repos.models import Repository

OG_IMAGE_WIDTH = 1200
OG_IMAGE_HEIGHT = 630
OG_IMAGE_CACHE_TIMEOUT_SECONDS = 6 * 60 * 60
OG_IMAGE_HISTORY_DAYS = 30

BACKGROUND = "#F7FBF7"
CHART_FILL = "#BDEBC7"
GREEN = "#15803D"
GREEN_DARK = "#166534"
SLATE = "#0F172A"
SLATE_MID = "#334155"
SLATE_MUTED = "#64748B"
SLATE_LIGHT = "#94A3B8"
BLUE = "#2563EB"
AMBER = "#F59E0B"
WHITE = "#F8FAFC"

FONT_PATHS = {
    False: (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    ),
    True: (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    ),
}


@dataclass(frozen=True)
class RepositoryOgImagePoint:
    captured_at: datetime
    stars: int


@dataclass(frozen=True)
class RepositoryOgImageData:
    full_name: str
    owner: str
    name: str
    description: str
    awesome_list_count: int
    last_update: datetime | None
    baseline_captured_at: datetime | None
    latest_captured_at: datetime | None
    points: tuple[RepositoryOgImagePoint, ...]
    star_delta: int | None
    star_growth_percent: float | None
    commit_delta: int | None
    commit_growth_percent: float | None
    cache_key: str

    @property
    def has_30_day_history(self) -> bool:
        return self.baseline_captured_at is not None and self.latest_captured_at is not None


def _growth_percent(delta: int | None, baseline: int | None) -> float | None:
    if delta is None or not baseline:
        return None
    return delta / baseline * 100


def build_repository_og_image_data(repository: Repository) -> RepositoryOgImageData:
    snapshots = repository.snapshots.order_by("captured_at", "id")
    latest = snapshots.only("captured_at", "stars", "commit_count").last()
    baseline = None
    points: tuple[RepositoryOgImagePoint, ...] = ()

    if latest is not None:
        cutoff = latest.captured_at - timedelta(days=OG_IMAGE_HISTORY_DAYS)
        baseline = (
            snapshots.filter(captured_at__lte=cutoff)
            .only("captured_at", "stars", "commit_count")
            .last()
        )
        if baseline is not None:
            points = tuple(
                RepositoryOgImagePoint(captured_at=captured_at, stars=stars)
                for captured_at, stars in snapshots.filter(
                    captured_at__gte=baseline.captured_at
                ).values_list("captured_at", "stars")
            )

    star_delta = latest.stars - baseline.stars if latest and baseline else None
    commit_delta = None
    if (
        latest
        and baseline
        and latest.commit_count is not None
        and baseline.commit_count is not None
    ):
        commit_delta = latest.commit_count - baseline.commit_count

    awesome_list_count = repository.awesome_list_count
    last_update = (
        repository.github_updated_at
        or repository.last_synced_at
        or (latest.captured_at if latest else None)
        or repository.updated_at
    )
    cache_state = (
        repository.full_name,
        repository.description,
        repository.updated_at.isoformat(),
        awesome_list_count,
        last_update.isoformat() if last_update else None,
        latest.captured_at.isoformat() if latest else None,
        latest.stars if latest else None,
        tuple((point.captured_at.isoformat(), point.stars) for point in points),
        baseline.commit_count if baseline else None,
        latest.commit_count if latest else None,
    )
    cache_digest = hashlib.sha256(repr(cache_state).encode()).hexdigest()[:24]

    return RepositoryOgImageData(
        full_name=repository.full_name,
        owner=repository.owner,
        name=repository.name,
        description=repository.description,
        awesome_list_count=awesome_list_count,
        last_update=last_update,
        baseline_captured_at=baseline.captured_at if baseline else None,
        latest_captured_at=latest.captured_at if latest else None,
        points=points,
        star_delta=star_delta,
        star_growth_percent=_growth_percent(star_delta, baseline.stars if baseline else None),
        commit_delta=commit_delta,
        commit_growth_percent=_growth_percent(
            commit_delta,
            baseline.commit_count if baseline else None,
        ),
        cache_key=f"awesome:repository-og:{repository.pk}:{cache_digest}",
    )


@cache
def _font(size: int, *, bold: bool = False):
    for font_path in FONT_PATHS[bold]:
        if font_path.exists():
            return ImageFont.truetype(font_path, size)
    return ImageFont.load_default(size=size)


def _text_width(draw: ImageDraw.ImageDraw, text: str, font) -> float:
    return draw.textlength(text, font=font)


def _fit_title_font(draw: ImageDraw.ImageDraw, text: str):
    for size in range(76, 37, -2):
        font = _font(size, bold=True)
        if _text_width(draw, text, font) <= 1070:
            return font
    return _font(38, bold=True)


def _truncate_to_width(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> str:
    if _text_width(draw, text, font) <= max_width:
        return text
    suffix = "..."
    low = 0
    high = len(text)
    while low < high:
        midpoint = (low + high + 1) // 2
        if _text_width(draw, f"{text[:midpoint]}{suffix}", font) <= max_width:
            low = midpoint
        else:
            high = midpoint - 1
    return f"{text[:low].rstrip()}{suffix}"


def _wrap_description(draw: ImageDraw.ImageDraw, text: str, font) -> list[str]:
    words = text.split()
    if not words:
        return ["Repository details on Awesome"]

    lines: list[str] = []
    word_index = 0
    while word_index < len(words) and len(lines) < 3:
        current = ""
        while word_index < len(words):
            candidate = f"{current} {words[word_index]}".strip()
            if current and _text_width(draw, candidate, font) > 560:
                break
            current = candidate
            word_index += 1
            if _text_width(draw, current, font) > 560:
                break

        if len(lines) == 2 and word_index < len(words):
            current = f"{current} {words[word_index]}"
        lines.append(_truncate_to_width(draw, current, font, 560))

    return lines


def _chart_coordinates(data: RepositoryOgImageData) -> list[tuple[float, float]]:
    if len(data.points) < 2:
        return []
    first_time = data.points[0].captured_at.timestamp()
    last_time = data.points[-1].captured_at.timestamp()
    if first_time == last_time:
        return []

    values = [point.stars for point in data.points]
    value_min = min(values)
    value_max = max(values)
    value_range = value_max - value_min
    padding = max(value_range * 0.08, 1)
    domain_min = value_min - padding
    domain_max = value_max + padding

    return [
        (
            (point.captured_at.timestamp() - first_time)
            / (last_time - first_time)
            * OG_IMAGE_WIDTH,
            500 - (point.stars - domain_min) / (domain_max - domain_min) * 360,
        )
        for point in data.points
    ]


def _draw_brand(draw: ImageDraw.ImageDraw) -> None:
    draw.rounded_rectangle((64, 48, 98, 82), radius=9, fill=SLATE)
    draw.line((73, 58, 73, 72), fill=WHITE, width=3)
    for y, width in ((58, 11), (65, 9), (72, 6)):
        draw.line((78, y, 78 + width, y), fill=WHITE, width=3)
    draw.regular_polygon((89, 73, 6), n_sides=5, rotation=0, fill=AMBER)
    draw.text((111, 59), "AWESOME", font=_font(18, bold=True), fill=GREEN)


def _draw_title(draw: ImageDraw.ImageDraw, data: RepositoryOgImageData) -> None:
    title_font = _fit_title_font(draw, data.full_name)
    title_width = _text_width(draw, data.full_name, title_font)
    if title_width > 1070:
        title = _truncate_to_width(draw, data.full_name, title_font, 1070)
        draw.text((64, 110), title, font=title_font, fill=SLATE, stroke_width=2)
        return

    owner = f"{data.owner}/"
    draw.text((64, 110), owner, font=title_font, fill=SLATE, stroke_width=2)
    draw.text(
        (64 + _text_width(draw, owner, title_font), 110),
        data.name,
        font=title_font,
        fill=GREEN,
        stroke_width=2,
    )


def _draw_description(draw: ImageDraw.ImageDraw, description: str) -> None:
    font = _font(23)
    for index, line in enumerate(_wrap_description(draw, description, font)):
        draw.text((67, 202 + index * 30), line, font=font, fill=SLATE_MID)


def _format_date(value: datetime | None) -> str:
    if value is None:
        return "NOT AVAILABLE"
    return f"{value:%b} {value.day}, {value.year}".upper()


def _format_delta(value: int | None) -> str:
    if value is None:
        return "—"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:,}"


def _format_growth_annotation(
    value: float | None,
    *,
    has_30_day_history: bool,
    delta: int | None,
) -> str:
    if not has_30_day_history:
        return "(needs 30 days)"
    if value is None:
        return "(not available)" if delta is None else "(from 0)"
    sign = "+" if value > 0 else ""
    return f"({sign}{value:.1f}%)"


def _draw_metric(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    color: str,
    value: str,
    label: str,
    annotation: str = "",
) -> None:
    draw.ellipse((x, 550, x + 14, 564), fill=color)
    value_font = _font(28, bold=True)
    draw.text((x + 27, 536), value, font=value_font, fill=SLATE, stroke_width=1)
    if annotation:
        annotation_x = x + 35 + _text_width(draw, value, value_font)
        draw.text((annotation_x, 546), annotation, font=_font(16, bold=True), fill=color)
    draw.text((x + 27, 582), label, font=_font(12, bold=True), fill=SLATE_MID)


def render_repository_og_image(data: RepositoryOgImageData) -> bytes:
    image = Image.new("RGB", (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    chart_points = _chart_coordinates(data)

    if chart_points:
        draw.polygon(
            [*chart_points, (OG_IMAGE_WIDTH, OG_IMAGE_HEIGHT), (0, OG_IMAGE_HEIGHT)],
            fill=CHART_FILL,
        )
        draw.line(chart_points, fill=GREEN, width=4, joint="curve")
        endpoint_x, endpoint_y = chart_points[-1]
        draw.ellipse(
            (endpoint_x - 10, endpoint_y - 10, endpoint_x + 10, endpoint_y + 10),
            fill=GREEN,
            outline=BACKGROUND,
            width=5,
        )
        draw.text(
            (965, 104),
            "30-DAY STAR GROWTH",
            font=_font(12, bold=True),
            fill=GREEN_DARK,
        )
    else:
        draw.text((930, 340), "30-DAY STAR GROWTH", font=_font(12, bold=True), fill=GREEN_DARK)
        draw.text((900, 368), "Not enough history yet", font=_font(17, bold=True), fill=SLATE_MUTED)
        tracking_date = _format_date(data.latest_captured_at)
        draw.text(
            (900, 397),
            f"Tracking started {tracking_date.title()}",
            font=_font(13),
            fill=SLATE_LIGHT,
        )

    _draw_brand(draw)
    _draw_title(draw, data)
    _draw_description(draw, data.description)
    _draw_metric(
        draw,
        x=64,
        color=GREEN if data.has_30_day_history else SLATE_LIGHT,
        value=_format_delta(data.star_delta),
        annotation=_format_growth_annotation(
            data.star_growth_percent,
            has_30_day_history=data.has_30_day_history,
            delta=data.star_delta,
        ),
        label="STARS IN LAST 30 DAYS" if data.has_30_day_history else "STAR GROWTH",
    )
    _draw_metric(
        draw,
        x=354,
        color=BLUE if data.has_30_day_history else SLATE_LIGHT,
        value=_format_delta(data.commit_delta),
        annotation=_format_growth_annotation(
            data.commit_growth_percent,
            has_30_day_history=data.has_30_day_history,
            delta=data.commit_delta,
        ),
        label="COMMITS IN LAST 30 DAYS" if data.has_30_day_history else "COMMIT GROWTH",
    )
    _draw_metric(
        draw,
        x=684,
        color=GREEN,
        value=_format_date(data.last_update),
        label="LAST UPDATE",
    )
    _draw_metric(
        draw,
        x=984,
        color=AMBER,
        value=f"{data.awesome_list_count:,}",
        label="AWESOME LIST" if data.awesome_list_count == 1 else "AWESOME LISTS",
    )

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
