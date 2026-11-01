# Verified signup sandbox

Opt-in only for hnb-checkout.localhost. Existing signup remains unchanged when disabled.

Implemented: role-specific required fields, optional profile fields, immutable verified contacts, email and SMS codes with expiration and attempt limits, password confirmation, account creation and return to standard Frappe login. Provider trials are ended at creation; existing subscription policy remains the payment gate. Provider endorsement is separate from contact verification.

Only configured test contacts can receive codes. WhatsApp sending is not enabled. The general email queue and scheduler remain suspended. No production configuration or payment implementation is changed.

Run scripts/deploy-verified-signup-sandbox.py from the sandbox bench for read-only prerequisite checks. Add --deploy only when ready; the script checks conflicts, makes a private backup, builds the sandbox frontend, and asks for hidden test contacts. A source conflict stops deployment. Restart only the sandbox after deployment.

Requirements: exactly one isolated institute record, an operational SMS adapter, Brevo outgoing account, privacy policy URL/version, server encryption key, and a new test email. Institute administrator signup additionally needs an explicit il_self_signup_institute_email assignment and no existing institute administrator. Never assign a new public registrant to an existing customer workspace.

Validation so far: 569 Python tests and 64 frontend tests pass; Vite build passes. New tests cover per-role required fields, privilege stripping, contacts/consent, password confirmation, dual-proof requirements, OTP expiration, attempt exhaustion, and no account creation with missing phone proof. These are not live signup or SMS tests.

Outstanding runtime checks: email OTP receipt, SMS OTP receipt, account creation for each role in isolated fixtures, subsequent login, password reset, provider payment-required enforcement and verified sandbox payment. Provider endorsement/review remains a separate restriction. No launch or production readiness is claimed.


## Role and Google follow-up

Run `scripts/test-signup-roles-sandbox.py` in the sandbox bench. It accepts two new, distinct email addresses through hidden prompts and preserves the configured student and SMS recipient. The institute test is refused if an institute administrator already exists. It does not create an administrator until that assigned email completes both OTP checks. Unknown source changes stop installation.

After restarting only the sandbox, register the teacher and institute using their respective emails. Both must land on the plan/payment screen and remain locked while unpaid. Run the script with `--check` to verify backend roles and subscription availability. This is not evidence that a payment works.

Run with `--reset` to request one native reset email for an existing allowlisted test account. Only that newly created queue record may be sent; the general queue stays paused. A one-hour reservation prevents automatic duplicate retries. Complete the link in the browser, verify new-password login and rejection of the old password. SMTP acceptance alone is not delivery or password-reset success.

Google now appears alongside password login and on the signup form. Signup uses the existing Frappe Google OAuth callback, then the same required role details and both OTP checks. A trusted Google session must match the email exactly and cannot overwrite an existing member/profile. Existing accounts should use Google sign-in on the login page. Google provider/callback configuration and live OAuth remain to be verified. The signup form also sets a local password so the requested return-to-login flow supports both methods.

Local verification after follow-up: 576 Python tests, 64 frontend tests, Vite build. No live teacher/institute registration, OAuth callback, reset link or payment success is claimed from these local tests.
