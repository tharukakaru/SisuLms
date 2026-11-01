# HNB CyberSource sandbox handover — 30 October 2026

Activation case **002760691**, reported by HNB/customer as Work in Progress.
HNB has agreed to testing with customer-initiated payments. This is not production
approval or confirmation that each wallet is activated. No real transaction was
performed during implementation. No credentials were supplied or invented.

## Integration and boundaries

The adapter uses direct REST `POST https://apitest.cybersource.com/uc/v1/sessions`.
No CyberSource server SDK is installed. The official browser Unified Checkout
library is still required to securely collect payment details. It is not the
server SDK that HNB asked us to avoid.

The current Sessions v1 guide uses `VAS.UnifiedCheckout`, `createCheckout` and
`mount`, with a server-created `completeMandate` for CAPTURE and 3DS. In this
context autoProcessing means completing the transaction the customer is currently
authorizing. It does not mean recurring payments. We request no stored card/TMS
creation, have no merchant-initiated charge endpoint and schedule no charges.

REST authentication uses certificate-based JWT v2 with an RSA private key loaded
from a server-only P12 certificate. JWTs bind the exact body digest, method, path,
sandbox host, merchant, issuance, short expiry and unique nonce. The official
HTTP-signature example is deprecated; do not copy its legacy authentication.
HNB must confirm/provide the merchant's registered JWT key ID and sandbox P12.

Configuration is disabled by default. The transport has only a sandbox hostname;
setting mode to live is rejected. Enabling production requires a separate reviewed
change and bank acceptance. Install this branch only on a dedicated test site.
Sandbox settlement deliberately updates test invoices/access, never real ledgers.

## Payment flow

1. The authenticated customer clicks Pay online on an existing invoice. The server
   checks role, site/institute scope, invoice ownership, status and its stored amount.
2. A dedicated `IL CyberSource Attempt` records a unique reference and immutable
   financial snapshot before calling the provider. A unique active invoice key
   and row locks serialize repeated clicks. The session token is encrypted in a
   Frappe Password field; API keys/certificates never reach the browser.
3. Only explicitly configured/activated card and wallet options enter the session.
   Visa/Mastercard use PANENTRY. Other options are GOOGLEPAY, APPLEPAY and CLICKTOPAY.
4. The customer completes checkout. Browser completion, failure, cancellation,
   token contents and redirect URLs are never financial proof.
5. The backend queries `/tss/v2/searches` for its own immutable reference, then
   `/tss/v2/transactions/{id}` using authenticated merchant requests. It requires
   exact merchant/reference/amount/currency and successful `ics_auth` + `ics_bill`.
   A successful authorization alone never grants access. Ambiguous, unmatched,
   reversed or incomplete reports remain pending/review.
6. An atomic allocation records the merchant-namespaced unique settlement key,
   marks the invoice paid and calls existing access/subscription/usage services.
   Repeat verification cannot grant twice. Financial history is retained.

The reporting API is explicitly not a real-time API. It may take several minutes
to index a payment. The customer sees verification pending and can check again
after five minutes. No browser JWT is trusted as a shortcut. Actual processor
settlement/bank remittance is distinct from acceptance of the capture request;
confirm settlement in Transaction Management for HNB acceptance.

Closing checkout leaves the attempt pending until verified. An owner can inspect
`cybersource.review_queue`, and use `close_unpaid` only after reviewing Transaction
Management, recording at least 30 characters of evidence, waiting for session
expiry plus five minutes, and obtaining an empty authenticated report. A known
transaction cannot be discarded. Session-creation timeouts with unknown expiry
remain blocked for support review; do not blindly reset them or charge again.

Payments.lk, its signatures and callbacks remain separate. Bank review is retained;
an unresolved CyberSource attempt prevents competing manual settlement. An existing
Payments.lk attempt or pending bank slip prevents a new CyberSource session.

## Supported billing sources

| Kind | Existing invoice | Settlement effect |
|---|---|---|
| tuition | IL Invoice | Class/course/programme installment payment and existing paid access |
| subscription | IL Account Invoice | Teacher/institute plan and paid-through date |
| usage | IL Usage Invoice | Issued platform usage charge and existing reactivation rules |
| platform | IL Provider Invoice | Existing historical provider charge paid record |

Frontend buttons are added to student Payment history, subscription invoices and
usage invoices. The reusable component accepts `kind="platform"` for historical
provider invoices; these do not currently have a customer checkout screen.
Separate recorded-lesson purchases (`IL Lecture Order`) and the older control-plane
Premium-AI quote service are not routed through this adapter. They retain their
existing provider; do not advertise those as CyberSource-tested.

## Merchant routing and credentials

Do not post passwords, P12 files or keys in chat or commit them to Git.
The config helper `scripts/configure-cybersource-sandbox.py` uses hidden prompts,
copies the certificate to the bench's `local-private/cybersource` directory, and
sets restricted permissions. It leaves the provider disabled unless the explicit
`--enable` flag is supplied on a dedicated sandbox site.

Server-side `site_config.json` shape (placeholders only):

```json
{
  "il_cybersource": {
    "enabled": false,
    "mode": "sandbox",
    "origin": "https://YOUR-DEDICATED-SANDBOX-HOST",
    "merchants": {
      "platform": {
        "merchant_id": "YOUR-SANDBOX-MID",
        "key_id": "YOUR-REGISTERED-JWT-KEY-ID",
        "p12_path": "/home/USER/sisu-test-bench/local-private/cybersource/platform.p12",
        "p12_password": "ENTER-LOCALLY-USING-HIDDEN-PROMPT",
        "methods": ["PANENTRY"],
        "currencies": ["LKR"]
      }
    }
  }
}
```

The platform merchant is used for SISU's own subscriptions/charges. Tuition uses
an explicit `tuition:<IL Provider Account name>` mapping (or institute name for
legacy invoices). It never silently falls back to the platform merchant. Confirm
with HNB who receives each provider's tuition. Current provider-owned bank fees go
directly to that provider; this release does not invent split-settlement or move
money between merchants. Mapping one sandbox MID to several test providers is a
test-only choice, not approval for a live marketplace collection arrangement.

Only LKR is enabled unless HNB confirms another currency and it is explicitly
listed. Do not automatically convert USD subscription invoices. TLS is required
for the origin and it must match Frappe's configured host_name. The current
`http://localhost:8000` LMS can continue operating; use an HTTPS test site/origin
for checkout. Wallet/device/domain eligibility remains provider-controlled.

## Install on an isolated Frappe test bench

Use the existing Frappe 17/LMS/Payments dependency versions. Back up the test site,
install this working branch as `apps/institute_lms`, and run from that bench:

```bash
bench setup requirements
bench --site YOUR-TEST-SITE migrate
bench build --app institute_lms
```

Restart that bench after updating Python. Do not copy or migrate over a colleague's
working checkout. The schema migration adds a service-owned attempt DocType.
Keep the existing site encryption key; it protects stored session tokens.

## HNB sandbox acceptance matrix (not yet executed)

For both a student tuition invoice and a provider subscription invoice:

| Scenario | Expected result / evidence |
|---|---|
| Visa and Mastercard success | Correct amount; authenticated capture; one receipt/access grant |
| Card decline | Unpaid; no access; verified decline allows a fresh customer attempt |
| 3DS challenge success | Authentication/authorization/capture accepted; one allocation |
| 3DS failure/cancel | No access; reconcile any ambiguous provider outcome |
| Google Pay | Activated merchant, eligible wallet/device; correct Payment Solution |
| Apple Pay | Activated merchant/domain/device and sandbox wallet; correct Payment Solution |
| Click to Pay Visa/Mastercard | Official CTP test enrolment/card; correct Payment Solution |
| Double click / two tabs / repeated status | One active attempt and one financial allocation |
| Browser close/network loss/restart | Retained attempt; server report can recover; no second charge |
| Wrong user/tenant/invoice/amount/reference | Denied; no invoice or access change |
| Subscription renewal | Customer starts another checkout; no automatic deductions |
| Issued usage bill | Paid status/reactivation only after verified amount |
| Estimate or void invoice | Checkout denied |

Use current official test card tables, not real card data. HNB specifically supplied
3DS test Visa `4000000000001091`; follow HNB's challenge instructions and the current
official guide for expiry/CVV/scenarios. Wallet availability must be confirmed after
activation case 002760691; do not mark an absent wallet as passed.

For each test, record SISU attempt/reference, invoice, role, amount/currency,
CyberSource request ID, method, UTC timestamp and screenshot of Transaction
Management. Verify Client Application = Unified Checkout, Payment Solution and
Authentication/Authorization/Settlement results. Keep card data and secrets out
of test logs. A report response not matching the strict parser stays pending:
collect a redacted real sandbox fixture and adapt/test it before acceptance.

## Official references checked

- [Unified Checkout quick start](https://developer.cybersource.com/docs/cybs/en-us/unified-checkout/developer/all/rest/unified-checkout/uc-qs-intro.html)
- [Sessions request example](https://developer.cybersource.com/docs/cybs/en-us/unified-checkout/developer/all/rest/unified-checkout/uc-setup-capture-context/uc-appendix-complete-cc-ex.html)
- [Session signature validation](https://developer.cybersource.com/docs/cybs/en-us/unified-checkout/developer/all/rest/unified-checkout/uc-setup-capture-context/uc-session-validate.html)
- [JWT v2 request authentication](https://developer.cybersource.com/docs/cybs/en-us/platform/developer/all/rest/rest-getting-started/restgs-jwt-message-intro/restgs-jwt-const-intro.html)
- [Transaction search and details](https://developer.cybersource.com/docs/cybs/en-us/txn-search/developer/all/rest/txn-search.html)
- [Test cards](https://developer.cybersource.com/docs/cybs/en-us/unified-checkout/developer/all/rest/unified-checkout/uc-reference-test-cards/uc-reference-test-cards-uc.html)
- [Click to Pay test cards](https://developer.cybersource.com/docs/cybs/en-us/unified-checkout/developer/all/rest/unified-checkout/uc-reference-test-cards/uc-reference-test-cards-visa-ctp.html)

## Local validation recorded

- Latest base: clean Git commit `2f3559a`; source comparison found only a trailing
  whitespace difference in the older working source, not missing functional edits.
- Separate branch: `feature/hnb-cybersource-sessions`.
- 497 Python unit tests passed (26 new CyberSource tests).
- 61 frontend tests passed (2 new checkout tests).
- Static validation: 374 Python sources and 111 JSON documents passed.
- Ruff undefined-name/export checks passed.
- Vue/Vite production build passed; existing large-chunk advisory remains.

These are local contract/mock tests and build checks. No real Frappe database
migration, browser-hosted CyberSource checkout, P12 authentication against the
sandbox, 3DS/wallet transaction, reporting fixture, settlement or HNB acceptance
has been verified. The working local LMS/preview and production were not changed.
