# SISU monthly subscriptions — 18 October 2026

This is the current pricing contract. It supersedes older active-enrolment, 30-day usage, assigned-price and three-day app-trial documents. The production package has no presentation account seed or preview entry point.

| Account / package | Verified Sri Lanka billing country | Other verified billing countries |
| --- | ---: | ---: |
| Student | USD 0.50/month | USD 1.50/month |
| Teacher · Individual | USD 6/month | USD 9/month |
| Teacher · Silver | USD 15/month | USD 22/month |
| Teacher · Gold | USD 45/month | USD 65/month |
| Teacher · Platinum | USD 75/month | USD 110/month |
| Institute · Individual | USD 12/month | USD 18/month |
| Institute · Silver | USD 30/month | USD 44/month |
| Institute · Gold | USD 90/month | USD 130/month |
| Institute · Platinum | USD 150/month | USD 220/month |

## Customer experience

- One 14-day trial per new account, anchored to account creation. Login, plan changes, reactivation and migration cannot reset it. Institute administrators share one institute subscription; adding another administrator does not create another institute bill or trial.
- The Subscription page replaces the pricing calculator and old provider billing page. Students also have Subscription in their sidebar. Old `#pricing` and `#plans` links lead to Subscription.
- Country review is an internal backend/owner operation. Customers see only their applicable price; no country selector, country-pricing explanation or cross-market catalogue is exposed by the customer billing response. Only the verified platform owner can approve a billing country, with a recorded review reason. Changing profile country, browser language, device location or IP address cannot grant Sri Lankan prices. A pending country change keeps the previous verified country until approval.
- All amounts are USD, stored as integer cents. No currency conversion or tax amount is invented. The billing document is identified as a subscription invoice, not a statutory tax invoice.
- No student-count, class-count or course-duration usage fee is added. One-day workshops and long programmes use the same account subscription. Class tuition and tuition access remain separate.
- Course access duration is still configurable for the learning experience. The old cost acknowledgement and “Allow always” prompts are removed.
- Core LMS and Study Room are available on every active subscription. Gold and Platinum retain the news feed and advanced provider features; Platinum retains delivery and watermark features. No AI package is newly enabled.
- A paid package change applies at the next renewal, without repricing existing paid invoices. Cancellation stops renewal invoices and preserves access through the existing end date. Resume does not restart the free trial.
- The invoice service period defines the billing anniversary. A 31 January cycle ends on 28/29 February, then the next cycle ends on 31 March. Time follows the Frappe site's configured time zone. No new paid period is granted without confirmed payment.
- Initial billing is requested after trial expiry. The daily job prepares an established account's next invoice at expiry. It does not accumulate invoices during a long unpaid lapse. A new invoice after a lapse starts a fresh period; unused locked-out months are not back-billed.
- Expired accounts can still sign in for subscription and account recovery. Protected learning/teaching APIs and private files enforce expiry on the server, independent of the browser or scheduler.

## Deployment

1. Back up the real Frappe database and files. This Windows folder is source plus compiled assets, not a running Frappe database.
2. Install/update this app in the existing Frappe bench using the normal deployment procedure. Preserve existing site configuration, private files, identity provider and integration secrets.
3. Run `bench --site YOUR_SITE migrate`, then `bench build --app institute_lms`, clear the site cache and restart the normal web/workers/scheduler processes. The supplied compiled `/campus` entry is already rebuilt; rebuilding the Vue frontend uses `npm ci` and `npm run build` inside `frontend`.
4. Migration adds **IL Account Subscription** and **IL Account Invoice**, required indexes and existing-member subscription identities. It preserves original account creation dates, existing package choices and historical financial documents. It disables legacy provider auto-pay mandates. No demo members, fabricated payments or fresh migration trials are inserted.
5. Before cutting over a site with existing paid commercial agreements, reconcile those agreements and arrange the cutover with the owner. Historical LKR usage invoices are retained but are not converted into USD subscription payments or invented account credit. Accounts older than their trial need an explicitly verified payment under the new contract.
6. Confirm the configured, verified platform-owner login can use **Subscriptions & country verification**. Institute administrators cannot approve their own country or mark their subscription paid.
7. Configure outgoing email and the scheduler. Optionally set `il_subscription_bank_instructions` in private site configuration to publish real SISU bank transfer instructions. None are fabricated in this package. Configure operational storage capacity separately; it is not a subscription price or an enrolment meter.
8. If deploying the included marketing website separately, build with `VITE_LMS_URL` pointing to the real HTTPS `/campus` URL. Its default is the same-origin `/campus`, not a localhost demonstration link.
9. On a staging Frappe site, verify all three roles: new-account trial, exact expiry, country review, package change, cancellation, invoice ownership, bank settlement, receipt email, next-month renewal, protected files and native LMS access. Database row locking, unique keys, migration and real email delivery still require this live-site acceptance.

## Payment gateway handover

Online gateway and saved-card collection are deliberately **not connected**. No card number or CVC is collected by the subscription page. Choosing Card saves a preference only; no automatic-debit consent is implied. Legacy saved-card mandates must not be reused for these new USD subscriptions.

The server-only integration boundary is `account_billing.record_verified_payment(invoice, reference, received_minor, currency, channel)`. It is not whitelisted and cannot be called directly by a browser. A future gateway adapter must:

1. Create hosted checkout server-side from an existing unpaid invoice's immutable USD amount, identity and service period.
2. Keep secrets on the server. Use HTTPS, explicit merchant/environment binding, callback signature verification and provider-side settlement verification.
3. Bind the provider payment ID, merchant and invoice. Use a namespaced globally unique settlement reference. Confirm exact amount and USD currency before calling the settlement service within the database transaction.
4. Treat successful redirect pages as informational only. Reject replay, mismatched invoices, duplicate references, unsupported currency, partial/overpayment and expired or void invoices. Reconcile late money externally before allocating or refunding it.
5. Obtain explicit recurring-card consent through the gateway and save only approved provider tokens and masked card metadata. Add revoke/cancel controls, idempotent renewal attempts, failure handling and settlement reconciliation before enabling automatic debit.
6. Never extend paid access merely because an invoice was created or a payment was attempted. Queue receipts only after verified settlement. Add refund/chargeback handling before live card acceptance.

Until then, the platform owner can record a genuinely cleared bank payment through the owner review form, with the exact USD cents, unique reference and evidence note. The service records a receipt and queues email. A student/teacher cannot mark a payment successful. Local test fixtures never transfer funds or send messages.

## Data boundaries

- New subscription rows are unique by account identity; institute admins share the institute key.
- One unpaid invoice per subscription is protected by a database unique open-invoice key, in addition to account row locking.
- Payment references are globally unique in the new invoice table. Repeated verified callbacks for the same paid invoice/reference do not extend access again.
- Trial start/end and identity are immutable through the managed document controller; invoice price, country, plan and service period are immutable snapshots.
- Historical provider invoices remain available as historical records, but their issue/collection jobs and usage-price mutation endpoints are retired.
- Learning tuition invoices, provider payouts, protected course access and their existing gateway integrations are separate from the new SISU account subscription.

## Validation recorded for this handover

- 28 new Python billing rules/service tests: exact rates, once-only trial calculation, expiry, month-end anchors, payment matching/idempotency, pending country changes, owner authority, invoices, cancellation and escaping.
- 55 existing retained frontend checks passed after removing retired demo-only workflow tests and updating navigation/production-client expectations.
- Five desktop/mobile role layouts and subscription recovery checks passed against mocked API responses. The refreshed presentation preview was also checked for Student and Teacher subscription screens.
- Production LMS and marketing website builds succeeded. Python sources compile. The LMS build retains a pre-existing large optional ProductWorkspace chunk warning.
- No live Frappe/MariaDB migration, gateway charge, card debit or real email delivery was performed on this Windows machine.

## Simplified customer UI update

Your billing now presents a compact plan card, View plans for providers, collapsed Manage settings, and invoice/receipt downloads. Unverified billing shows a neutral pending-setup message and cannot issue an invoice; it never guesses a price. Student profiles display their ID card with a photo uploader and no cover banner. Teacher and institute covers remain.
