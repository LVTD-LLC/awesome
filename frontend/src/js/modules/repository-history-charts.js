const CHART_SELECTOR = "[data-repository-history-chart]";
const CHART_THEME_TOKENS = {
  border: "--awesome-chart-border",
  commits: "--awesome-chart-commits",
  grid: "--awesome-chart-grid",
  hoverLine: "--awesome-chart-hover-line",
  muted: "--awesome-chart-muted",
  stars: "--awesome-chart-stars",
  surface: "--awesome-chart-surface",
  text: "--awesome-chart-text",
};
const RANGE_CONTROLS_SELECTOR = "[data-repository-history-range-controls]";
const ACTIVE_BUTTON_CLASSES = ["bg-green-700", "text-white", "dark:bg-green-500", "dark:text-gray-950"];
const INACTIVE_BUTTON_CLASSES = [
  "bg-white",
  "text-gray-700",
  "ring-1",
  "ring-gray-200",
  "hover:bg-gray-100",
  "dark:bg-gray-950",
  "dark:text-gray-300",
  "dark:ring-gray-700",
  "dark:hover:bg-gray-900",
];
const DAY_IN_MS = 24 * 60 * 60 * 1000;
const rangeStateBySource = new Map();

document.addEventListener("DOMContentLoaded", () => {
  if (window.d3) {
    initRepositoryHistoryCharts();
    return;
  }

  window.addEventListener("load", () => initRepositoryHistoryCharts(), { once: true });
});

export function initRepositoryHistoryCharts(root = document) {
  const charts = [...root.querySelectorAll(CHART_SELECTOR)];
  if (!charts.length || !window.d3) {
    return;
  }

  initRangeControls(root, charts);

  charts.forEach((chart) => {
    const data = historyData(chart.dataset.historySource);
    const renderer = () => renderChart(chart, data);

    if (window.ResizeObserver) {
      const observer = new ResizeObserver(renderer);
      observer.observe(chart);
    } else {
      renderer();
      window.addEventListener("resize", renderer);
    }
  });

  observeThemeChanges(() => charts.forEach((chart) => renderChart(chart, historyData(chart.dataset.historySource))));
}

function initRangeControls(root, charts) {
  const controls = [...root.querySelectorAll(RANGE_CONTROLS_SELECTOR)];

  controls.forEach((control) => {
    const sourceId = control.dataset.historySource;
    if (!sourceId) {
      return;
    }

    if (!rangeStateBySource.has(sourceId)) {
      rangeStateBySource.set(sourceId, { type: "all" });
    }

    const buttons = [...control.querySelectorAll("[data-chart-range-value]")];
    const startInput = control.querySelector("[data-chart-custom-start]");
    const endInput = control.querySelector("[data-chart-custom-end]");

    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        rangeStateBySource.set(sourceId, rangeFromButtonValue(button.dataset.chartRangeValue));
        clearCustomInputs(startInput, endInput);
        updateRangeControls(control, rangeStateBySource.get(sourceId));
        renderChartsForSource(charts, sourceId);
      });
    });

    [startInput, endInput].forEach((input) => {
      input?.addEventListener("change", () => {
        rangeStateBySource.set(sourceId, customRangeFromInputs(startInput, endInput));
        updateRangeControls(control, rangeStateBySource.get(sourceId));
        renderChartsForSource(charts, sourceId);
      });
    });

    updateRangeControls(control, rangeStateBySource.get(sourceId));
  });
}

function renderChartsForSource(charts, sourceId) {
  charts
    .filter((chart) => chart.dataset.historySource === sourceId)
    .forEach((chart) => renderChart(chart, historyData(chart.dataset.historySource)));
}

function historyData(sourceId) {
  const source = document.getElementById(sourceId);
  if (!source) {
    return [];
  }

  try {
    return JSON.parse(source.textContent);
  } catch {
    return [];
  }
}

function renderChart(chart, rawData) {
  const d3 = window.d3;
  const plot = chart.querySelector("[data-chart-plot]");
  const metric = chart.dataset.metric;
  const label = chart.dataset.label || "Repository history";
  if (!plot || !metric) {
    return;
  }

  const allData = rawData
    .map((point) => ({
      date: new Date(point.captured_at),
      value: point[metric] == null ? null : Number(point[metric]),
    }))
    .filter((point) => Number.isFinite(point.date.getTime()) && Number.isFinite(point.value))
    .sort((left, right) => left.date - right.date);
  const range = chartRange(chart);
  const data = filterHistoryDataByRange(allData, range);

  plot.innerHTML = "";
  plot.classList.add("relative");
  if (!data.length) {
    const message = allData.length && range?.type !== "all" ? "No tracked data in this time range." : "No tracked data yet.";
    plot.append(emptyState(message));
    return;
  }

  const width = Math.max(plot.clientWidth, 320);
  const height = Math.max(plot.clientHeight, 240);
  const margin = { top: 18, right: 18, bottom: 34, left: 54 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const theme = chartTheme(metric);

  const svg = d3
    .select(plot)
    .append("svg")
    .attr("role", "img")
    .attr("aria-label", `${label} history`)
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("width", "100%")
    .attr("height", "100%");

  const x = d3.scaleTime().domain(expandedDateDomain(d3.extent(data, (point) => point.date))).range([0, innerWidth]);
  const y = d3.scaleLinear().domain(expandedValueDomain(d3.extent(data, (point) => point.value))).nice().range([innerHeight, 0]);
  const line = d3
    .line()
    .x((point) => x(point.date))
    .y((point) => y(point.value))
    .curve(d3.curveMonotoneX);

  const content = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
  content
    .append("g")
    .attr("class", "grid")
    .call(d3.axisLeft(y).ticks(4).tickSize(-innerWidth).tickFormat(""))
    .call((axis) => axis.select(".domain").remove())
    .call((axis) => axis.selectAll("line").attr("stroke", theme.grid));

  content
    .append("path")
    .datum(data)
    .attr("fill", "none")
    .attr("stroke", theme.line)
    .attr("stroke-width", 2.5)
    .attr("stroke-linecap", "round")
    .attr("stroke-linejoin", "round")
    .attr("d", line);

  content
    .selectAll("circle")
    .data(data)
    .join("circle")
    .attr("cx", (point) => x(point.date))
    .attr("cy", (point) => y(point.value))
    .attr("r", data.length === 1 ? 4 : 3)
    .attr("fill", theme.line)
    .attr("stroke", theme.surface)
    .attr("stroke-width", 1.5);

  content
    .append("g")
    .attr("transform", `translate(0,${innerHeight})`)
    .call(d3.axisBottom(x).ticks(4).tickSizeOuter(0).tickFormat(d3.timeFormat("%b %d")))
    .call(styleAxis, theme);

  content
    .append("g")
    .call(d3.axisLeft(y).ticks(4).tickSizeOuter(0).tickFormat(d3.format("~s")))
    .call(styleAxis, theme);

  attachTooltip({
    content,
    data,
    height: innerHeight,
    label,
    margin,
    plot,
    theme,
    width: innerWidth,
    x,
    y,
  });
}

function attachTooltip({ content, data, height, label, margin, plot, theme, width, x, y }) {
  const d3 = window.d3;
  const bisect = d3.bisector((point) => point.date).center;
  const marker = content.append("g").attr("display", "none");
  marker.append("line").attr("y1", 0).attr("y2", height).attr("stroke", theme.hoverLine).attr("stroke-dasharray", "3 3");
  marker.append("circle").attr("r", 4).attr("fill", theme.line).attr("stroke", theme.surface).attr("stroke-width", 2);

  const tooltip = d3
    .select(plot)
    .append("div")
    .attr("class", "pointer-events-none absolute z-10 hidden rounded-lg border px-3 py-2 text-xs shadow-lg")
    .style("background", theme.surface)
    .style("border-color", theme.border)
    .style("color", theme.text);

  content
    .append("rect")
    .attr("width", width)
    .attr("height", height)
    .attr("fill", "transparent")
    .on("pointerenter", () => {
      marker.attr("display", null);
      tooltip.classed("hidden", false);
    })
    .on("pointerleave", () => {
      marker.attr("display", "none");
      tooltip.classed("hidden", true);
    })
    .on("pointermove", (event) => {
      const [pointerX] = d3.pointer(event);
      const point = data[bisect(data, x.invert(pointerX))];
      if (!point) {
        return;
      }

      const markerX = x(point.date);
      const markerY = y(point.value);
      marker.attr("transform", `translate(${markerX},0)`);
      marker.select("circle").attr("cy", markerY);
      const tooltipLeft = Math.max(8, Math.min(margin.left + markerX + 12, plot.clientWidth - 160));
      const tooltipTop = Math.max(8, margin.top + markerY - 46);
      tooltip
        .html(`<div class="font-semibold">${formatNumber(point.value)} ${label.toLowerCase()}</div><div>${formatDate(point.date)}</div>`)
        .style("left", `${tooltipLeft}px`)
        .style("top", `${tooltipTop}px`);
    });
}

function filterHistoryDataByRange(data, range) {
  if (!range || range.type === "all" || !data.length) {
    return data;
  }

  const [startDate, endDate] = rangeDateBounds(data, range);
  if (startDate && endDate && startDate > endDate) {
    return [];
  }

  return data.filter((point) => {
    const afterStart = !startDate || point.date >= startDate;
    const beforeEnd = !endDate || point.date <= endDate;
    return afterStart && beforeEnd;
  });
}

function rangeDateBounds(data, range) {
  if (range.type === "days") {
    const latestDate = data[data.length - 1]?.date;
    if (!latestDate) {
      return [null, null];
    }
    return [new Date(latestDate.getTime() - range.days * DAY_IN_MS), latestDate];
  }

  if (range.type === "custom") {
    return [range.startDate, range.endDate];
  }

  return [null, null];
}

function chartRange(chart) {
  const sourceId = chart.dataset.historySource;
  return sourceId ? rangeStateBySource.get(sourceId) : null;
}

function rangeFromButtonValue(value) {
  if (value === "all") {
    return { type: "all" };
  }

  const days = Number(value);
  if (Number.isFinite(days) && days > 0) {
    return { type: "days", days };
  }

  return { type: "all" };
}

function customRangeFromInputs(startInput, endInput) {
  const startValue = startInput?.value || "";
  const endValue = endInput?.value || "";
  if (!startValue && !endValue) {
    return { type: "all" };
  }

  return {
    type: "custom",
    startDate: dateFromInputValue(startValue),
    startLabel: startValue,
    endDate: dateFromInputValue(endValue, { endOfDay: true }),
    endLabel: endValue,
  };
}

function dateFromInputValue(value, { endOfDay = false } = {}) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) {
    return null;
  }

  const [, year, month, day] = match;
  const date = new Date(Number(year), Number(month) - 1, Number(day));
  if (!Number.isFinite(date.getTime())) {
    return null;
  }
  if (endOfDay) {
    date.setHours(23, 59, 59, 999);
  }
  return date;
}

function clearCustomInputs(...inputs) {
  inputs.forEach((input) => {
    if (input) {
      input.value = "";
    }
  });
}

function updateRangeControls(control, range) {
  const activeValue = rangeButtonValue(range);
  control.querySelectorAll("[data-chart-range-value]").forEach((button) => {
    setRangeButtonActive(button, button.dataset.chartRangeValue === activeValue);
  });

  const summary = control.querySelector("[data-chart-range-summary]");
  if (summary) {
    summary.textContent = rangeSummary(range);
  }
}

function rangeButtonValue(range) {
  if (range?.type === "days") {
    return String(range.days);
  }
  if (range?.type === "all") {
    return "all";
  }
  return "";
}

function setRangeButtonActive(button, active) {
  button.setAttribute("aria-pressed", active ? "true" : "false");
  ACTIVE_BUTTON_CLASSES.forEach((className) => button.classList.toggle(className, active));
  INACTIVE_BUTTON_CLASSES.forEach((className) => button.classList.toggle(className, !active));
}

function rangeSummary(range) {
  if (range?.type === "days") {
    return `Last ${range.days} days`;
  }
  if (range?.type === "custom") {
    if (range.startLabel && range.endLabel) {
      return `Custom: ${range.startLabel} to ${range.endLabel}`;
    }
    if (range.startLabel) {
      return `Custom: since ${range.startLabel}`;
    }
    if (range.endLabel) {
      return `Custom: through ${range.endLabel}`;
    }
  }
  return "All tracked data";
}

function chartTheme(metric) {
  const styles = getComputedStyle(document.documentElement);
  const line =
    metric === "stars"
      ? themeToken(styles, CHART_THEME_TOKENS.stars)
      : themeToken(styles, CHART_THEME_TOKENS.commits);
  return {
    border: themeToken(styles, CHART_THEME_TOKENS.border),
    grid: themeToken(styles, CHART_THEME_TOKENS.grid),
    hoverLine: themeToken(styles, CHART_THEME_TOKENS.hoverLine),
    line,
    muted: themeToken(styles, CHART_THEME_TOKENS.muted),
    surface: themeToken(styles, CHART_THEME_TOKENS.surface),
    text: themeToken(styles, CHART_THEME_TOKENS.text),
  };
}

function themeToken(styles, name) {
  return styles.getPropertyValue(name).trim();
}

function styleAxis(axis, theme) {
  axis.select(".domain").attr("stroke", theme.border);
  axis.selectAll("line").attr("stroke", theme.border);
  axis.selectAll("text").attr("fill", theme.muted).attr("font-size", 11);
}

function expandedDateDomain([min, max]) {
  if (!min || !max) {
    return [new Date(), new Date()];
  }
  if (min.getTime() !== max.getTime()) {
    return [min, max];
  }

  const oneDay = 24 * 60 * 60 * 1000;
  return [new Date(min.getTime() - oneDay), new Date(max.getTime() + oneDay)];
}

function expandedValueDomain([min, max]) {
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    return [0, 1];
  }
  if (min === max) {
    return [Math.max(0, min - 1), max + 1];
  }

  return [Math.max(0, min), max];
}

function observeThemeChanges(callback) {
  if (!window.MutationObserver) {
    return;
  }

  const observer = new MutationObserver(callback);
  observer.observe(document.documentElement, {
    attributeFilter: ["class"],
    attributes: true,
  });
}

function emptyState(message) {
  const element = document.createElement("div");
  element.className = "flex h-full items-center justify-center rounded-xl bg-gray-50 text-sm text-gray-500 dark:bg-gray-900 dark:text-gray-400";
  element.textContent = message;
  return element;
}

function formatNumber(value) {
  return new Intl.NumberFormat().format(value);
}

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(value);
}
