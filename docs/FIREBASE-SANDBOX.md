# Firebase browser push sandbox

Project: `sisu-lms`. Site: `hnb-checkout.localhost`. Production and ordinary
customer outbox delivery remain disabled: no `il_push_adapter` is configured.
The Admin JSON remains in owner-only Linux storage outside the bench.

Run `scripts/deploy-firebase-push-sandbox.py` using the sandbox virtualenv from
`~/sisu-hnb-sandbox-bench`. This checks source conflicts, validates public Web
fields and the VAPID public point, confirms the existing test login, performs a
Google OAuth credential refresh (no message), backs up source/config privately,
builds the Vue app, and enables only the selected user's browser self-tests.
It does not install dependencies, migrate payment schemas, or enable scheduler
delivery. Existing WhatsApp/payment source is excluded from its copy list.

Enter the four Web configuration values from Firebase Console > Project settings
> General > Your Web app: apiKey, projectId, messagingSenderId, appId. Enter the
public key from Cloud Messaging > Web Push certificates. These browser values
are public by design, unlike the Admin service-account private key. All terminal
prompts are hidden. The test login may be `Administrator` on this isolated site.

Restart only this bench. Open `http://localhost:8001/campus?firebase_test=1`
in Chrome (localhost is a secure-context exception), or the protected HTTPS
sandbox origin. Use one origin consistently; permissions/tokens belong to it.
Sign in as the configured tester. Enable notifications, validate without sending,
then send a foreground test and a background test. Actual test sending requires
a successful dry run for that user/token within the last hour. Only own active
web device records are accepted. Request IDs are reserved before network I/O;
uncertain sends are not retried automatically. No arbitrary message/recipient API
is exposed. Registration reuses the encrypted IL Device Token field and owner
checks. Token refresh is performed when Enable this browser is clicked again.

Firebase acceptance is not proof of receipt. Foreground receipt changes the panel
text; background receipt must appear as an OS/browser notification. Check browser
and OS notification permissions if acceptance succeeds but nothing appears. Then
revoke the device and confirm tests are denied. Customer sending must stay off
until the normal outbox adapter, preferences and tenant delivery path are enabled
and tested in a separately approved rollout. This patch deliberately exposes only
a single-account test sender.

The existing token-based LMS contract is retained with Firebase JS 13.0.0
`getToken`; do not mix installation IDs into IL Device Token. SDK loads use the
official gstatic CDN. CSP/network policy must allow that host and Firebase APIs.
The service worker has an explicit /assets/institute_lms/ scope and is passed
directly to getToken; it does not replace another root service worker. Notification
payloads use Firebase's background display once; clicks always open own /campus.

Local unit tests/build do not establish Google authentication, token registration
or real delivery. Those results must come from the running sandbox and browser.

References:
- https://firebase.google.com/docs/cloud-messaging/web/get-started
- https://firebase.google.com/docs/cloud-messaging/web/receive-messages
