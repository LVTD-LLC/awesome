# Awesome - Internal Link Inventory

> Pre-populated list of every URL the SEO sprint can link to. Each pattern phase must pick links from this inventory and update this file when it ships a new page.

## Existing Pages

### Homepage And Core Marketing

| Slug | URL | Title (anchor-text candidate) | Used by patterns |
|---|---|---|---|
| `/` | https://awesome.lvtd.dev/ | Search Awesome repositories | All |
| `/lists/` | https://awesome.lvtd.dev/lists/ | Awesome Lists Directory | B, C, E |
| `/lists/request/` | https://awesome.lvtd.dev/lists/request/ | Request an awesome list | B, C, E |
| `/blog/` | https://awesome.lvtd.dev/blog/ | Awesome blog | E |
| `/uses` | https://awesome.lvtd.dev/uses | Technologies We Use | occasional |
| `/privacy-policy` | https://awesome.lvtd.dev/privacy-policy | Privacy Policy | trust/footer |
| `/terms-of-service` | https://awesome.lvtd.dev/terms-of-service | Terms of Service | trust/footer |

Note: `/uses` intentionally omits a trailing slash because the current Django route is
`path("uses", ...)`; production `/uses` returns 200 while `/uses/` returned 500 on
2026-06-17. If Phase 0 canonicalizes that route to a trailing slash, update this row.

### Features

| Slug | URL | Title | Linked by |
|---|---|---|---|
| `/` | https://awesome.lvtd.dev/ | Repository search with filters | B, C, D, E |
| `/lists/` | https://awesome.lvtd.dev/lists/ | Browse indexed awesome lists | B, C, E |
| `/lists/request/` | https://awesome.lvtd.dev/lists/request/ | Request a GitHub awesome list | B, E |
| `/api/` | https://awesome.lvtd.dev/api/ | Awesome API | C, E |
| `/mcp` | https://awesome.lvtd.dev/mcp | Public MCP endpoint | C, E |
| `/repos/<owner>/<name>/` | dynamic | Repository detail pages | B, C, E |
| `/lists/<slug>/` | dynamic | Awesome-list detail pages | B, C, E |
| `/repos/<owner>/<name>/newsletters/` | dynamic | Repository newsletter archives | B, E |

### Tools And Free Utilities

| Slug | URL | Title | Linked by |
|---|---|---|---|
| `/` | https://awesome.lvtd.dev/ | GitHub repository search tool | B, C, D, E |
| `/lists/` | https://awesome.lvtd.dev/lists/ | Awesome-list browser | B, C, E |
| `/mcp` | https://awesome.lvtd.dev/mcp | MCP repository-search integration | C, E |

### Blog Posts

| Slug | URL | Title | Topic | Linked by |
|---|---|---|---|---|
| `/blog/` | https://awesome.lvtd.dev/blog/ | Blog index | Existing blog posts are database-backed | E |

## SEO-Sprint-Generated Pages

### `/alternatives/[slug]`

| Slug | Ships in phase | URL | Inbound links from | Outbound links to |
|---|---|---|---|---|
| `github-topics` | 5 | `/alternatives/github-topics/` | TBD | `/`, `/lists/`, sibling alternatives |
| `github-trending` | 6 | `/alternatives/github-trending/` | TBD | `/`, `/lists/`, sibling alternatives |
| `libraries-io` | 7 | `/alternatives/libraries-io/` | TBD | `/`, `/lists/`, sibling alternatives |
| `ossinsight` | 12 | `/alternatives/ossinsight/` | TBD | `/`, `/lists/`, sibling alternatives |
| `ecosyste-ms` | 13 | `/alternatives/ecosyste-ms/` | TBD | `/`, `/api/`, sibling alternatives |
| `openalternative` | 14 | `/alternatives/openalternative/` | TBD | `/`, `/lists/`, sibling alternatives |

### `/for/[slug]`

| Slug | Ships in phase | URL | Inbound links from | Outbound links to |
|---|---|---|---|---|
| `find-maintained-open-source-projects` | 1 | `/for/find-maintained-open-source-projects/` | TBD | `/`, `/lists/`, `/blog/` |
| `search-awesome-lists` | 2 | `/for/search-awesome-lists/` | TBD | `/`, `/lists/`, `/lists/request/` |
| `github-repository-search` | 3 | `/for/github-repository-search/` | TBD | `/`, `/lists/`, `/api/` |
| `find-github-repositories-by-topic` | 8 | `/for/find-github-repositories-by-topic/` | TBD | `/`, `/lists/`, dynamic topic/search pages |
| `developers` | 9 | `/for/developers/` | TBD | `/`, `/lists/`, `/blog/` |
| `repository-monitoring` | 10 | `/for/repository-monitoring/` | TBD | `/`, dynamic repository newsletter pages |
| `mcp-github-repository-search` | 11 | `/for/mcp-github-repository-search/` | TBD | `/mcp`, `/api/`, `/` |

### `/compare/[slug]`

| Slug | Ships in phase | URL | Inbound links from | Outbound links to |
|---|---|---|---|---|
| `libraries-io-vs-github-topics` | 15 | `/compare/libraries-io-vs-github-topics/` | TBD | related alternatives, `/`, `/lists/` |
| `oss-insight-vs-github-trending` | 16 | `/compare/oss-insight-vs-github-trending/` | TBD | related alternatives, `/`, `/lists/` |

### `/playbooks/[slug]`

| Slug | Ships in phase | URL | Inbound links from | Outbound links to |
|---|---|---|---|---|
| `evaluate-github-repository` | 4 | `/playbooks/evaluate-github-repository/` | TBD | `/`, `/lists/`, repository examples |
| `use-awesome-lists-for-tool-discovery` | 17 | `/playbooks/use-awesome-lists-for-tool-discovery/` | TBD | `/`, `/lists/`, `/lists/request/` |
| `choose-open-source-dependency` | 18 | `/playbooks/choose-open-source-dependency/` | TBD | `/`, repository examples, `/blog/` |

## Anchor-Text Variations

Use these to avoid repeating one exact anchor everywhere.

### Homepage/Search

- search GitHub repositories from awesome lists
- filter repositories by freshness and cross-list signal
- explore indexed awesome-list repositories
- find maintained open-source projects
- compare GitHub repositories before adopting one

### Awesome-List Directory

- browse tracked awesome lists
- inspect indexed awesome-list sources
- find repositories from curated GitHub lists
- explore awesome lists by coverage and freshness

### Request A List

- request another awesome list
- submit a GitHub awesome-list source
- add a missing awesome list to the catalog

### API And MCP

- query the Awesome catalog through the API
- use the public MCP endpoint
- connect agents to repository search
- expose awesome-list repository data to tools
