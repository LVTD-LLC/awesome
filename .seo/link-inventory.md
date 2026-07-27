# Awesome — Internal Link Inventory

> Every SEO sprint phase must select links from this inventory and update it when a new page ships.

## Existing pages

### Homepage and core discovery

| Slug | URL | Title / anchor candidate | Used by |
|---|---|---|---|
| `/` | https://awesome.lvtd.dev/ | Find GitHub repositories worth watching | All |
| `/repos/` | https://awesome.lvtd.dev/repos/ | Search awesome repositories | All |
| `/lists/` | https://awesome.lvtd.dev/lists/ | Browse and compare awesome lists | All |
| `/updates/` | https://awesome.lvtd.dev/updates/ | Repository development updates | Use cases, playbooks |
| `/lists/request/` | https://awesome.lvtd.dev/lists/request/ | Request an awesome list | Awesome-list content |
| `/blog/` | https://awesome.lvtd.dev/blog/ | Awesome blog | Playbooks |

### Product capabilities

| Slug | URL | Title | Linked by |
|---|---|---|---|
| `/repos/?sort=stars_growth_7d` | https://awesome.lvtd.dev/repos/?sort=stars_growth_7d | Fast-growing GitHub repositories | Star-growth content |
| `/repos/?sort=commits_growth_7d` | https://awesome.lvtd.dev/repos/?sort=commits_growth_7d | Repositories shipping the most code | Health and momentum content |
| `/starred/` | https://awesome.lvtd.dev/starred/ | Search your starred repositories | Personal discovery content |
| `/api/` | https://awesome.lvtd.dev/api/ | Awesome API | Agent and integration content |
| `/mcp` | https://awesome.lvtd.dev/mcp | Awesome MCP server | Agent and integration content |
| `/uses` | https://awesome.lvtd.dev/uses | Technologies used to build Awesome | Technical/company content |

### Dynamic content families

| Pattern | Example | Link purpose |
|---|---|---|
| `/repos/<owner>/<name>/` | `/repos/django/django/` | Repository facts, stack, activity, list mentions, and related projects |
| `/repos/<owner>/<name>/updates/` | `/repos/django/django/updates/` | Weekly/monthly development summaries and feeds |
| `/lists/<slug>/` | `/lists/awesome-django/` | One curated list’s activity, coverage, and repositories |

## SEO-sprint-generated pages

### `/alternatives/[slug]`

| Slug | Ships in phase | URL | Inbound links from | Outbound links to |
|---|---|---|---|---|
| `github-explore` | 6 | `/alternatives/github-explore/` | Pending | `/repos/`, `/lists/`, `/updates/` |
| `star-history` | 7 | `/alternatives/star-history/` | Pending | Growth search, repository details, `/updates/` |

### `/for/[slug]`

| Slug | Ships in phase | URL | Inbound links from | Outbound links to |
|---|---|---|---|---|
| `github-repository-discovery` | 2 | `/for/github-repository-discovery/` | Pending | `/repos/`, `/lists/`, repository details |
| `github-repository-analytics` | 3 | `/for/github-repository-analytics/` | Pending | Growth searches, repository details, `/updates/` |
| `github-star-tracking` | 4 | `/for/github-star-tracking/` | Pending | Growth search, repository details, update feeds |

### `/playbooks/[slug]`

| Slug | Ships in phase | URL | Inbound links from | Outbound links to |
|---|---|---|---|---|
| `evaluate-open-source-projects` | 5 | `/playbooks/evaluate-open-source-projects/` | Pending | Search, lists, details, updates |

## Anchor-text variations

For `/repos/`:

- search GitHub repositories from awesome lists
- browse the repository catalog
- filter maintained open-source projects
- compare indexed GitHub projects

For `/lists/`:

- browse curated awesome lists
- compare active awesome lists
- search the awesome-list directory
- find topic-specific GitHub lists

For `/updates/`:

- follow repository development updates
- monitor weekly GitHub activity
- read recent project changes
- subscribe to repository updates
