# Real credentials and configuration checklist

**No provider was accepted live in this task.** Use secret management/site configuration; never paste secrets into chat or compile them into a client.

| Area | Required operator configuration | Acceptance |
|---|---|---|
| Control plane / tenant | Existing `il_control_plane`, `il_tenant_id`, `il_tenant_signing_keys`, tenant `il_control_plane_key`; `il_control_plane_url`; control `il_policy_delivery_hosts` | Two-site manifest revision, replay rejection, outage/retry/ack |
| Payments.lk | Existing separate student and platform merchant API/HMAC secrets and mode settings | Signed success/fail/cancel/replay, exact amount/currency/identity, duplicate protection; real merchant webhook routing |
| Premium pricing | Owner-assigned `IL Price Assignment` per tenant | Unconfigured offer unavailable; immutable quote; renewal and receipt |
| OpenAI | Existing encrypted IL SOUL Settings key, model, rates, feature-credit costs and limits | Responses, hosted retrieval, sources, ambiguity and quota behavior |
| LiveKit | `il_livekit_url` (wss), `il_livekit_api_key`, `il_livekit_api_secret`, `il_live_max_participants` | Real join/media permissions, reconnect, room end, recording, signed webhook |
| Live recording | `il_live_recording_s3`: bucket/access_key/secret/region and SDK-supported endpoint options; `il_recording_reservation_bytes` | Private egress, size, duplicate/out-of-order webhook and orphan reconciliation |
| Private media | `il_private_media_s3`: bucket/region/access_key/secret/optional endpoint_url; `il_private_video_adapter: institute_lms.private_media.grant`; `il_private_video_hosts`; `il_private_video_max_bytes` | Private versioned bucket, CORS, presigned POST, confirmed upload, short-lived playback, unauthorized rejection |
| Existing Frappe files | `il_storage_backend` defaults frappe; replacement adapters only after validation | Private file authorization and quotas |
| Mobile auth | `il_mobile_redirect_uris`, canonical HTTPS tenant, Google student login | Android/iOS browser callback, Sisu exchange and revocation |
| Email | Frappe Email Account/SMTP and DNS | Real queue delivery and bounce/failure |
| SMS/WhatsApp/push | Existing SMS/push adapters; Meta template/token/webhook configuration | OTP cooldown/expiry/attempts, delivery/retries, revoked devices |
| Google | Existing Google login, Calendar and YouTube OAuth configuration | Exact redirect hosts, state/CSRF, callback persistence, token refresh |

The live/media optional dependencies installed for local contract inspection were livekit-api 1.2.1 and boto3 1.43.108. That inspection generated only a local fictional token and inspected SDK types. It did not contact a live media provider. Pin and audit the full dependency set in the deployment environment.

V2: additionally configure and accept `il_lecture_refund_adapter` (vendor implementation required), exact matching egress/private-media storage, version listing/deletion permissions for explicit cleanup, signed commerce transport and subscription notice acknowledgement. Android SDK/device tests and iOS runner work remain.
