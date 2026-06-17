# Awesome - Brand Context for SEO

> Read this before executing any SEO sprint phase. This file is the product and positioning context for programmatic SEO work.

## Product

- **Name:** Awesome
- **One-liner (<=20 words):** Search and monitor GitHub repositories discovered across curated awesome lists.
- **What we do:** Awesome ingests GitHub awesome-list READMEs, extracts repository links, enriches those repositories with GitHub metadata, and gives developers one searchable catalog for maintained, relevant, repeatedly recommended projects.
- **Pricing structure:** No pricing page exists in the repo. README positions the hosted tool as free and open source.
- **Free tier?** Yes - the public discovery surface is free. Authenticated features and API/MCP access should be described honestly from current product behavior before any commercial page ships.

## Audience

- **Primary persona:** Developers and technical teams evaluating open source projects from curated GitHub awesome lists.
- **Secondary personas:** Open-source maintainers, DevTools founders, OSS researchers, technical writers and curators, and AI-agent builders needing repository context.
- **Industries we target:** Software development, DevTools, open-source infrastructure, developer education, AI tooling, and technical research.
- **Company size we target:** Individual developers through small engineering teams; future API/MCP users may include developer-tooling teams.
- **Jobs to be done (top 3):**
  1. Find maintained repositories for a stack, language, or topic without manually scanning many awesome lists.
  2. Compare projects by stars, age, freshness, archive status, language, topics, stack signals, and cross-list mentions.
  3. Monitor repository/list activity and expose the catalog through API and MCP workflows.

## Competitors

These competitors were inferred from repository positioning plus manual web research. Review before writing alternative/comparison pages.

| Brand | Slug | URL | Tier | Notes |
|---|---|---|---|---|
| GitHub Topics/Search | github-topics | https://github.com/topics | head | Official GitHub discovery surface with huge authority; broader but less curated around awesome-list cross-list signals. |
| GitHub Trending | github-trending | https://github.com/trending | head | Official trending repository surface; strong brand, weak historical/filter depth for awesome-list use cases. |
| Libraries.io | libraries-io | https://libraries.io | mid | Open-source package discovery and dependency metadata. More package-centric than awesome-list-centric. |
| ecosyste.ms | ecosyste-ms | https://ecosyste.ms | mid | Open datasets and APIs for package, repository, dependency, and sustainability data. More infrastructure/data focused. |
| OSS Insight | ossinsight | https://ossinsight.io | mid | GitHub event analytics, repository insights, and collections. More analytics/trends focused. |
| OpenAlternative | openalternative | https://openalternative.co | niche | Curated open-source alternatives directory. More product-alternative focused than repository research focused. |
| sindresorhus/awesome | sindresorhus-awesome | https://github.com/sindresorhus/awesome | head | Source corpus and search-intent competitor; not a SaaS competitor, but users may compare Awesome with manually browsing awesome lists. |

## Brand Voice

- **Voice tags:** honest, technical, no-hype, practical, open-source, catalog-first.
- **Person/perspective:** "we" for product copy; "you" for task-focused page sections.
- **Forbidden words/phrases:** revolutionary, ultimate, game-changing, synergy, seamless, AI-powered unless describing a concrete AI-agent integration.
- **Reference brands for tone:** GitHub docs for clarity, Linear docs for brevity, Django docs for plain explanations.

## Anti-Positioning

Use these in honesty sections and comparison pages.

1. We are not a GitHub replacement or source-code hosting platform.
2. We are not a package dependency security scanner.
3. We are not a private-code analytics product.
4. We are not a paid placement marketplace or pay-to-rank directory.
5. We are not a generic listicle site; SEO pages should be backed by catalog data and product behavior.
6. We do not guarantee a project is healthy; we surface signals that help users decide.

## Concrete Differentiators

1. Cross-list recommendation signal: repositories that appear across many curated lists are easier to identify.
2. Repository freshness filters: archive state, last push, age, stars, language, topics, generated tags, and stack signals.
3. Awesome-list level browsing: users can inspect a source list and its indexed repositories instead of reading one README at a time.
4. Public integration surface: authenticated API and public read-only MCP endpoint for agent workflows.
5. Request and rescan workflows: users can ask for new lists and operators can refresh catalog data.

## Visual Brand

- **Accent color (primary):** #15803D
- **Accent color (secondary):** #2563EB
- **Ink color:** #0F172A
- **Surface color:** #FFFFFF
- **Hero font family:** Inter, ui-sans-serif, system-ui, sans-serif
- **Body font family:** Inter, ui-sans-serif, system-ui, sans-serif
- **Icon set:** Existing templates primarily use text and SVG/static brand assets; keep future SEO pages consistent with current Django/Tailwind conventions.

## Links To Existing Surfaces

- Homepage/search: https://awesome.lvtd.dev/
- Pricing: none
- Blog: https://awesome.lvtd.dev/blog/
- Awesome-list directory: https://awesome.lvtd.dev/lists/
- Request an awesome list: https://awesome.lvtd.dev/lists/request/
- Public MCP endpoint: https://awesome.lvtd.dev/mcp
- API surface: https://awesome.lvtd.dev/api/
