# Browse Awesome observability

Production uses PostHog project **651928 (Browse Awesome)** in LVTD's US organization:
https://us.posthog.com/project/651928

Set these on both the web and worker CapRover apps:

- `POSTHOG_API_KEY`: project token (`phc_`), never the operator's personal API key.
- `POSTHOG_HOST=https://us.i.posthog.com`
- `POSTHOG_LOGS_ENABLED=True`
- `POSTHOG_TRACING_ENABLED=True`
- `POSTHOG_AI_ENABLED=True`
- `POSTHOG_SERVICE_NAME=browseawesome-web` / `browseawesome-worker`

The key enables existing queued domain events (signup, likes, newsletter subscriptions,
checkout/fulfillment, API/MCP activity) and browser pageviews/autocapture.
The three switches independently control new export pipelines. Leave the key empty in
development/tests. No personal API key is required by the application.

## What to look at

- **Web analytics:** pageviews, visitors, referrers, entry pages, web vitals.
- **Product analytics:** `catalog_browsed`, `repository_viewed`, `github_link_clicked`,
  `discovery_action_clicked`, `outbound_link_clicked`, and existing server-side conversion events.
- **Logs:** web/worker structured application and Django logs, INFO and above.
- **Error tracking:** not sent to PostHog. Sentry owns error tracking; the PostHog
  browser and Python SDKs have exception capture turned off so 404s and other errors do not
  bill as PostHog exceptions. Failed background jobs are still logged as
  `background_job_failed` without task arguments or results.
- **Tracing:** request route, method, status and duration; MCP tool spans; AI agent spans.
  This is scoped instrumentation, not complete database/network auto-instrumentation.
- **AI observability:** PydanticAI generations (tagging, newsletters) and OpenRouter
  embeddings. Tokens/model/latency are captured; PostHog derives supported-model costs.
  Unknown-model costs may be absent. Existing Logfire is not replaced.

## Privacy and volume

No AI prompts/completions or embedding text/vectors are sent. Form text/attributes are
masked; query strings are stripped from page/referrer URLs; sensitive account URLs are
collapsed. Search telemetry includes only query presence, allowlisted filter names and
sort values, and a positive safe-integer page number. Unknown parameter names and raw
filter values are not captured by `catalog_browsed`.
Identified users use profile IDs, not email addresses. Session recording is disabled.
Server traces use route names, not request bodies, query strings or credentials. Exported
logs/events redact sensitive property keys, common key formats and email addresses.
PostHog drops IPs. Operational log messages can still contain application-specific data;
keep credentials and personal data out of application log messages at their source.

Logs/spans use bounded asynchronous SDK queues. HTTP traces currently capture all routes;
review volume before enabling broader database or network instrumentation. Telemetry is
not part of business transaction success and should never gate it.

### Discovery shortcut measurement

`discovery_action_clicked` records only a fixed `action` label: `directory_self_hosted`,
`directory_python`, `directory_cli`, `directory_apis`, `directory_checklist`,
`selfhosted_bookmarks`, or `selfhosted_checklist`. It uses the existing delegated click
listener, including keyboard-activated links and content inserted by HTMX. It does not
send the link label, destination URL, query text, or a new persistent identifier.
Links work normally without analytics or JavaScript. Unknown labels and external
destinations do not emit this task event.

For outcome reads, restrict events to the production host and exclude
`telemetry_test=true` plus known QA/bot traffic. Join by the existing session ID with
ordered timestamps: task click, `repository_viewed`, then `github_link_clicked` whose
destination matches that repository. This measures onward exploration, not adoption,
successful installation, or revenue. Ordinary list visits cannot establish which
shortcut was clicked; list-detail pageviews still omit raw search queries. Cross-tab
activity within a session and small samples limit attribution. Do not infer causal
uplift from this observational sequence or mix synthetic checks into its denominator.

## Verification and rollback

Visit `/`, `/repos/`, a repository detail page, and follow a GitHub link. Test HTMX
navigation and check one pageview per URL transition. Confirm events in PostHog and
check web/worker service names in Logs and Tracing. Run one bounded real embedding or
agent call and confirm AI model, usage and latency. Mark synthetic verification events
with `telemetry_test=true`; do not mistake those for real user engagement.

`awesome_repos.telemetry.flush()` flushes queues for short-lived operator smoke commands.
Never deliberately break a live user request just to test error tracking: send a
handled synthetic exception to Sentry from an operator command instead.

To disable export, restore the previous CapRover env snapshot or clear
`POSTHOG_API_KEY` on both apps. To disable only logs/traces/AI, set the corresponding
switch false. Redeploy the previous image if application health regresses.

References: https://posthog.com/docs/logs/installation/python,
https://posthog.com/docs/distributed-tracing/installation/python,
https://posthog.com/docs/ai-observability/installation/pydantic-ai.
