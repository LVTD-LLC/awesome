/* Shared bootstrap for normal navigation and HTMX. No form contents are captured. */
(() => {
  const config = document.currentScript.dataset;
  const ph = window.posthog;
  if (!ph || !config.posthogKey) return;
  const safeUrl = (value) => {
    try {
      const url = new URL(value, window.location.origin);
      // Account, checkout, and subscription URLs can carry bearer tokens in paths.
      if (/\/(accounts|admin|settings|sponsor|highlighted|newsletter)\b/.test(url.pathname)) {
        return `${url.origin}/[private]`;
      }
      return `${url.origin}${url.pathname}`;
    } catch { return ""; }
  };
  let lastUrl = null;
  ph.init(config.posthogKey, {
    api_host: config.posthogHost,
    defaults: "2025-05-24",
    person_profiles: "identified_only",
    capture_pageview: false,
    capture_pageleave: true,
    capture_exceptions: true,
    capture_performance: { web_vitals: true },
    disable_session_recording: true,
    autocapture: { mask_all_text: true, mask_all_element_attributes: true },
    before_send: (event) => {
      if (!event) return null;
      const scrub = (properties) => {
        if (!properties || typeof properties !== "object") return;
        for (const key of Object.keys(properties || {})) {
          if (/email|password|authorization|token|cookie/i.test(key)) {
            delete properties[key];
          } else if (typeof properties[key] === "object") {
            scrub(properties[key]);
          } else if (/url|referrer/i.test(key) && typeof properties[key] === "string") {
            properties[key] = safeUrl(properties[key]);
          } else if (key === "$pathname") {
            properties[key] = new URL(safeUrl(properties[key])).pathname;
          }
        }
        delete properties.$search_keyword;
      };
      // The SDK's public project token routes ingestion; it is not a user secret.
      const projectToken = event.properties?.token === config.posthogKey;
      scrub(event.properties);
      if (projectToken) event.properties.token = config.posthogKey;
      return event;
    },
    loaded: (client) => {
      if (config.posthogProfile) client.identify(config.posthogProfile);
      else if (client.get_property("$user_id")) client.reset();
      client.register({ app: "browseawesome" });
      pageview();
    },
  });
  function pageview() {
    const url = window.location.href;
    if (url === lastUrl) return;
    lastUrl = url;
    ph.capture("$pageview", { $current_url: safeUrl(url) });
    const path = window.location.pathname;
    const params = new URLSearchParams(window.location.search);
    if (path === "/repos/" || path === "/lists/") {
      ph.capture("catalog_browsed", {
        catalog: path === "/repos/" ? "repositories" : "lists",
        has_query: Boolean(params.get("q")),
        filter_names: [...params.keys()].filter((key) => key !== "q").sort(),
        sort: params.get("sort") || "default",
        page: Number(params.get("page")) || 1,
      });
    } else if (/^\/repos\/[^/]+\/[^/]+\/$/.test(path)) {
      ph.capture("repository_viewed", { repository: path.split("/").slice(2, 4).join("/") });
    }
  }
  document.addEventListener("htmx:pushedIntoHistory", pageview);
  document.addEventListener("htmx:replacedInHistory", pageview);
  document.addEventListener("htmx:historyRestore", pageview);
  document.addEventListener("htmx:configRequest", (event) => {
    if (ph.get_distinct_id()) event.detail.headers["X-POSTHOG-DISTINCT-ID"] = ph.get_distinct_id();
    if (ph.get_session_id()) event.detail.headers["X-POSTHOG-SESSION-ID"] = ph.get_session_id();
  });
  document.addEventListener("click", (event) => {
    const link = event.target.closest("a[href]");
    if (!link) return;
    const url = new URL(link.href, window.location.origin);
    if (url.hostname === "github.com") {
      ph.capture("github_link_clicked", { destination: safeUrl(url.href) });
    } else if (url.origin !== window.location.origin && /^https?:$/.test(url.protocol)) {
      ph.capture("outbound_link_clicked", { destination_host: url.hostname });
    }
  });
})();
