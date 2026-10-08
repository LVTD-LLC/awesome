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

Hourly runs compare full sitemap lastmod timestamps. Deploy runs resubmit all
current and previously observed URLs to cover template/static/blog changes.
Transient failures retry with bounded backoff; failed runs stay visible in Actions
and the next hourly run retries. A cache checkpoint advances only after every
batch is accepted. Workflows share one concurrency group.

GitHub cache eviction causes a safe full resubmission but loses knowledge of older
removed URLs. Changes/deletions occurring entirely between scans can be missed.
The site's one-hour sitemap cache may delay discovery by another scan. Content
changes that do not update sitemap timestamps need a manual full submission or
a deployment. Acceptance (200, or 202 pending key verification) does not guarantee
indexing, and IndexNow does not replace Google Search Console/sitemaps.

Manual dry run/full submission (standard-library Python, no site credentials):

```
python apps/pages/indexnow.py --site-url https://browseawesome.com --dry-run
python apps/pages/indexnow.py --site-url https://browseawesome.com
```

To disable notifications, disable this workflow in GitHub Actions. Failed
notifications do not roll back or fail an otherwise successful production deploy.
