# Brevo sandbox runbook and signup findings

Run scripts/configure-brevo-sandbox.py in the dedicated Ubuntu sandbox virtualenv.
The --inspect option is read-only and does not prompt for a key. Normal execution
inspects accounts/queue, refuses competing outgoing accounts, collects the SMTP
key and exactly one authorized recipient through hidden prompts, checks TLS with
certificate validation and SMTP authentication, and makes a private bench backup.
It uses the native Email Account Password field for encrypted credential storage.
The backup is under ~/.sisu-secrets/brevo-sandbox; exclude that directory from
shared backups. Do not copy site encryption keys or database backups to Git.

Server smtp-relay.brevo.com:587, STARTTLS, login be4def001@smtp-brevo.com,
sender SISU Academy <noreply@sisuacademylk.com>. Reply-To info@sisuacademylk.com is
configured only after the operator confirms that mailbox can receive email.
SMTP credentials are not an IMAP mailbox and do not prove inbound delivery.

The general Email Queue is suspended and scheduler must remain paused. The script
force-sends only its one explicitly created test queue record. It never flushes
the queue. A private reservation prevents a second send on rerun, including after
an uncertain network result. Do not delete that reservation to retry blindly.
Check native queue status and Brevo delivery logs first. Existing LMS dispatch
retains its recipient consent/verification and transactional outbox protections.
Native retry behavior must be tested with controlled fixtures before scheduling
is enabled; SMTP cannot promise exactly-once delivery after an ambiguous response.

Operator checks: verify noreply sender/domain in Brevo; check Transactional Logs
for the test subject and recipient at the run time; confirm Delivered plus inbox
receipt, and inspect bounce/blocked events if not. A Sent Frappe queue means SMTP
acceptance, not recipient delivery. No Brevo log access has been provided here.

Current signup review:
- Students currently use Google; password signup for students is not implemented.
- Providers receive an email code, then require owner approval. Approval sends a
  password setup email. Profile and mobile verification precede membership.
- Registration requires a configured HTTPS site URL, enabled signup, and published
  privacy policy. Do not enable those merely to pass an SMTP probe.
- Existing plans include trial logic. Immediate provider payment gating differs
  from the current flow and needs backend plus frontend changes and regression
  tests; a popup alone must never enforce access.
- Institute activation currently assigns this site's institute. Arbitrary public
  institute signup needs workspace provisioning, not automatic administrator access
  to an existing institute.
- WhatsApp/mobile verification and CyberSource sandbox verification remain separate
  blockers; Firebase delivery does not verify either service.

Pending runtime tests: registration code expiry/wrong code/single use, reset link
expiry/single use, mobile verification, required fields, role routing, provider
payment gating, class/assignment/payment event emails, retry and duplicate handling.
Use only operator-owned accounts and synthetic sandbox records. No bulk messages
or production deployment are authorized by this setup script.

References:
https://help.brevo.com/hc/en-us/articles/7924908994450-Send-transactional-emails-using-Brevo-SMTP
https://raw.githubusercontent.com/frappe/frappe/develop/frappe/email/doctype/email_account/email_account.json
https://raw.githubusercontent.com/frappe/frappe/develop/frappe/email/doctype/email_queue/email_queue.py
