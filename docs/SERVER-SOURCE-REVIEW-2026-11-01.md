# Server source review — 2026-11-01

Archive: local Downloads/sisu-server-source.tgz. Running server unchanged.

Compared source: 606 identical, 70 differing, 0 server-only. Generated assets and potential credential/config files were excluded.

## Differences from handover cb31f49

- `frontend/src/native/ProductWorkspace.vue`: server adds 3, removes 3 lines relative to handover; do not blindly copy over current source.
- `frontend/src/native/LiveRoom.vue`: server adds 2, removes 2 lines relative to handover; do not blindly copy over current source.
- `frontend/src/native/SubscriptionBilling.vue`: server adds 2, removes 4 lines relative to handover; do not blindly copy over current source.
- `frontend/src/native/Operations.vue`: server adds 1, removes 2 lines relative to handover; do not blindly copy over current source.
- `frontend/src/native/SubscriptionAdmin.vue`: server adds 3, removes 4 lines relative to handover; do not blindly copy over current source.
- `tests/test_final_services.py`: server adds 2, removes 13 lines relative to handover; do not blindly copy over current source.
- `tests/test_account_billing_service.py`: server adds 0, removes 33 lines relative to handover; do not blindly copy over current source.
- `tests/test_commercial_rules.py`: server adds 0, removes 6 lines relative to handover; do not blindly copy over current source.
- `institute_lms/materials.py`: server adds 0, removes 15 lines relative to handover; do not blindly copy over current source.
- `institute_lms/hooks.py`: server adds 0, removes 2 lines relative to handover; do not blindly copy over current source.
- `institute_lms/account_billing.py`: server adds 13, removes 30 lines relative to handover; do not blindly copy over current source.
- `institute_lms/institute_lms/doctype/il_material/il_material.json`: server adds 2, removes 8 lines relative to handover; do not blindly copy over current source.
- `institute_lms/api.py`: server adds 1, removes 16 lines relative to handover; do not blindly copy over current source.

Server billing differs from current LKR/usage billing. Server material schema lacks expires_at present in the current release. Current source includes newer access override and expiry checks. Keep these current protections; schema migrations and runtime acceptance are required before deployment.

This comparison does not establish database contents, active users, DNS, provider readiness or live tenancy. No accounts, trials, schemas or server files were modified by this review.
