# ERP Customization Register

One register of every customization across the site, with a change log that
fills itself in.

**Approval is set once.** A record gets a requester and an approver, then it is
locked. Every change after that appends to its history — it never asks to be
re-approved.

## What gets tracked

| Source | Mechanism | Fires when |
|---|---|---|
| Site edit | `doc_events` in `hooks.py` | you save a script, field, print format, workflow |
| Git push | webhook at `tripod_hr.registry.git_hook.receive` | you push to the repo |
| Migration | `before_migrate` snapshot + `after_migrate` diff | you run `bench migrate` |
| Nightly | scheduler `tracker.nightly_sync` | safety net for anything missed |

Artefacts covered: DocType, Report, Page, Server Script, Client Script,
Print Format, Custom Field, Property Setter, Workflow, Notification,
Dashboard Chart, Web Form — filtered to custom apps, except Custom Field,
Property Setter and non-standard Print Format, which are customizations by
definition.

## Setup

1. `bench --site <site> migrate`
2. Open **ERP Customization Register** from the awesomebar.
3. Menu → **Preview discovery (read only)** to see the real artefact count per
   app. Nothing is created.
4. Primary action → **Run discovery scan** to seed the register. Everything
   lands in `Needs Names`.
5. Clear the backlog: list view of **ERP Customization**, filter
   `registration_status = Needs Names`, multi-select, then call
   `tripod_hr.registry.discovery.bulk_set_approval` — or open records one at a
   time from the register page.

## Git webhook

In `site_config.json`:

```json
{ "erp_registry_webhook_secret": "<same value as GitHub>" }
```

In GitHub → repo → Settings → Webhooks:

- Payload URL: `https://<site>/api/method/tripod_hr.registry.git_hook.receive`
- Content type: `application/json`
- Secret: the value above
- Events: **Just the push event**

Unsigned or wrongly signed payloads are rejected with 401. Without the secret
set, the endpoint rejects everything — the site feed and migration diff still
work on their own.

## Migration diff

`before_migrate` writes an inventory snapshot with a fingerprint hash per
object. `after_migrate` takes a second snapshot and triages three ways:

- **new object in a custom app** → register record created, `Needs Names`
- **changed object already in the register** → history entry appended
- **framework object** → counted in the diff report only, never registered

Watchlist objects (see `WATCHLIST` in `core.py`) are pulled out of the framework
bucket and raised as alerts, because v15 patches are known to undo fixes such as
the System Manager DocPerm strip on HR and Payroll doctypes. View the last diff
from the page menu.

## Notes

- Site hooks skip entirely during migrate, install, patch and import. The
  snapshot diff covers that window instead.
- Handler failures are swallowed and written to the Error Log. A registry
  problem must never block a user's save.
- Non-standard print formats live only in the database, so the change log is
  their only version history. Bodies are stored in `new_value` on each entry.
- Deleted artefacts set `is_active = 0`; history is never removed.
