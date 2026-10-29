# Final acceptance checklist

All items below are **pending real staging acceptance**, even when unit tests cover part of the rule.

- [ ] Fresh and upgraded Frappe sites migrate without data loss; repeat patch safely; compatible Frappe/LMS commits recorded.
- [ ] Two tenants remain isolated; Institute Admin cannot use owner APIs; platform metadata does not disclose private course/chat content.
- [ ] Free Starter works after Premium expiry; organization suspension and stale signed lease still block access; failed renewal preserves paid dates.
- [ ] Unconfigured price is unavailable; owner changes price without rewriting old quote/invoice; only verified webhook activates Premium; duplicate callbacks produce one transaction/receipt.
- [ ] Signed policy delivery survives timeouts, replay and reordering; acknowledgement/revision visible; paid tenant refreshes without relogin.
- [ ] Individual allocation denies zero/exhausted allocation; Shared ignores personal cap; concurrent requests cannot exceed monthly organization budget; switching modes preserves history.
- [ ] Lesson checkout is separate from course and SaaS billing; order locks amount/version/beneficiary; another student cannot use purchased access; archived sold lesson remains accessible; expired/revoked entitlement denied.
- [ ] Failed/cancelled/replayed/late payment and second-charge reconciliation are tested. Refund workflow is not automated; agree and implement the authorized operational process before selling lessons.
- [ ] Private MP4/WebM upload quota reserves before upload; wrong size/type rejected; signed playback expires; no public bucket; orphan/reservation cleanup procedure proved.
- [ ] Teacher live camera/mic/screen share/device switch/reconnect; Student cannot start recording; unpaid/foreign classroom denied; verified egress produces private Ready recording; duplicate/out-of-order callbacks reconciled.
- [ ] Paper generation 10/100 questions, source changed/deleted, insufficient credits, duplicate prompts, worker crash, ambiguous provider outcome; teacher reviews/edits before publish; student answer keys remain protected.
- [ ] Mobile PKCE browser approval, Google student policy, callback handling, expired/revoked sessions and tenant switching on actual Android/iOS devices.
- [ ] Mobile missing RTC/editor/checkout/player workflows completed and accepted before claiming full mobile parity.
- [ ] Email, SMS, WhatsApp, push, OpenAI, Payments.lk and Google acceptance recorded separately with timestamp/environment/evidence.
- [ ] Backup/restore drill, worker/scheduler monitoring, health, TLS, DNS and tenant-by-tenant rollback rehearsed.

Local preview success verifies only fictional UI behavior. No item above should be checked merely because a preview or mocked test passes.
