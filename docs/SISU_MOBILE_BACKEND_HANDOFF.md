# V2 mobile integration update

This section supersedes the historical status table below. All calls still use the existing ParityService/FrappeClient and site-scoped Sisu authentication. Native screens are implemented and unit/web-build tested; real backend/device acceptance is pending.

| Flutter component | Methods / contract | V2 behavior |
|---|---|---|
| SubscriptionPage | billing_bridge.request summary/quote/checkout/receipt; checkout payload mobile=true | Confirm immutable quote, hosted handoff, server refresh, history, share HTML receipt |
| LessonsPage / editor | lectures.listing/detail/save/checkout/history/receipt; private_media.begin/complete | Cards, owned/archive, native editor, streamed signed upload, receipt |
| ProtectedPlayer | lectures.playback or live_classes.recording | HTTPS short-lived URL, foreground pause, retry requests fresh authorization |
| CreditManagement | ai_credits.management search/role/page, configure | Server allocation totals, validation/history, mode toggle |
| LiveClassesPage / SisuLiveRoom | live_classes.listing/join/control/room_status/recording/publish_recording/lecture_draft/reconcile/cleanup_failed | SDK media, server controls, 10-second status refresh, teacher review, cleanup confirmation |
| PaperWorkspace | paper_generator.sources/create/listing/status/resume/printable; papers.detail/draft/publish/archive | Mixed blueprint, queue, editable answer key draft, reviewed publication, HTML share |
| AiWorkspace / Hub | full_api.capabilities, ai.allowance | Premium routes and effective individual/shared credit state; refresh on resume |

Payment return uses fixed tenant `/mobile_payment_return` with `sisu.payments://return`. Any app/website could invoke a custom scheme: therefore it carries no trusted payment assertion and triggers only an authenticated server reload. Keep the existing AppAuth redirect allowlist. Device acceptance must verify correct origin, expiry/revocation, deep links, canceled checkout, still-pending settlement and subsequent policy delivery.

New live/media/provider controls require configured services. Presentation mock service is imported only by main_presentation.dart; it never falls back in production. No permanent signed URL/provider token should be persisted. Advanced print design, automatic video transcription and native iOS extensions remain outside the supported implementation.

---
## Historical handoff (pre-V2 implementation statuses)

# Mobile backend handoff

The web and Flutter app share the same site-scoped Frappe backend. No Firebase/Supabase or shared tenant database was added. Backend authorization is authoritative.

## Authentication

`lib/auth.dart` now defaults to `SISU_AUTH_PROTOCOL=sisu`. AppAuth generates PKCE S256 and state in the system browser, calling `mobile_auth.app_authorize`. This adapter accepts the standard AppAuth parameter names, then reuses `authorize` and the existing CSRF-protected `approve` page. Registered redirects, Google student policy, user-enabled checks and 120-second authorization codes remain enforced.

Flutter exchanges the returned code plus verifier through `mobile_auth.exchange`; a successful response has `access_token`, `token_type: Sisu`, `expires_at`, `site`. `FrappeClient(..., tokenKind: MobileTokenKind.sisu)` sends `Authorization: Sisu <token>` only to the configured HTTPS origin. The token stays in memory. `mobile_auth.logout` revokes the hashed server-side session. Default server expiry is seven days; restart requires login. No shared privileged API key or client secret exists.

AppAuth state validation is retained; backend permits URL-safe states of 22–128 characters (128-bit AppAuth state is 22 characters). The redirect is `lk.sisulearning.app:/oauthredirect` and must be allowlisted in `il_mobile_redirect_uris`. Existing OAuth is preserved as an explicit `SISU_AUTH_PROTOCOL=oauth` compatibility option with `SISU_OAUTH_CLIENT`; do not switch protocols merely to bypass student policy. Real browser callback/device acceptance remains required.

## New services and connected views

All method names below are relative to `/api/method/institute_lms.`; Frappe returns successful values in `message`. Existing `ParityService` and `FrappeClient` remain the transport.

| Capability | Method / key input | Main response | Mobile status |
|---|---|---|---|
| Current role/features | `full_api.capabilities` | role, plan, premium_ai, organization_available, revision, features | Hub uses resolved premium visibility |
| Institute Plan | same | friendly features and resolved dates/state | Connected data view |
| Subscription/billing | `billing_bridge.request` `{action:"summary"}` | offer, subscription, payments, receipts, policy_delivery | Connected read view; native checkout/receipt UX still incomplete |
| Lesson Store | `lectures.listing` | product list, price_minor, currency, owned, locked | Connected list |
| My Purchases | `lectures.listing` `{purchases:true}`; `lectures.history` | owned products / receipts | Connected list; detailed receipt UX pending |
| Checkout | `lectures.checkout` `{product}` | redirect_url or owned | Opens approved HTTPS Payments.lk URL; no local paid activation |
| Playback | `lectures.playback` `{product}` | short-lived url, expires_in, title | Player wiring pending; never persist signed URL |
| Teacher library | `lectures.listing` `{library:true}` | owned products | Connected list; create/upload/edit mobile forms pending |
| Live classes | `live_classes.listing` | status, recording_status, can_control | Connected status list; mobile RTC controls pending |
| Live join | `live_classes.join` `{name}` | url, token, expires_in, can_publish, can_control | Contract ready; mobile SDK adapter not implemented |
| Recording | `live_classes.recording` `{name}` | protected video grant | Mobile player integration pending |
| Personal credits | `ai_credits.status` | mode, period, allocated, used, remaining, organization_remaining | Connected read view |
| Admin credits | `ai_credits.management/configure` | users, history; mode/allocations/reason writes | Connected read view; native edit forms pending |
| Paper generation | `paper_generator.create/status/export` | job name/status/progress/paper | Preview implemented; connected queue UI pending |
| Existing AI / notifications / OTP | `ai.*`, `notification_service.*`, verification services | Existing RUN 2/3 contracts | Preserved; still require provider/backend acceptance |

`FinalWorkspace` deliberately shows server-returned structured data rather than fabricated values. It is an integration view, not a finished native UX for every operation. The separate preview illustrates the intended states without pretending these missing connections exist.

## Permission and integration checks

Use the canonical tenant HTTPS origin; switching organizations requires a new authenticated session. Platform Owner remains web-first. Do not send browser cookies with Sisu tokens. Distinguish missing entitlement, expired signed policy lease, exhausted allowance and unconfigured provider; show server errors and offer refresh. A redirect never settles payment. Poll server state after checkout, and refetch capabilities after policy propagation. Do not display provider/vector identifiers as authorization.

Acceptance must cover Android callback matching/cancel/back/logout, Google student login, tenant isolation, expired/revoked tokens, negative entitlements, checkout pending vs verified success, quota errors, source citations, direct-route authorization, live microphone/camera permissions and background/resume. No live mobile backend/provider integration was tested here.
