# Browse Awesome product truth

Verified from current main on 2026-10-08. Recheck when product behavior changes.

- Public catalog discovery is free and does not require an account: README.md, apps/repos/urls.py and views.py.
- Awesome-list search supports names, descriptions, owners and topics; sorting includes stars, indexed links, README counts, commits and scan/push dates: apps/repos/search_services.py.
- Indexed repositories are not guaranteed safe, maintained or suitable for production; evaluate their upstream documentation and license independently. No security-audit claim.
- Public canonical origin is https://browseawesome.com; July research for awesome.lvtd.dev is historical, not a current baseline.
- Error pages must return 404/noindex and must not require catalog/account/sponsor queries: apps/pages/error_views.py and test_error_pages.py.
- IndexNow acceptance is notification delivery, never proof of indexing.

MCP claims reverified October 13, 2026 UTC against revision 0f1e49c and live tool calls:

- `/mcp` is public, read-only Streamable HTTP without authentication; it searches the Browse Awesome index, not all GitHub.
- List-scoped repository search requires `slug`; global repository search uses optional `list`. Search results expose pagination; use `has_next`, since out-of-range pages can resolve to the last page.
- `get_repository` takes `full_name`; README text is opt-in and bounded, with explicit truncation when applicable. Repository, README, list-scan and stored GitHub push timestamps describe different observations.
- Catalog matches, upstream documentation and locally tested behavior are distinct evidence levels. No installation, security or production-readiness claim follows from discovery.

Archive-status claim reverified October 15, 2026 UTC:

- `Repository.is_archived` stores GitHub's archive flag, not a maintenance
  assessment. A false flag cannot substantiate “Actively maintained.”
- `last_synced_at` is nullable and `is_archived` defaults to false. When no sync
  is recorded, the detail header and metadata must say the status is not checked.
- Source: `apps/repos/models.py`, repository metadata sync, and GitHub's
  [archiving documentation](https://docs.github.com/en/repositories/archiving-a-github-repository/archiving-repositories).
  Verify upstream releases, issue responses and project fit independently.
