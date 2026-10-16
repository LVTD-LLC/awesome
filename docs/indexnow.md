# IndexNow

Browse Awesome serves a stable public ownership proof at `/indexnow-key.txt`.
The key is public, not an authentication credential, and is unrelated to Django's
secret key. Keep it stable across deployments. The response includes the image's
`X-Deployment-Revision` so automation waits for the expected live release.

The **IndexNow public URL changes** GitHub workflow runs hourly at :37 UTC
(GitHub schedules can be delayed), manually, and after successful Deploy Prod
runs. It traverses every paginated sitemap section, submits only canonical
same-origin URLs in batches of at most 10,000, and includes previously observed
URLs that disappear. Empty optional sections are allowed; failed/invalid sections
abort the entire scan before any removals are inferred. It never enumerates
private database records or sends page contents.

Hourly and deploy runs compare full sitemap lastmod timestamps. The deployment
revision gates reachability only; deploying unchanged content never triggers a
catalog-wide notification. The workflow uses the repository's stable numeric ID
so a rename does not disable it, while forks remain excluded. Legacy cached
revision prefixes are stripped before comparison; existing timestamps and removed
URLs are retained. The cache key namespace and schedule are unchanged.
Transient failures retry with bounded backoff; failed runs stay visible in Actions
and the next hourly run retries. A cache checkpoint advances only after every
batch is accepted. Workflows share one concurrency group.

If the GitHub cache is missing or evicted, the first complete scan establishes a
checkpoint without submitting the whole catalog. It cannot recover older removed
URLs or notify changes from before that baseline. Changes/deletions occurring
entirely between scans can be missed.
The site's one-hour sitemap cache may delay discovery by another scan. Content
changes must update the affected pages' content dates to be detected; a deployment
alone is not evidence that every page changed. Explicit full submission remains
an operator-only recovery option, not a routine indexing nudge.
Acceptance (200, or 202 pending key verification) does not guarantee
indexing, and IndexNow does not replace Google Search Console/sitemaps.

Manual dry run/full submission (standard-library Python, no site credentials):

```
python apps/pages/indexnow.py --site-url https://browseawesome.com --dry-run
python apps/pages/indexnow.py --site-url https://browseawesome.com
```

To disable notifications, disable this workflow in GitHub Actions. Failed
notifications do not roll back or fail an otherwise successful production deploy.
