# Meta WhatsApp webhook

Callback path: `/api/method/institute_lms.notification_service.whatsapp_webhook`

The current sandbox address would yield:
`https://boot-oecd-chelsea-invision.trycloudflare.com/api/method/institute_lms.notification_service.whatsapp_webhook`

This is NOT yet ready to enter in Meta: the sandbox has not received this patch,
and Cloudflare email Access blocks Meta's server requests. Keep that protection.
Use a dedicated public HTTPS hostname/route restricted to this exact webhook path
(GET and POST only, 256 KiB body limit), or a separate webhook-only reverse proxy.
Do not expose the entire development server/debugger. Preserve raw POST bytes and
X-Hub-Signature-256, do not redirect the challenge, and route to this Frappe site.
A stable hostname is preferable: quick-tunnel URLs change on restart.

## Configuration (server only)

Apply the changed modules, hooks and new IL WhatsApp Receipt DocType to the sandbox,
then run `bench --site hnb-checkout.localhost migrate` and restart its processes.
Run `env/bin/python apps/institute_lms/scripts/configure-whatsapp-webhook.py`
from `~/sisu-hnb-sandbox-bench`. It prompts without echo for the verify token and
Meta App Secret and writes site_config.json with mode 0600 atomically.

- `il_whatsapp_verify_token`: a random 32+ character token from a password manager.
  Enter the SAME value in Meta's Verify token field; it is not the access token.
- `il_whatsapp_app_secret`: Meta Developer App settings > Basic > App Secret.
- `il_whatsapp_waba_id`: the WhatsApp Business Account ID.
- `il_whatsapp_phone_id`: the registered Phone Number ID, not its telephone number.

One institute per Frappe site is enforced by existing institute resolution. Provision
that institute before receiving messages. No payload-provided tenant ID is trusted.
In Meta WhatsApp webhook configuration, verify the callback and subscribe to the
`messages` field. Ensure the app is subscribed to the intended WhatsApp business
account. Template approval is separate from webhook verification.

The existing `il_whatsapp_token`, graph version, opt-ins, verified phone and approved
template mappings control outbound sending. This helper does not enable sending.
The submitted `sisu_otp_verification` Authentication template must not be mapped to
the generic notification body: its authentication parameters/buttons require the OTP
adapter's matching schema. `sisu_class_reminder` must match its approved parameters
and language. Neither template is assumed approved or sent by these changes.

## Processing and retries

GET returns a raw text challenge only after constant-time token and mode checks.
POST checks the App Secret HMAC-SHA256 signature over unchanged request bytes.
Only the configured WABA/phone's messages changes are accepted for processing.
Incoming text (up to 4096 characters) and bounded message metadata are stored in a
private receipt with no client CRUD permissions. Media is not downloaded; no auto
reply, phone verification or enrollment action is triggered by incoming messages.
These receipts are durable intake, not a user-facing chat inbox.

Receipt primary keys hash account, phone, kind, message ID and status. Duplicate
notifications have no repeated effect. Delivery updates require one matching
WhatsApp outbox record in the same institute and matching member/recipient phone.
Statuses advance monotonically. No webhook retries an outbound send. Existing
sender backoff/uncertain-delivery rules remain unchanged.

Unknown/early status IDs remain Pending. The reconciliation job runs every five
minutes when the site's scheduler is enabled; on the paused sandbox run:
`bench --site hnb-checkout.localhost execute institute_lms.whatsapp_webhook.reconcile`
Database errors are not acknowledged: transactions roll back and Meta may retry.
Unmatched receipts require operator review; no ambiguous cross-tenant mapping is
attempted. Apply the site's privacy/retention policy to incoming-message records.

## Acceptance checks still required

- Real Frappe migration, anonymous GET returning raw text (not JSON/HTML).
- Missing/wrong signature rejected; signed real Meta message accepted.
- Actual WABA subscription, live callback through webhook-only HTTPS route.
- Same callback twice produces one receipt; out-of-order statuses don't regress.
- Send approved test template to an opted-in test number; verify delivered/read.
- Paused-scheduler reconciliation and callbacks arriving before sender commit.
- Confirm generic REST/guest access cannot read receipt contents.

No production configuration or deployment was performed. Local tests use a Frappe
database double; they do not replace these runtime checks.


## Prepared sandbox deployment (webhook-only gateway)

The Codex Windows session cannot access the user's WSL distribution (E_ACCESSDENIED).
These commands must run in the user's existing Ubuntu terminal. They have not yet
been executed on that sandbox. The 525 passing Python tests include 11 gateway
boundary tests; they are not live deployment results.

1. From `~/sisu-hnb-sandbox-bench`, run the Windows-mounted source script
   `scripts/deploy-whatsapp-sandbox.py` with `env/bin/python`. It checks handler/new
   file conflicts before modifying anything, backs up source and site configuration
   in `local-private/whatsapp-backups`, runs `bench backup --with-files`, imports only
   IL WhatsApp Receipt with reload-doc, and clears cache. It does not run unrelated
   full-site migration hooks or modify payment files. Failed operations stop; do not
   blindly rerun after a partial failure. Inspect the private backup and error first.
2. Its configuration prompts accept a password-manager-generated 32+ character verify
   token and the App Secret without echo. Save the verify token in that password manager
   for Meta's Verify token field. Do not print it in terminal commands. WABA and Phone
   Number IDs are separate prompts. No outbound access token or template is enabled.
3. Restart only the sandbox `bench start` process. Leave the email-protected tunnel
   running. Run in another terminal:
   `env/bin/python apps/institute_lms/scripts/whatsapp-webhook-gateway.py`
4. In another Ubuntu terminal run:
   `env/bin/python apps/institute_lms/scripts/verify-whatsapp-endpoint.py`
   This checks gateway GET, invalid signatures, a signed empty POST forwarded through
   Frappe, altered bodies and forbidden routes without printing secrets or URL queries.
   It creates no message, notification, payment or enrollment data.
5. After local probes pass, start a SECOND tunnel to the gateway only:
   `$HOME/.local/bin/cloudflared tunnel --url http://127.0.0.1:8102`
   Intentionally no allowed-mail flag on this webhook-only tunnel. Do not change the
   protected tunnel on port 8001. All paths except the exact webhook path are rejected.
6. Use the newly printed HTTPS origin with:
   `env/bin/python apps/institute_lms/scripts/verify-whatsapp-endpoint.py --origin https://NEW-HOST.trycloudflare.com`
   The helper permits HTTPS trycloudflare hosts only and never prints request secrets.
   The challenge probe sends the token only to the URL supplied; double-check that it
   is the hostname printed by your tunnel. Do not enable HTTP debug/access logging.
7. Exact callback = that NEW origin plus
   `/api/method/institute_lms.notification_service.whatsapp_webhook`.
   Paste the saved Verify token into Meta, then Verify and save. Subscribe to messages.
   Only successful Meta verification confirms the subscription handshake.

The gateway binds only 127.0.0.1:8102. It answers GET verification using the backend
configuration, without forwarding the secret query to Frappe's URL access logs. POST
signature checks happen at both the gateway and Frappe. Incoming headers/cookies and
query dispatch overrides cannot select another Frappe method. Upstream errors are
sanitized. Its bounded payload/timeouts and request concurrency are appropriate for
sandbox testing; use a managed, rate-limited production ingress for launch.

Real message receipt requires exactly one configured IL Institute on this test site.
An empty signed probe does not establish that business provisioning is complete.
Scheduler remains paused; reconcile pending statuses explicitly during sandbox tests.
The actual generated public URL, deployment completion, live HTTP probes and Meta
verification are all pending until the user runs these steps and supplies the results.


## System User token: read-only verification, no sending

After completing the webhook configuration prompts, run the source script
`scripts/verify-whatsapp-access.py` using the sandbox's env/bin/python. It prompts
for the SisuAcademy App ID, supported Graph API version shown in Meta, actual WABA,
Phone Number ID and registered business telephone number. It fails if IDs differ
from the webhook configuration. Paste the System User token only at its hidden
prompt; no command-line or environment-variable token is used.

It calls Meta debug_token with the App Secret from site configuration, checks
validity, app binding, whatsapp_business_management/whatsapp_business_messaging,
and both expiration fields. Missing expiration metadata stops staging rather than
being interpreted as never expiring. Zero is reported as no fixed expiration, not
a promise against revocation. It reads the selected WABA and its phone-number edge,
matching both the selected Phone Number ID and the actual registered telephone.
The user must confirm the displayed account/name/number against WhatsApp Manager's
real business assets. IDs alone cannot prove production-vs-test ownership.

On success it stores only `il_whatsapp_pending_credentials` in site_config.json,
atomically with mode 0600. This is intentionally NOT the active il_whatsapp_token
key, so existing outbox workers cannot start sending with it. Existing dispatch
configuration is preserved. No messages, template changes or production writes.

The checker uses fixed HTTPS graph.facebook.com URLs, no redirects/environment
proxies, disabled HTTP logging, sanitized failures and hidden inputs. Meta's debug
endpoint requires input_token as a request parameter: it is sent only to Meta via
TLS, never printed. Do not run with external HTTP tracing enabled. These live
checks remain pending until the user runs the script; 534 local unit tests passed
including nine token/asset validation tests.


## Switching to the new SisuLms app/account (31 October 2026)

Run the source `scripts/verify-whatsapp-access.py --new-account` from the dedicated
sandbox bench. App ID, App Secret, System User token, WABA ID, Phone Number ID,
registered number and chosen webhook verify token are hidden prompts. Use all NEW
app/account values; no previous numeric IDs are defaults. Graph version remains an
ordinary nonsecret prompt. Verification is read-only against Meta and completes
before any configuration write. App/token permissions, expiry, WABA access and the
phone ID/number belonging to that WABA must pass. These checks establish API access
and asset relationships, not legal ownership of the business portfolio.

After confirmation, the previous site config is backed up with restricted permissions
under local-private/whatsapp-config-backups. New webhook fields replace the old ones
atomically; the access token remains under il_whatsapp_pending_credentials. Existing
active outbound tokens cause an explicit stop for review. Payment keys and unrelated
configuration remain unchanged. Do not rerun the original deployment script solely
to switch credentials; the webhook schema/code remains the same.

Clear the sandbox cache and restart its bench after a successful switch. Start the
existing gateway on 8102, run the local probes, then start the separate webhook-only
quick tunnel. The old email-protected URL is not a Meta callback. The exact new
callback hostname cannot be known until cloudflared prints it. Enter that new origin
plus the fixed webhook path in Meta, and paste the SAME verify token from your
password manager into Meta's Verify token field. Subscribe to messages only after
Verify and save succeeds. Keep the original LMS tunnel protected.

537 local Python tests passed after adding the account-switch checks. New credentials
have not been supplied to the agent; new live verification and Meta handshake remain
pending. No production deployment or message sending was performed.
