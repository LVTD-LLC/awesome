# Awesome SEO Sprint - Roadmap

> **Canonical document.** This file is the source of truth for the multi-phase SEO sprint. Every agent or worktree picking up SEO work on this project should read this file first.

## Manual Research Mode

Ahrefs MCP was not available during initialization on 2026-06-17. This roadmap uses manual web research and repository context. Treat every volume, KD, and traffic-potential value as an estimate until `.seo/keyword-research.json` is refreshed from Ahrefs, Semrush, Google Keyword Planner, or Google Search Console.

Until Domain Rating is measured, assume the domain has limited authority for new SEO surfaces. Prefer long-tail, high-fit pages before head terms.

## How To Use This Document

1. Read this entire `docs/seo-sprint.md` file.
2. Read `AGENTS.md`, `.seo/brand.md`, `.seo/link-inventory.md`, `.seo/config.json`, and `.seo/keyword-research.json`.
3. Find the next `pending` phase in the Phase Status Tracker.
4. Read the phase section. It is intentionally self-contained.
5. Execute only that phase, verify the quality gate, and update the tracker row in the same branch as the work.
6. Do not auto-commit unless the user asks.

Do not modify Reference Data, Conventions, or Keyword Research Appendix without explicit instruction. They are shared contracts for the sprint.

## Phase Status Tracker

| # | Phase | Pattern | Status | PR |
|---|---|---|---|---|
| 0 | Technical foundations and Django SEO renderer | Setup | pending | - |
| 1 | Ship `/for/find-maintained-open-source-projects/` | B - use case | pending | - |
| 2 | Ship `/for/search-awesome-lists/` | B - use case | pending | - |
| 3 | Ship `/for/github-repository-search/` | B - use case | pending | - |
| 4 | Ship `/playbooks/evaluate-github-repository/` | E - playbook | pending | - |
| 5 | Ship `/alternatives/github-topics/` | A - alternatives | pending | - |
| 6 | Ship `/alternatives/github-trending/` | A - alternatives | pending | - |
| 7 | Ship `/alternatives/libraries-io/` | A - alternatives | pending | - |
| 8 | Ship `/for/find-github-repositories-by-topic/` | B - use case | pending | - |
| 9 | Ship `/for/developers/` | C - audience | pending | - |
| 10 | Ship `/for/repository-monitoring/` | B - use case | pending | - |
| 11 | Ship `/for/mcp-github-repository-search/` | C - audience/use case | pending | - |
| 12 | Ship `/alternatives/ossinsight/` | A - alternatives | pending | - |
| 13 | Ship `/alternatives/ecosyste-ms/` | A - alternatives | pending | - |
| 14 | Ship `/alternatives/openalternative/` | A - alternatives | pending | - |
| 15 | Ship `/compare/libraries-io-vs-github-topics/` | D - compare | pending | - |
| 16 | Ship `/compare/oss-insight-vs-github-trending/` | D - compare | pending | - |
| 17 | Ship `/playbooks/use-awesome-lists-for-tool-discovery/` | E - playbook | pending | - |
| 18 | Ship `/playbooks/choose-open-source-dependency/` | E - playbook | pending | - |
| 19 | Off-page: directory and community submissions | Off-page | pending | - |
| 20 | Refresh keyword data with Ahrefs/GSC | Research | pending | - |

**Conventions:**
- `pending` -> `in_progress` -> `completed`.
- PR column should become `branch <name> (PR TBD)` while active, then `#NNN` after PR creation.
- If a phase is abandoned, status becomes `skipped` with a one-line reason.

## Reference Data

### Site Facts

- **Domain:** https://awesome.lvtd.dev
- **Ahrefs project_id:** null
- **Domain Rating:** unknown as of 2026-06-17
- **KD cap:** use low-tail and low/medium-competition terms until DR is measured.
- **Stack:** Django 6, server-rendered Django templates, Tailwind CSS 4 CLI, HTMX, Alpine.js.
- **Routing:** URLConf/controller-based.
- **Brand accent color:** #15803D primary, #2563EB accent.
- **Hero/body font:** Inter, ui-sans-serif, system-ui, sans-serif.
- **Marketing pages root:** `apps/pages`, `apps/repos`, `apps/blog`, and `frontend/templates`.

### Existing Programmatic Surface

| Surface | URL pattern | Backing code | SEO notes |
|---|---|---|---|
| Repository search/homepage | `/` | `apps/repos/views.py`, `frontend/templates/repos/search.html` | Has unique title, description, canonical, WebSite schema from base layout. |
| Repository detail | `/repos/<owner>/<name>/` | `apps/repos/views.py`, `frontend/templates/repos/detail.html` | Has page-specific metadata and `SoftwareSourceCode` JSON-LD. |
| Awesome-list directory | `/lists/` | `apps/repos/views.py`, `frontend/templates/repos/lists.html` | Listed in sitemap. Strong internal link target. |
| Awesome-list detail | `/lists/<slug>/` | `apps/repos/views.py`, `frontend/templates/repos/list_detail.html` | Has page-specific metadata and `CollectionPage` JSON-LD. |
| Blog index/detail | `/blog/`, `/blog/<slug>/` | `apps/blog/views.py`, `frontend/templates/blog/` | Blog detail has `BlogPosting` JSON-LD. |
| Repository newsletters | `/repos/<owner>/<name>/newsletters/` | `apps/repos/views.py`, `frontend/templates/repos/newsletter_*` | Useful for repository monitoring intent. |
| Public MCP endpoint | `/mcp` | `apps/mcp_server` | Good high-intent link target for AI-agent pages. |
| API | `/api/` | `apps/api` | Good link target for integration pages. |

### Critical Files

| File | What lives there |
|---|---|
| `awesome_repos/urls.py` | Top-level routing, dynamic `robots.txt`, sitemap route. |
| `awesome_repos/sitemaps.py` | Django sitemap classes for static pages, repositories, awesome lists, and blog posts. |
| `apps/repos/urls.py` | Public repository/list/newsletter URL patterns. |
| `apps/repos/views.py` | Search, repository detail, awesome-list, request-list, and newsletter views. |
| `apps/pages/views.py` | Landing/legal/signup page views. |
| `apps/blog/views.py` | Blog list/detail views. |
| `frontend/templates/components/seo_meta.html` | Shared title, description, canonical, OpenGraph, and Twitter metadata include. |
| `frontend/templates/base_landing.html` | Public layout and default WebSite JSON-LD. |
| `frontend/templates/base_app.html` | App layout and default WebSite JSON-LD. |
| `frontend/templates/repos/detail.html` | Repository page schema and metadata integration. |
| `frontend/templates/repos/list_detail.html` | Awesome-list page schema and metadata integration. |
| `apps/repos/tests/test_seo.py` | Existing SEO tests for metadata, robots, sitemap, and schema. |
| `.seo/brand.md` | Brand, audience, competitors, voice, anti-positioning. |
| `.seo/link-inventory.md` | Internal link targets for every phase. |
| `.seo/keyword-research.json` | Manual-mode keyword cache. |

### Technical Audit Snapshot

Checks performed on 2026-06-17:

| Check | Result | Notes |
|---|---|---|
| Production domain | pass | `https://awesome.lvtd.dev/` returned 200. |
| Robots | pass | `https://awesome.lvtd.dev/robots.txt` returns `Allow: /` and advertises the sitemap. |
| Sitemap | pass with follow-up | `https://awesome.lvtd.dev/sitemap.xml` returns 200 and includes static pages plus repository/list URLs with `lastmod`. Full parse timed out because the sitemap is large; Phase 0 should add a bounded verifier. |
| Homepage meta | pass | Title, description, canonical, and one H1 are present. |
| Homepage schema | partial | Current schema is `WebSite` plus `Organization` and `SearchAction`; add `SoftwareApplication` or `WebApplication` for product SEO. |
| Native SEO page renderer | missing | No `/alternatives/*`, `/for/*`, `/compare/*`, or `/playbooks/*` route surface exists yet. |

### Conventions

**URL slugs:** lowercase, hyphenated, never underscored.

**Django implementation:** Prefer a small Django-native SEO surface over leaving markdown orphaned. The skill's markdown fallback can be used as a data shape, but Phase 0 should add routes/templates/sitemaps/tests that render content as real HTML.

**Honesty section:** Required on every `/alternatives/[brand]` page. Include 3-4 honest tradeoffs where the competitor wins.

**Plural-form capture:** Every alternative page's first major comparison section should use "Best [Brand] alternatives in [CURRENT_YEAR]". Substitute the four-digit year at page-generation time.

**Internal-link minimums per page:**
- `/alternatives/*`: at least 2 sibling alternatives, 1 feature, and 1 tool.
- `/for/*`: at least 2 features/tools and 1 sibling `/for/` page.
- `/compare/*`: both related alternative pages, 1 `/for/` page, and the homepage/search page.
- `/playbooks/*`: at least 3 product surfaces, 2 `/for/` pages, and 1 alternative page.
- Every new page should be reachable from at least 2 other pages after the relevant sibling pages exist.

**Word counts:**
- `/alternatives/*`: at least 600 words.
- `/for/*`: at least 800 words.
- `/compare/*`: at least 700 words.
- `/playbooks/*`: at least 2,500 words.

**Schema:**
- Homepage/search: `WebSite`, `Organization`, `SearchAction`, plus `WebApplication` or `SoftwareApplication`.
- `/alternatives/*`: `SoftwareApplication` or `WebApplication`, `BreadcrumbList`, `FAQPage`.
- `/for/*`: `SoftwareApplication` or `WebApplication`, `BreadcrumbList`, `FAQPage`.
- `/compare/*`: `BreadcrumbList`, `FAQPage`.
- `/playbooks/*`: `Article`, `BreadcrumbList`.

## Keyword Research Appendix

All numbers are estimates. Refresh before building more than one or two pages.

### A.1 - `/alternatives/[brand]` Candidates

| Candidate | Target keyword | Volume range | KD estimate | Confidence | Notes |
|---|---|---:|---|---|---|
| GitHub Topics/Search | GitHub Topics alternative | 30-150 | high | estimated | Head competitor; wait until stronger internal page spine exists. |
| GitHub Trending | GitHub Trending alternative | 30-150 | high | estimated | Strong discovery intent, but official GitHub SERP competition. |
| Libraries.io | Libraries.io alternative | 10-100 | medium | estimated | Best package-discovery adjacent competitor. |
| OSS Insight | OSS Insight alternative | 10-100 | medium | estimated | Good analytics/trend angle. |
| ecosyste.ms | ecosyste.ms alternative | 0-50 | medium | estimated | Data/API audience, likely low volume. |
| OpenAlternative | OpenAlternative alternative | 0-50 | low | estimated | More product-alternative than repository-discovery intent. |

### A.2 - `/for/[use-case]` Candidates

| Candidate | Target keyword | Volume range | KD estimate | Confidence | Notes |
|---|---|---:|---|---|---|
| Find maintained OSS projects | find maintained open source projects | 50-300 | low-medium | medium | Best first use-case page; maps directly to freshness/archive filters. |
| Search awesome lists | search awesome lists | 30-150 | low-medium | medium | Highest-fit phrase for the current catalog. |
| GitHub repository search | GitHub repository search | 500-2000 | high | estimated | Use a long-tail awesome-list angle, not a generic head-term page. |
| Find GitHub repositories by topic | find GitHub repositories by topic | 50-300 | medium | estimated | Maps to topics, generated tags, languages, and stack filters. |
| Repository monitoring | GitHub repository monitoring | 50-300 | medium | estimated | Tie to freshness, history, newsletters, and rescan workflows. |

### A.3 - `/for/[audience]` Candidates

| Candidate | Target keyword | Volume range | KD estimate | Confidence | Notes |
|---|---|---:|---|---|---|
| Developers | open source discovery for developers | 30-150 | low-medium | estimated | Good persona bridge. |
| AI agents/MCP builders | MCP server for GitHub repository search | 0-100 | low | estimated | Emerging query with high product fit because Awesome exposes `/mcp`. |

### A.4 - `/compare/[a-vs-b]` Candidates

| Candidate | Target keyword | Volume range | KD estimate | Confidence | Notes |
|---|---|---:|---|---|---|
| Libraries.io vs GitHub Topics | Libraries.io vs GitHub Topics | 0-50 | low | estimated | Shows package metadata vs broad GitHub discovery vs awesome-list cross-signal. |
| OSS Insight vs GitHub Trending | OSS Insight vs GitHub Trending | 0-50 | low | estimated | Useful for analytics/trend intent. |

### A.5 - `/playbooks/[topic]` Candidates

| Candidate | Target keyword | Volume range | KD estimate | Confidence | Notes |
|---|---|---:|---|---|---|
| Evaluate GitHub repository | how to evaluate a GitHub repository | 50-300 | low-medium | medium | Strong editorial page that can link into product filters. |
| Use awesome lists for tool discovery | how to use awesome lists | 50-300 | medium | estimated | Educational angle with natural links to `/lists/`. |
| Choose open-source dependency | how to choose an open source dependency | 50-300 | medium | estimated | Maps to freshness, archive status, stack detection, and similar repos. |

### A.6 - Striking Distance

No GSC data was available during initialization. Add rows here after exporting Search Console queries in positions 5-20.

| Query | Current URL | Position | Clicks | Impressions | Action |
|---|---|---:|---:|---:|---|
| - | - | - | - | - | Paste GSC export before running a boost phase. |

### A.7 - Already-Saturated Head Terms

| Keyword | Reason |
|---|---|
| GitHub | Navigational head term owned by GitHub. |
| open source | Extremely broad SERP with high-authority publishers. |
| open source software | Broad informational query; not a good first target. |
| GitHub search | Official GitHub product query. |
| best GitHub repositories | Listicle-heavy and too broad without a category modifier. |
| software alternatives | Too broad; target precise open-source/developer-tool modifiers instead. |

### A.8 - Out Of Scope

| Keyword | Reason |
|---|---|
| GitHub alternatives | Awesome is not a Git hosting or DevOps platform. |
| GitHub security scanner | Awesome surfaces repository signals but is not a security scanner. |
| package vulnerability database | Not the current product category. |

## Phases

Each phase should be one deployable PR unless the user asks for a different cadence.

### Phase 0 - Technical Foundations And Django SEO Renderer

**Why:** The existing foundation is solid, but new programmatic pages need real Django routes, sitemap support, reusable schema, and tests before content phases ship.

**Scope:**

1. Add a Django-native SEO content surface for `/alternatives/<slug>/`, `/for/<slug>/`, `/compare/<slug>/`, and `/playbooks/<slug>/`.
2. Store page payloads in a small structured layer. Prefer a repo-local data module or markdown/frontmatter reader with validation; keep business logic out of templates.
3. Add reusable schema helpers/includes for `WebApplication` or `SoftwareApplication`, `FAQPage`, `BreadcrumbList`, and `Article`.
4. Add `WebApplication` or `SoftwareApplication` JSON-LD to the homepage/search page while preserving existing `WebSite`/`SearchAction`.
5. Include generated SEO pages in `awesome_repos/sitemaps.py`.
6. Add tests in `apps/repos/tests/test_seo.py` or a new focused SEO test module for route status, metadata, H1 count, canonical, schema, robots, and sitemap inclusion.
7. Add a bounded sitemap verifier command or test helper so the full production sitemap can be checked without hanging on a large response.

**Files likely modified:**

- `awesome_repos/urls.py`
- `awesome_repos/sitemaps.py`
- `apps/pages/views.py` or a new `apps/seo/`
- `frontend/templates/components/seo_meta.html`
- `frontend/templates/base_landing.html`
- new `frontend/templates/seo/*.html`
- `apps/repos/tests/test_seo.py` or new SEO tests

**Verification:**

- [ ] `uv run python manage.py check`
- [ ] `uv run pytest apps/repos/tests/test_seo.py -q`
- [ ] `/robots.txt` still allows crawling and advertises sitemap.
- [ ] `/sitemap.xml` includes the first SEO test page when content exists.
- [ ] Homepage has exactly one H1 and valid `WebSite` plus product schema.

### Phase 1 - Ship `/for/find-maintained-open-source-projects/`

**Target:** `find maintained open source projects` (estimated 50-300 volume, low-medium KD).

**Angle:** Show how Awesome helps users avoid stale, archived, or one-off recommendations by combining awesome-list curation with GitHub freshness signals.

**Required sections:** problem framing, why maintenance signals matter, product workflow, example filters, FAQ, CTA to `/`.

**Internal links:** `/`, `/lists/`, `/blog/`, one example repository page if stable fixture data exists.

**Verification:** At least 800 words, unique meta title/description, one H1, FAQPage schema, included in sitemap, at least 3 internal links.

### Phase 2 - Ship `/for/search-awesome-lists/`

**Target:** `search awesome lists` (estimated 30-150 volume, low-medium KD).

**Angle:** Position Awesome as a search surface over many curated GitHub awesome-list READMEs, not another static list.

**Internal links:** `/`, `/lists/`, `/lists/request/`, Phase 1 page.

**Verification:** At least 800 words, FAQPage schema, links to at least two list/repository examples where possible.

### Phase 3 - Ship `/for/github-repository-search/`

**Target:** `GitHub repository search` (estimated 500-2000 volume, high KD).

**Angle:** Do not claim to replace GitHub search. Focus on repository search for awesome-list-curated projects with freshness, stack, and cross-list filters.

**Internal links:** `/`, `/lists/`, `/api/`, Phase 1 and Phase 2.

**Verification:** At least 800 words, honesty/tradeoff section explaining where GitHub search wins, FAQPage schema.

### Phase 4 - Ship `/playbooks/evaluate-github-repository/`

**Target:** `how to evaluate a GitHub repository` (estimated 50-300 volume, low-medium KD).

**Angle:** A practical checklist for adoption decisions: freshness, releases, issues, archive state, language, license, list mentions, and stack/dependency signals.

**Internal links:** `/`, `/lists/`, repository examples, Phase 1, Phase 3.

**Verification:** At least 2,500 words, Article schema, no generic filler, concrete product screenshots or examples if available.

### Phase 5 - Ship `/alternatives/github-topics/`

**Target:** `GitHub Topics alternative` (estimated 30-150 volume, high KD).

**Angle:** Awesome is not a GitHub replacement; it is a narrower discovery layer for repositories that appear in curated awesome lists.

**Honesty rows:** GitHub has broader coverage, first-party data, and native repository UX.

**Internal links:** `/`, `/lists/`, Phase 1, Phase 2, at least two sibling alternatives once available.

**Verification:** At least 600 words, a "Best GitHub Topics alternatives in [CURRENT_YEAR]" section with the current four-digit year substituted at page-generation time, 3-4 honesty rows, FAQPage schema.

### Phase 6 - Ship `/alternatives/github-trending/`

**Target:** `GitHub Trending alternative` (estimated 30-150 volume, high KD).

**Angle:** GitHub Trending is great for daily momentum; Awesome is better for curated-list context and maintained project discovery.

**Verification:** Same alternative-page quality gate.

### Phase 7 - Ship `/alternatives/libraries-io/`

**Target:** `Libraries.io alternative` (estimated 10-100 volume, medium KD).

**Angle:** Libraries.io is package/dependency centered; Awesome is repository/list centered.

**Verification:** Same alternative-page quality gate.

### Phase 8 - Ship `/for/find-github-repositories-by-topic/`

**Target:** `find GitHub repositories by topic` (estimated 50-300 volume, medium KD).

**Angle:** Use topics, generated tags, language, stack, and awesome-list context to narrow discovery.

**Verification:** At least 800 words, FAQPage schema, links to search/list examples.

### Phase 9 - Ship `/for/developers/`

**Target:** `open source discovery for developers` (estimated 30-150 volume, low-medium KD).

**Angle:** Persona page for developers choosing libraries/tools without manually reading many READMEs.

**Verification:** At least 800 words, links to use-case pages and core surfaces.

### Phase 10 - Ship `/for/repository-monitoring/`

**Target:** `GitHub repository monitoring` (estimated 50-300 volume, medium KD).

**Angle:** Repository history, newsletters, freshness signals, archive state, and rescans.

**Verification:** At least 800 words, link to repository newsletter examples if public and stable.

### Phase 11 - Ship `/for/mcp-github-repository-search/`

**Target:** `MCP server for GitHub repository search` (estimated 0-100 volume, low KD).

**Angle:** High-intent AI-agent workflow page around the public `/mcp` endpoint and catalog search tools.

**Verification:** At least 800 words, include setup guidance only if it matches current product behavior, FAQPage schema.

### Phases 12-14 - Additional Alternative Pages

Run one page per phase:

| Phase | Page | Target | Positioning |
|---|---|---|---|
| 12 | `/alternatives/ossinsight/` | OSS Insight alternative | Awesome is repository discovery from curated lists; OSS Insight is GitHub event analytics. |
| 13 | `/alternatives/ecosyste-ms/` | ecosyste.ms alternative | Awesome is a productized discovery surface; ecosyste.ms is a broad open data/API ecosystem. |
| 14 | `/alternatives/openalternative/` | OpenAlternative alternative | Awesome is for GitHub repository evaluation; OpenAlternative is for replacing proprietary products. |

Each page must include the required honesty section and FAQ schema.

### Phases 15-16 - Comparison Pages

Run one comparison per phase:

| Phase | Page | Target | Notes |
|---|---|---|---|
| 15 | `/compare/libraries-io-vs-github-topics/` | Libraries.io vs GitHub Topics | Use Awesome as the third path: package metadata vs broad GitHub discovery vs awesome-list cross-signal. |
| 16 | `/compare/oss-insight-vs-github-trending/` | OSS Insight vs GitHub Trending | Analytics/trends vs daily popularity vs curated-list repository discovery. |

Each page must link to both related alternatives plus at least one `/for/` page and the homepage/search page.

### Phases 17-18 - Playbooks

| Phase | Page | Target | Notes |
|---|---|---|---|
| 17 | `/playbooks/use-awesome-lists-for-tool-discovery/` | how to use awesome lists | Explain the manual workflow, where it breaks, and how Awesome improves it. |
| 18 | `/playbooks/choose-open-source-dependency/` | how to choose an open source dependency | Use practical selection criteria; avoid pretending Awesome is a security scanner. |

Each playbook must be at least 2,500 words, use `Article` schema, and link to relevant product surfaces.

### Phase 19 - Off-Page Directory And Community Submissions

**Scope:**

1. Submit or update Awesome on directories where it fits: Product Hunt, Indie Hackers, AlternativeTo, OpenAlternative or similar, SaaSHub if appropriate, GitHub repository README, and relevant awesome-list/meta-list communities.
2. Add a small backlink target list to `.seo/backlink-targets.json` if outreach begins.
3. Track submission URLs and statuses in this section.

**Verification:**

- [ ] Every submission has URL, date, status, and owner.
- [ ] No paid placement claims or inflated positioning.

### Phase 20 - Refresh Keyword Data

Run after Ahrefs/Semrush/GSC access is available.

**Required imports:**

- Domain Rating or comparable authority score.
- GSC queries in positions 5-20.
- Competitor organic keyword exports for GitHub Topics/Search, GitHub Trending, Libraries.io, ecosyste.ms, OSS Insight, OpenAlternative.
- Volume/KD/traffic potential for each planned page.

**Output:** update `.seo/keyword-research.json`, this appendix, and the tracker ordering if the data changes the priority.

## Off-Page Checklist

### Directory Submissions

- [ ] Product Hunt - schedule launch or update existing listing.
- [ ] Indie Hackers - submit founder/product note if appropriate.
- [ ] AlternativeTo - only if Awesome can be listed honestly as an alternative to a discovery product.
- [ ] OpenAlternative/Open Source Alternatives directories - submit only if category fit is real.
- [ ] SaaSHub - evaluate fit first; avoid low-quality listings.
- [ ] GitHub repository topics and README - ensure repo metadata supports search intent.

### Community And List Outreach

- [ ] Ask maintainers of meta awesome-list resources whether Awesome can be listed as a search/indexing tool.
- [ ] Share with developer communities only after Phase 1-3 pages exist and are useful.
- [ ] Build a backlink target list from pages that already discuss "how to find open source projects" and "awesome lists".

## Review Notes

Items to confirm with the product owner before running many content phases:

1. Production domain is assumed to be `https://awesome.lvtd.dev`.
2. Competitor set is inferred, not owner-approved.
3. Product is treated as free and open source because README says so and no pricing page exists.
4. No Ahrefs/GSC data was available, so all search numbers are estimates.
