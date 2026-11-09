# Shared provider plan catalogue

The deployed `il_plan_catalog_source_site` configuration identifies the authoritative Bench site. Only that site's owner API may publish; every consumer uses a fixed read-only SQL query in a separate connection, with request-local caching. Only public plan fields reach the guest API. An unavailable source fails closed rather than issuing invoices at stale fallback prices. Authentication and subscriptions never switch into the source site's context.

`card_features` is ordered plain text, independent of the existing boolean feature entitlements. Legacy payloads receive a display list based on their current switches. The publisher preserves optimistic revision checks and owner audit history. Existing invoice amounts and subscription periods are not rewritten. `account_billing.price` already reads the catalogue for new LKR provider invoices.

Live activation preserves an existing published public catalogue when the owner catalogue is still empty. Conflicting published catalogues stop activation. Site config backups are private. Public and Teen live sites share the owner catalogue; staging remains isolated. Repeated activation verifies the shared version without applying old local copies.

Deployment order: upload source archive and scripts; run deploy as sisu; run catalogue activation as sisu; restart web/workers; run rollback check as sisu; run website activation as root. Website activation verifies the guest endpoint before changing the existing marketing app and backs up that app. No Nginx, DNS, payment, or email changes occur.

Browser acceptance: add a truthful card feature and change a description; review and publish; refresh website and provider billing plan cards; confirm price, description, feature order and removed rows match. Institute teachers see the read-only card text. Do not test price/access switches on real subscribers casually: they apply to future invoices/current entitlements. The checker tests publication and stale/unauthorized rejection in a rollback transaction; shared consumer reads compare the committed baseline. Gateway testing remains paused.

All money-moving paths, existing invoices, and current paid periods remain subject to their existing rules. Publishing card text does not implement a new product feature.
