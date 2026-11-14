# Mobile campus selection

Use the existing SISU mobile access token on every request:
`Authorization: Sisu <access_token>` (do not mix browser cookies).

- GET `/api/method/institute_lms.campus_context.choices`: returns `message.institutes` and `message.selected`.
- POST `/api/method/institute_lms.campus_context.select`: JSON body `{"institute":"<institute ID from choices>"}`.
- POST `/api/method/institute_lms.campus_context.clear`: no institute argument; returns to overall campus.

Selection persists on the authenticated IL Mobile Session only. Keep using the same token; refetch dashboard/classroom data after success. Other devices and browser selection are unchanged. Selection requires an active membership; pending applications do not grant access. Clear does not remove memberships. Server reads use selected_institute(); operations requiring institute access use current_institute(), which revalidates membership.

No schema migration is required: the existing IL Mobile Session.institute field is used. Deploy institute_lms/campus_context.py and restart Frappe web/workers before mobile acceptance testing.

Local validation: 13 campus-context tests pass, covering existing browser behavior, device persistence, clear, choices and foreign/revoked/expired session rejection. Live mobile testing is still required: select, request data, restart the app, verify selection, clear, and attempt an unauthorized institute.
