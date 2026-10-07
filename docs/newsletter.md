# Weekly discovery newsletter operations

## Services

- Admin: https://newsletter.browseawesome.com/admin/
- CapRover: `https://captain.cr.lvtd.dev`, host `138.201.126.181`.
- Apps: `browseawesome-listmonk`, `browseawesome-listmonk-db`.
- Listmonk 6.2.0, upstream image digest
  `sha256:f535d59e14991337a9f2d570273685378ae86b0d7698c3e00da444e3bc205286`.
- PostgreSQL 17, private overlay only; persistent volume mounted at
  `/var/lib/postgresql/data`. Uploads persist at `/listmonk/uploads`.
- The app starts with `--install --idempotent --yes --config ''`, then
  `--config ''`. Version upgrades/migrations are deliberately not automatic.
- Credentials: Infisical **Openclaw / prod / /projects/browseawesome**,
  `LISTMONK_ADMIN_USER`, `LISTMONK_ADMIN_PASSWORD`, `LISTMONK_DB_PASSWORD`,
  `LISTMONK_SMTP_PASSWORD`. Retrieve securely; never paste into issues or chat.

## Sending and consent

Mailgun US domain `mg.browseawesome.com`; SMTP `smtp.mailgun.org:587`, login
`postmaster@mg.browseawesome.com`, STARTTLS with certificate verification.
Sender: **Rasul at BrowseAwesome <rasul@browseawesome.com>**.
SPF, 2048-bit DKIM, MX and tracking CNAME are DNS-only records. Monitor-only
DMARC (`p=none`, relaxed alignment) is published for the apex and sending subdomain. This configures
outbound mail, not an inbox for `rasul@browseawesome.com`; no apex MX is changed.

The public **Weekly awesome open-source discoveries** list uses double opt-in. Visitors
must confirm the Listmonk email before receiving campaigns. Duplicate requests
use the same generic response; existing unsubscribe/blocklist state is managed
by Listmonk, never overwritten by the Django app. Open/click tracking is disabled
in Listmonk and Mailgun. Mailgun maintains domain-level bounce/complaint
suppressions; this initial setup does not mirror provider events into Listmonk.
Keep suppression lists intact. Use Listmonk's unsubscribe link in every campaign.

No campaign or recurring editorial automation is created. Compose the weekly
news/projects edition in Listmonk, send yourself a preview, then schedule it to
this list. Check the sender and unsubscribe footer before sending.

## Website integration

Set `NEWSLETTER_LISTMONK_URL=http://browseawesome-listmonk:9000` and
`NEWSLETTER_LIST_UUID` on web and workers. Set `NEWSLETTER_TRUST_PROXY=True` only behind the CapRover Nginx edge, which overwrites X-Real-IP. Neither URL nor UUID is an admin credential.
Empty configuration hides the homepage form and makes the signup endpoint
return a recoverable unavailable response.

`POST /newsletter/` validates email and CSRF, checks a honeypot and a separate
10-attempt/IP/hour Redis-backed rate limit, then calls Listmonk's public
subscription API with only the configured list UUID. It does not preconfirm
subscribers or store their email in the Django database. Timeouts/errors return
503 and retain the form; successful requests redirect to a generic inbox page.
Provider bodies, exceptions and email addresses are not logged by this flow.

CapRover's custom Nginx template blocks external `/api/public/subscription`
requests and redirects the `/subscription/form` (and bare `/subscription`) to the website, preventing
bypass of the website's signup rate limit. UUID-based confirmation/preferences
and unsubscribe routes remain reachable. The private overlay API stays available.
Preserve these rules when updating the CapRover Nginx template.

## Backups

A consistent initial custom-format dump is saved privately on the host at
`/docker/data/browseawesome-listmonk-backups/initial-2026-10-07.dump`. An isolated
restore into a disposable database passed. The existing `restic-main` nightly
backup discovers PostgreSQL containers automatically, creates logical dumps,
and includes `/docker`, `/captain`, and Docker volumes. The new services match
that discovery; the first scheduled offsite backup after provisioning is still
pending. The bootstrap dump has also been uploaded to the existing encrypted
offsite Restic repository (snapshot `1055ac0e`, tag
`browseawesome-listmonk-bootstrap`). Restoring that offsite snapshot produced
a byte-for-byte SHA-256 match with the dump used in the database restore check.

## Verification and rollback

- Check HTTPS `/health` and authenticated settings/list state.
- Submit through the landing page to an operator-controlled inbox; confirm the
  message is delivered from the configured sender with authenticated DKIM/SPF.
- Follow confirmation; ensure list status becomes confirmed. Exercise unsubscribe
  with that same test subscriber before an actual campaign.
- Check mobile/desktop and light/dark form states, validation, provider failure,
  duplicates and rate limits. PostgreSQL tests run in GitHub CI.
- Website rollback: clear `NEWSLETTER_LIST_UUID` to hide/disable the integration,
  or revert the feature PR. Preserve Listmonk and subscriber data.
- Before Listmonk upgrades, take a consistent `pg_dump -Fc` and uploads snapshot;
  test restoring into a separate disposable database. Retain the pinned app image
  and never downgrade an already-migrated database without restoring its backup.

## Network isolation

The main shared overlay (10.0.1.0/24) was out of addresses during setup. Only
the new newsletter services were changed: the database is on the private
`browseawesome-newsletter-private` overlay (10.0.2.0/24), and Listmonk joins
both that network and the shared proxy/application overlay. CapRover
`serviceUpdateOverride` preserves these attachments across redeploys. The
database has no published ports. Preserve the network and aliases during
maintenance; reconnecting the database to the exhausted shared network can
prevent scheduling. Broader host network capacity planning remains separate.

Existing per-repository update subscriptions are not imported or changed.
The general discovery newsletter requires separate explicit consent.
