# SISU LMS — monthly subscription release

Updated 18 October 2026. Start with [the current subscription contract and deployment handover](docs/ACCOUNT_SUBSCRIPTIONS.md).

This folder contains the latest editable LMS source and compiled production `/campus` assets. It contains no Wisdom presentation data, demo seed, preview HTML or preview runtime. The separate presentation remains in `D:\Preview`.

Teachers, students and institutes now use fixed monthly USD subscriptions based on verified billing country. Every new account has one 14-day trial. The Subscription page replaces the usage calculator, provider enrolment billing and class-cost consent prompts.

## Build and deploy

From `frontend`, run `npm ci` and `npm run build`. On your configured Frappe bench, deploy the app and run the migration described in the handover. Existing site secrets, identity providers, files and operational storage settings must be retained. No live database migration was performed on this Windows computer.

## Validation

Run `python -m unittest discover -s tests -p "test_account_billing*.py" -v` for the new billing service tests. From `frontend`, run `npm test` for the retained frontend checks. QA screenshots and reports accompany the final package.

## Payments

Payment gateways and recurring card collection are not connected. The backend exposes a server-only verified-settlement integration boundary and owner-only verified bank-payment review. No card details or fake successful payments are collected. See the handover before enabling a real payment provider.

Older documents under `docs/history` and dated architecture notes are historical; the October 18 account subscription contract governs pricing and trial behaviour.
