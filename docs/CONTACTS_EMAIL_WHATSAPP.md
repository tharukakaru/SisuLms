# Contacts, invitations and notification setup

Updated 28 September 2026. The local preview sends no messages. It uses the clearly labelled code `123456`; that code is not accepted by the live backend.

## What is implemented

- My profile has private contact number, city/address, birthday, computed age and optional gender. Students must supply a birthday when saving this private form. Gender includes “Prefer not to say”.
- Under-16 students need a guardian name, relationship and phone. Optional guardian email is stored without claiming it is verified. WhatsApp notifications for these students use the matching guardian number and permission acknowledgement. Parent/guardian numbers do not require OTP verification and are not marked as verified. Other WhatsApp contacts still require OTP verification. The under-16 threshold is a product rule, not a claim of worldwide legal compliance.
- Public subject suggestions allow multiple selections and custom subjects. No DOB, gender, contact numbers or guardian fields are returned in the public directory.
- `IL Private Contact` is keyed uniquely by User and has no generic document permissions. Only the authenticated user's private API reads/writes it. Profile changes do not rename their login email.
- WhatsApp OTP requests use a Meta authentication template, rate limits, a one-minute resend delay, ten-minute expiry, five attempts and a server-secret HMAC. For adult students and providers, opt-in requires the exact verified phone. Under-16 students may opt in with the matching guardian number and permission without OTP. The outbox rechecks these rules before sending; the exemption does not create an account-verification record.
- Email address verification and opt-in use the existing contact API and Frappe Email Queue. Classroom scheduling, updates, materials and payment events already use the notification outbox. Sending is asynchronous; workers run every five minutes.
- Institute dashboard: invite a teacher by email. Teacher dashboard: review invitations or request an institute by its owner's registered login email. Pending invitations expire after seven days; duplicates are rejected. The invited teacher must sign in with the addressed email and have a verified teacher profile. Acceptance creates a membership request for institute review, not automatic teaching access. Invitations require HTTPS and outgoing email. Direct join requests still appear in the institute dashboard, with an email queued when SMTP is configured.
- Requests by institute email look up verified institute profiles on this Frappe site. Cross-site federation is not implemented. Existing multiple-institute deployment boundaries remain in effect.

## Recommended economical starting setup

Use Frappe's Email Account with an existing suitable business SMTP service for email, and connect directly to Meta WhatsApp Cloud API for automated WhatsApp notifications. This avoids a third-party WhatsApp handling markup; it does not remove Meta's charges or operational costs.

Meta prices depend on recipient market and message category. Use their current rate card rather than hard-coded prices in SISU: https://whatsappbusiness.com/products/platform-pricing/

Twilio currently lists a $0.005 handling fee for each inbound/outbound WhatsApp message in addition to Meta's fees: https://www.twilio.com/en-us/whatsapp/pricing

For illustration, 10,000 billable outgoing messages would add $50 of Twilio handling fees, excluding Meta charges, inbound traffic and other fees. Direct Meta avoids that specific markup. This is an arithmetic illustration, not a Sri Lankan tariff quote. Recheck rates at activation; do not budget on the assumption that automated messages are free.

To keep costs down: use email for detailed content, WhatsApp for essential class changes/receipts, avoid repeated announcements, and keep marketing separate from transactional opt-in. The current outbox deduplicates the same event; it does not yet batch separate updates into digests or enforce a monthly spend cap. Never automate WhatsApp Web sessions or unofficial bulk-sending tools.

## Email: configure once on the live Frappe site

1. Choose a sender mailbox such as `notifications@your-domain` and obtain its provider's SMTP settings. For volume, use a transactional SMTP relay with sufficient limits. No new self-hosted mail server is needed.
2. In Frappe Desk, search **Email Account**, create the sender account, enable outgoing and make it the default outgoing account. Use the provider's SMTP host, TLS/SSL mode and port. Keep SMTP authentication enabled. Use an app password, SMTP credential or supported OAuth; do not paste secrets into SISU public profile fields or chat.
3. Use the provider's instructions for domain authentication (SPF/DKIM/DMARC) and verify the sender. Configure the correct public HTTPS site URL so invitation links point to your installation.
4. Run the Frappe scheduler and workers. Inspect **Email Queue** for delivery errors. “Queued” means queued, not delivered.
5. Test with a mailbox you own: verify a schedule email, opt in, then trigger a test class update. Separately test an invitation to an authorized test teacher.

Official setup: https://docs.frappe.io/erpnext/email-account
Microsoft OAuth: https://docs.frappe.io/framework/user/en/microsoft-email-oauth

## WhatsApp: what you need

1. A Meta business portfolio, WhatsApp Business Account and a business phone number eligible for Cloud API. Complete Meta's onboarding/display-name and business checks applicable to your account. The ordinary WhatsApp Business mobile app alone is not the API integration.
2. A Meta app configured for WhatsApp, its phone-number ID, a suitable server-side access token, the correct permissions and a billing method when required. Your deployment operator should configure these privately.
3. An approved **authentication** template with a copy-code button for number verification. This implementation sends the code as body parameter 1 and URL-button parameter 0. Confirm the exact approved template in a sandbox before enabling real users.
4. Approved notification templates in English, Sinhala and/or Tamil. The existing sender expects one body text parameter per template. Templates must accurately describe the permitted notification use and match Meta's category/content rules; arbitrary promotional text must not be sent through a utility template. Adjust the sender's parameter schema if Meta approves a different structure.
5. A current supported Graph API version selected from Meta's app dashboard/documentation. Do not copy a stale version from a tutorial.

Configure these server-side Frappe site settings; the following is a placeholder schema, not ready-to-use credentials:

```json
{
  "il_whatsapp_token": "SERVER_SIDE_SECRET",
  "il_whatsapp_phone_id": "META_PHONE_NUMBER_ID",
  "il_whatsapp_graph_version": "SUPPORTED_GRAPH_VERSION",
  "il_whatsapp_auth_template": {
    "name": "YOUR_APPROVED_AUTHENTICATION_TEMPLATE",
    "language": "en_US"
  },
  "il_whatsapp_templates": {
    "en": {"name": "YOUR_APPROVED_EN_TEMPLATE", "language": "en_US"},
    "si": {"name": "YOUR_APPROVED_SI_TEMPLATE", "language": "si"},
    "ta": {"name": "YOUR_APPROVED_TA_TEMPLATE", "language": "ta"}
  }
}
```

Use only languages actually approved in your WhatsApp account. Tokens are never returned in frontend responses; protect site configuration and backups and rotate the token when needed. Frappe's encryption key must be configured for code HMACs. WhatsApp notification and OTP integration are separate from the earlier SMS signup hook (`il_send_verification_sms`); signup SMS still requires its own provider hook.

Before go-live: migrate the new DocTypes (`bench --site YOUR_SITE migrate`), restart workers, use an HTTPS site, test an authorized number, verify it in My profile (or supply the matching under-16 guardian number and permission), opt in and save. Trigger a class change and inspect **IL Notification**. Status **Accepted** means Meta accepted the request, not delivery/read confirmation. Status **Review** means the outcome is uncertain; reconcile in Meta before retrying to avoid duplicate charges. Delivery/read webhook reconciliation is not implemented by this change.

## API map

All are authenticated POST calls under `/api/method/institute_lms.` with normal CSRF checks.

| Method | Purpose |
|---|---|
| `private_contact.get_details` | Current user's private details and verified number |
| `private_contact.save_details` | Validate/save personal and guardian data; sync WhatsApp preferences to that user's active memberships |
| `private_contact.request_whatsapp_code` | Request Meta authentication OTP |
| `mobile_verification.verify` | Verify OTP; store exact verified phone |
| `contact.status`, `contact.request_verification`, `contact.verify`, `contact.preferences` | Existing verified email preference flow |
| `invitations.invite_teacher` | Institute admin queues invitation email |
| `invitations.list_invitations` | Institute's sent invitations or current teacher's received invitations |
| `invitations.respond` | Addressed verified teacher accepts/declines pending invitation |
| `invitations.request_by_email` | Verified teacher requests a matching verified institute |

## Validation and remaining deployment work

Automated tests cover age boundaries, guardian requirements, verified-phone enforcement, private-data isolation and invitation recipient/expiry/replay rules. Local preview exercises form saving and role-specific invitations without external transmission. There is no live Frappe database, SMTP account or Meta credential in this workspace, so migrations, real delivery, provider template approval and production concurrency must be verified on a staging site before launch. Add private contacts/invitation history to your deployment's privacy export and account-retention procedures before onboarding real children.


## 16 October update: provider dashboards, bank reviews and WhatsApp templates

### Step 1 — Update the live application

Back up the staging site and database, deploy this source, install frontend dependencies using the lockfile, and build with `npm run build --prefix frontend` from the app folder. From the Frappe bench directory run `bench --site YOUR_SITE migrate`, then restart workers using your deployment service manager. This update adds `IL Bank Slip.rejection_reason` and `IL Notification Event.classroom`; the new code requires these fields. Follow DEPLOYMENT_RUNBOOK.md for the installation-specific asset and process commands.

The local URL on port 5182 uses fictional preview data. It does not prove that your live Frappe database, bank or WhatsApp service is connected.

### Step 2 — Review bank payments

Open **Class fees → Bank payment reviews** as a teacher assigned to the class or an institute administrator. The review shows the student's name, LMS member ID, saved contact number, submission time, invoice, transfer reference, amount and status. Only the current student's own rows or staff's permitted classes are returned. Private birthdays, guardian records and addresses are not included in this table.

Use **View** to inspect the details and protected slip. Use **Approve** only after checking the actual bank credit; select the class access duration and record the verification note. For a course, session or custom duration, supply the end date. Approval records access and collection; it does not transfer money. Institute-owned classes pay the institute, which arranges teacher compensation.

Use **Reject** and select unreadable slip, wrong amount, money not received, wrong bank account, duplicate, wrong class/invoice, or Other. Other requires an explanation. The reason is saved and included in the student's review notification. Notification delivery still depends on channel preferences and connections.

### Step 3 — Create three approved Meta templates

Use your Meta WhatsApp Business account to create templates for payment approval, an existing student's enrolment/payment reminder, and a scheduled class. Have Meta approve the actual wording and each language before enabling it in SISU. Do not assume every reminder qualifies as a utility message. The current sender expects exactly one body text parameter: the server-generated class update. The approved template must include fixed surrounding text and that parameter in a structure Meta accepts. If your approved template uses several structured variables, update the dispatch adapter to match before activation.

The existing template sender documentation is available in [Meta's official API workspace](https://www.postman.com/meta/whatsapp-business-platform/request/lwtlz1k/send-message-template-interactive). Approval, language and category are determined by Meta; creating these SISU options does not create or approve templates in Meta.

### Step 4 — Configure server settings

Keep the existing private token, phone-number ID and supported Graph version settings described above. Add this event mapping in the site's server configuration, substituting your approved template names. Do not put credentials in the frontend or commit them to source control.

```json
{
  "il_whatsapp_event_templates": {
    "whatsapp.payment_approved": {
      "en": {"name": "YOUR_APPROVED_PAYMENT_TEMPLATE", "language": "en_US"}
    },
    "whatsapp.enrolment_reminder": {
      "en": {"name": "YOUR_APPROVED_ENROLMENT_TEMPLATE", "language": "en_US"}
    },
    "whatsapp.class_scheduled": {
      "en": {"name": "YOUR_APPROVED_SCHEDULE_TEMPLATE", "language": "en_US"}
    }
  }
}
```

The outer language key must match `IL Member.language`. Add only approved languages. The current new message body generator uses English; translated bodies need implementation and review before Sinhala/Tamil template rollout. Retain `il_whatsapp_templates` if existing automatic class updates use it. The new manual template option does not replace those automatic notifications.

### Step 5 — Test with your own consenting test student

1. Assign the class owner a Gold or Platinum provider account. The owning institute's plan applies to its classes; an independent teacher's plan applies to their own classes.
2. Add an active student enrolment. Save WhatsApp opt-in and an eligible number using My profile. Existing adult verification and guardian permission rules apply.
3. Schedule a future session in the classroom.
4. On the teacher/institute overview, open **WhatsApp updates**, choose the class, student and scheduled session, then **Preview message**. Check the message before queueing.
5. For a payment approval, approve a test bank slip and use its **WhatsApp update** action. The backend rejects an approval message for a pending, rejected or unrelated payment.
6. Test the reminder option for that existing enrolment. This is not an arbitrary-number or prospect marketing sender.
7. Queue one message to your authorized test number. Inspect **IL Notification** and Meta. The scheduler runs the WhatsApp dispatcher; workers must be running. Queued and Accepted do not mean delivered. Reconcile ambiguous Review outcomes before retrying. This change does not add a new delivery webhook implementation.
8. Verify denial for Silver, an unassigned teacher, another class's student, a suspended provider, missing language template and disabled consent. Recheck after queueing: the worker also enforces owner plan, suspension, current enrolment and recipient preferences.

Duplicate clicks reuse the same recipient/context event: payment messages per approved slip, schedule messages per session revision, and reminders once per classroom/student/day. A skipped or failed duplicate is not automatically retried as a new message; the administrator must inspect the existing outbox result.

### Step 6 — Check the overview

Teacher and institute overviews show student counts, class/team counts, remaining sessions today, completed scheduled time slots, pending slip reviews, upcoming lessons and verified collection charts. Teaching hours are scheduled durations, not measured meeting attendance. Collection charts show recorded gross collections, not bank balances. The sample Teen Master Business promotional card has been removed from these overviews. Existing programme records are preserved.

### Validation limits

338 backend unit tests and 100 frontend checks passed for this update. Tests cover rejection rules, class/student scope, plan/suspension checks, consent and template prerequisites, and message deduplication. Local browser checks use fictional records and send no external messages. A live Frappe/MariaDB migration and approved Meta template delivery remain staging acceptance steps; no live database or Meta credentials were available here.
