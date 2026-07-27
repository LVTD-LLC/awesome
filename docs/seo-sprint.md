# Awesome SEO Sprint — Roadmap

> **Canonical document.** This is the source of truth for Awesome's multi-phase SEO sprint. Every phase reads this file, `.seo/brand.md`, `.seo/link-inventory.md`, and `.seo/config.json` before starting.

## How to use this document

1. Find the lowest-numbered `pending` phase.
2. Re-check live SERPs and metrics when the cached data is more than 30 days old.
3. Mark the row `in_progress` on the phase branch.
4. Ship one deployable PR with tests, a `CHANGELOG.md` entry, link-inventory updates, and this tracker update.
5. Do not merge until CI and the repository review gates pass.

The current authority baseline is weak (DataForSEO rank 236 and six referring domains), so the default target cap is **KD ≤30**. Terms above that cap require a fresh authority/SERP check before work begins.

## Phase Status Tracker

| # | Phase | Pattern | Evidence | Status | PR |
|---|---|---|---|---|---|
| 0 | Technical foundations and measurement | Setup | 16,683-URL sitemap timed out the 10s audit; GSC has no submitted sitemap rows | pending | – |
| 1 | Strengthen `/lists/` for the awesome-lists cluster | Existing-page boost | “awesome lists” vol 210, KD 17; “github awesome list” vol 140, KD 22 | pending | – |
| 2 | Ship `/for/github-repository-discovery/` | Use case | “best github repositories” vol 210, KD 14, CPC $11.80 | pending | – |
| 3 | Ship `/for/github-repository-analytics/` | Use case | “github repo analytics” vol 20, KD 11, CPC $30.69 | pending | – |
| 4 | Ship `/for/github-star-tracking/` | Use case | “github stars tracker” vol 170, KD 36, CPC $46.75; re-check required | pending | – |
| 5 | Publish the open-source evaluation playbook | Playbook | Strong product/link fit; query phrasing still derived | pending | – |
| 6 | Ship an honest GitHub Explore alternative page | Alternative | Strategic positioning; measured query demand unavailable | pending | – |
| 7 | Ship an honest Star History alternative page | Alternative | Supports star-tracking cluster; measured query demand unavailable | pending | – |
| 8 | Audit the internal-link spine | Internal links | New pages must receive at least two contextual inbound links | pending | – |
| 9 | Directory and ecosystem outreach | Off-page | 14 backlinks from 6 referring domains | pending | – |

## Reference Data

### Site facts

- **Domain:** https://awesome.lvtd.dev
- **Stack:** Django 6, server-rendered Django templates, Tailwind, and Markdown-backed blog posts
- **Keyword source:** DataForSEO, with direct GSC for owned search truth
- **Analytics:** Plausible connected; PostHog project access unavailable to the connected management account
- **Authority:** DataForSEO domain rank 236, 14 backlinks, 6 referring domains
- **Current organic visibility:** one DataForSEO ranking keyword; GSC contains three impressions and no clicks in the available 90-day window
- **90-day Plausible baseline:** 794 visitors, 846 visits, 1,913 pageviews; Organic Search contributed 33 visitors and 152 pageviews
- **Brand accent:** `#15803D`
- **Typography:** Inter/system sans-serif
- **Marketing roots:** `apps/pages`, `apps/repos`, `frontend/templates`, `apps/blog/posts`

### Tool evidence snapshot

| Source | Status | Credential/config evidence | API/tool call evidence | Used for | Config saved | Reason |
|---|---|---|---|---|---|---|
| GSC | connected | Infisical service credential | Property, 90-day rows, sitemaps queried | Owned queries and indexing | `gsc_property` | Full-user access; data is sparse |
| Ahrefs | missing | Tools, env, TOOLS.md, repo, Infisical checked | No call possible | DR/Ahrefs data | `null` | No usable connection; DataForSEO used |
| DataForSEO | connected | Infisical service credentials | Keywords, SERPs, ranks, backlinks queried | Volume, KD, CPC, SERP, authority proxy | location/language | Measured market source |
| Plausible | connected | Runtime key + TOOLS.md | Traffic, channel, page, event queries succeeded | Landing-page and engagement value | `awesome.lvtd.dev` | 90-day measured baseline |
| PostHog | attempted_failed | Runtime management key | Projects listed; Awesome absent | Funnel/revenue events | `null` | Account lacks an accessible Awesome project |
| SearXNG/Exa | connected | Exa runtime key + TOOLS.md | Competitor/category discovery succeeded | Discovery | none | Fresh market/source finding |
| Firecrawl/Jina/WebFetch | connected | Runtime keys + OpenClaw tool | All three extraction routes succeeded | Live page verification | none | Competitor and product extraction |

Detailed evidence is stored in `.seo/config.json`. Raw and curated metrics are stored in `.seo/keyword-research.json`.

### Existing programmatic surface

| Surface | Pattern | Scale | SEO status |
|---|---|---|---|
| `/repos/<owner>/<name>/` | Repository detail | Thousands | Unique metadata, canonical, and `SoftwareSourceCode` schema |
| `/lists/<slug>/` | Awesome-list detail | Hundreds | Unique metadata, canonical, and `CollectionPage` schema |
| `/repos/<owner>/<name>/updates/` | Repository update index | Growing | Unique metadata, canonical, and `CollectionPage` schema |
| `/repos/<owner>/<name>/updates/<cadence>/<slug>/` | Update article | Growing | Unique metadata, canonical, and `Article` schema |
| `/blog/<slug>/` | Markdown article | Empty at initialization | Article metadata/schema pipeline exists |

### Critical files

| File | What lives there |
|---|---|
| `awesome_repos/sitemaps.py` | Static, repository, list, blog, and update sitemap sources |
| `awesome_repos/urls.py` | Robots and sitemap routes |
| `frontend/templates/components/seo_meta.html` | Shared title, description, canonical, OG, and Twitter metadata |
| `frontend/templates/base_landing.html` | Public layout, analytics, and `WebSite` schema |
| `frontend/templates/pages/landing/_content.html` | Homepage positioning and discovery links |
| `frontend/templates/repos/search.html` | Repository-search landing surface |
| `frontend/templates/repos/lists.html` | Awesome-list directory landing surface |
| `frontend/templates/repos/detail.html` | Repository detail metadata and schema |
| `frontend/templates/repos/list_detail.html` | Awesome-list detail metadata and schema |
| `apps/blog/posts/` | Checked-in Markdown articles |
| `apps/repos/tests/test_seo.py` | SEO metadata, schema, robots, and sitemap tests |

## Keyword Research Appendix

All volume, KD, CPC, and SERP data below is US/English DataForSEO data measured on 2026-07-27 unless stated otherwise.

### Owned search and analytics baseline

- GSC: 3 query/page rows, 3 impressions, 0 clicks, and no meaningful position 5-20 opportunities in the available 90-day window.
- DataForSEO: one ranking keyword — `ultraworkers/claw-code`, volume 50, KD 9, position 10 on its repository page.
- Plausible: Organic Search generated 33 visitors, 33 visits, and 152 pageviews in 90 days.
- The homepage led organic landing pages with 10 visitors and 59 pageviews.
- Plausible recorded 137 outbound-link clicks site-wide, but no product funnel goals.
- GSC and Plausible materially disagree on search visibility. Phase 0 must verify property coverage, sitemap submission, and attribution before using either for conversion scoring.

### Existing-page boost candidates

| Target | Volume | KD | CPC | Owning URL | Priority |
|---|---:|---:|---:|---|---|
| awesome lists | 210 | 17 | – | `/lists/` | High |
| github awesome list | 140 | 22 | – | `/lists/` | High |
| awesome list github | 70 | 30 | – | `/lists/` | Medium |

The “awesome lists” SERP contains GitHub, AwesomeLists.io, GetAwesomeLists, Context Awesome, and Ecosyste.ms Awesome. It rewards directory pages, so improving the existing directory is a closer intent match than creating a separate article.

### Use-case candidates

| Target | Volume | KD | CPC | Page | Priority |
|---|---:|---:|---:|---|---|
| best github repositories | 210 | 14 | $11.80 | `/for/github-repository-discovery/` | High |
| github repo analytics | 20 | 11 | $30.69 | `/for/github-repository-analytics/` | Medium-high |
| github stars tracker | 170 | 36 | $46.75 | `/for/github-star-tracking/` | Conditional |

“Best GitHub repositories” has a mixed SERP of GitHub Trending, Reddit, Trendshift, OSS Insight, and listicles. A data-backed discovery surface can compete. “GitHub stars tracker” is above the authority cap and led by Star History, so Phase 4 requires a fresh SERP check and a real tracking utility—not a thin article.

### Alternative and comparison candidates

No alternative or comparison phrase returned measurable demand in the initial batch. Keep GitHub Explore and Star History alternative pages behind the three measured use-case opportunities. Every alternative page must include at least three honest tradeoffs where the competitor wins.

### Playbook candidate

`/playbooks/evaluate-open-source-projects/` is a strategically strong, linkable guide tied directly to Awesome's activity, freshness, stack, cross-list, and archive signals. The exact query was not measured, so Phase 5 begins with a fresh DataForSEO phrasing sweep before drafting.

### Conversion-weighted opportunities

| Candidate | Source | Conversion signal | SEO signal | Priority impact |
|---|---|---|---|---|
| Homepage and repository discovery | Plausible | 10 organic visitors, 59 pageviews, 813s visit duration aggregate | Existing root visibility | Supports Phase 2 |
| Awesome-list directory | Plausible | 2 organic visitors, 4 pageviews | 3-keyword cluster, 420 combined measured volume | Promotes Phase 1 |
| Repository details | Plausible | Multiple long-tail organic landings | DataForSEO found one position-10 repo query | Preserve and strengthen programmatic surface |
| Signup/search/list request | No connected goal data | Not measurable | n/a | Add measurement in Phase 0 |

### Saturated or excluded terms

| Keyword | Volume | KD | Decision |
|---|---:|---:|---|
| github repository search | 170 | 35 | Defer: navigational intent and GitHub-controlled SERP |
| github explore | 320 | 69 | Exclude as a direct head target |
| open source alternatives | 720 | 42 | Exclude until Awesome truly supports alternative matching |
| best open source projects | 140 | 43 | Revisit after authority growth |
| github open source projects | 260 | 42 | Revisit after authority growth |

## Phases

### Phase 0 — Technical foundations and measurement

**Why:** the metadata basics are healthy, but indexing and measurement cannot yet support reliable prioritization.

**Scope:**

1. Replace the single 2.65 MB, 16,683-URL sitemap response with a sitemap index or bounded section sitemaps so crawlers and audits do not time out.
2. Preserve the current valid robots directive and ensure it points to the sitemap index.
3. Add `WebApplication` plus `Organization` JSON-LD to the homepage while retaining `WebSite` search action schema.
4. Submit the sitemap through GSC and record the accepted status.
5. Verify why GSC reports 3 impressions while Plausible reports 33 organic visits.
6. Add measurable events/goals for repository search, GitHub signup, list request, newsletter subscription, API-key creation, MCP setup copy, and outbound GitHub click.

**Likely files:** `awesome_repos/sitemaps.py`, `awesome_repos/urls.py`, `frontend/templates/base_landing.html`, `apps/core/analytics.py`, relevant tests.

**Verification:**

- Sitemap index and each child sitemap return 200 and valid XML.
- No child sitemap exceeds 10,000 URLs or a practical response-time budget.
- Homepage schema validates without errors.
- GSC shows a submitted sitemap row.
- At least one connected analytics source exposes the defined product events.

### Phase 1 — Strengthen `/lists/` for the awesome-lists cluster

Add a concise intent-matching introduction, explain how list activity and coverage are measured, add FAQ content/schema, and link contextually to repository search, list requests, representative list pages, and the evaluation playbook placeholder only after it exists. Preserve the directory as the canonical URL for all three measured terms.

**Gate:** unique title/description, one H1, ≥800 useful words across the page experience, FAQ schema, and at least two new contextual inbound links.

### Phase 2 — `/for/github-repository-discovery/`

Build an 800+ word use-case page around finding strong GitHub repositories from independent curator signals, current activity, stack, freshness, and project health. Show live repository examples from existing querysets rather than hard-coded rankings.

**Gate:** `WebApplication`, `BreadcrumbList`, and `FAQPage` schema; ≥2 feature links, ≥2 catalog links, ≥1 sibling/related content link, and ≥2 inbound links.

### Phase 3 — `/for/github-repository-analytics/`

Explain exactly which repository signals Awesome exposes and which it does not. Center the page on practical evaluation, not vanity metrics, and link to live repository detail/update examples.

**Gate:** same use-case quality bar plus an explicit limitations section covering security, maintainer quality, and license/compliance checks.

### Phase 4 — `/for/github-star-tracking/`

Re-run authority, keyword, and SERP checks first. Proceed only if Awesome can show useful historical growth and comparisons beyond a thin filter page. If the KD/authority gap remains too wide, mark the phase blocked and invest in Phase 5/9 first.

### Phase 5 — Open-source project evaluation playbook

Use the Markdown blog pipeline or add a dedicated playbook route only after the exact keyword phrasing is revalidated. Minimum 2,500 words, source-backed claims, `Article` and `BreadcrumbList` schema, and examples that use Awesome's live catalog.

### Phases 6-7 — Honest alternative pages

Revalidate demand and current competitor capabilities immediately before drafting. Each page must contain:

- A direct “choose X when…” summary.
- At least three areas where the competitor wins.
- Current feature/pricing claims from official sources.
- ≥600 words, `WebApplication`, `BreadcrumbList`, and `FAQPage` schema.
- Links to repository search, lists, updates, and at least two sibling pages once available.

### Phase 8 — Internal-link spine audit

Run the SEO sprint link audit across all generated pages. Every page must be reachable through at least two contextual links, and the homepage, `/repos/`, `/lists/`, `/updates/`, and playbook should form the central spine.

### Phase 9 — Directory and ecosystem outreach

Work through `.seo/backlink-targets.json`. Prioritize useful integrations, data/API collaboration, and genuinely relevant directory entries. Do not buy links or trade irrelevant placements.

## Off-page checklist

- [ ] Submit/verify Product Hunt profile after the SEO landing surfaces are live.
- [ ] Submit/verify AlternativeTo listing with honest category positioning.
- [ ] Explore an open-data/API collaboration with Ecosyste.ms Awesome.
- [ ] Propose relevant cross-references to awesome-list directory operators only when Awesome adds unique value.
- [ ] Publish a linkable open-source evaluation playbook before broad outreach.
- [ ] Re-run DataForSEO referring-domain research after Phase 5.
