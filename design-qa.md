# Signup and role selection visual QA

final result: passed

## Institute signup redesign

- Source: `C:/Users/nim20/AppData/Local/Temp/codex-clipboard-8a499328-9d04-4fe7-9a5e-4849742dd08e.png` (827 × 630). Blue screenshot frame is excluded from the app.
- Desktop: `local-private/institute-signup-desktop.png`, captured at 1440 × 1100 CSS viewport; full-page image 1424 × 1339. Comparison: `local-private/institute-signup-comparison.png`, source left and implementation right proportionally normalized to 827 × 778. Both full comparison and readable desktop capture inspected.
- Reuses provider branding, original illustration, lavender footer, white background, pale rounded fields and purple submit button. Institute fields are 50px high with 20px row margins. Individual teacher fields remain 40px high with 12px margins, verified in the browser.
- Mobile: `local-private/institute-signup-mobile.png` at 390 × 844; paired fields stack and there is no horizontal overflow. Legacy mobile bounds also checked without horizontal overflow. Legacy desktop upper form inspected in `local-private/institute-application-desktop.png`; full-page capture was unavailable for that mode, so its lower controls were checked through the rendered DOM and exercised in the local flow.
- Intentional differences preserve existing contracts: required username remains visible, current signup retains separate administrator first/last names, and country/time zone retain separate values. Optional fields stay accessible below the action. Existing policy, payment and review notices remain. Current signup uses “Verify email & continue” because further verification is required; legacy uses “Verify email & submit”.
- Current local-fixture flow passed: start → email verification → phone request → phone verification; save remained disabled without a password, and reset restored editable fields. Legacy local-fixture flow passed through code verification to the review-reference screen. No live accounts, emails or SMS were created, and no passwords were entered.
- Existing handler functions and form-model declarations match pre-change copies exactly. Captured requests preserve all 19 data keys and the Institute role in both modes. Backend and API payload construction are unchanged.
- All 116 frontend tests passed; production build passed with existing large-chunk warnings; browser error log was empty; whitespace check passed.
- No actionable P0/P1/P2 visual findings after accounting for required retained controls. Existing P3 differences remain: less-rounded bundled headline font and missing faint lower-right footer overlay. No visual correction iteration was needed.

## Compact teacher fields refinement

- Per user request, teacher text inputs/selects now measure 40px high (previously 50px), field-row margins are 12px (previously 20px), label gaps are 6px, and paired-input gaps are 8px.
- Verified computed dimensions and visual rendering at desktop 1440 × 1100 and mobile 390 × 844; no clipped text or horizontal overflow. Evidence: `local-private/teacher-signup-compact.png`.
- CSS-only refinement, shared by current and legacy individual teacher signup. Existing form logic and contracts remain untouched. Whitespace check passed.

## Individual teacher signup redesign

- Source: `C:/Users/nim20/AppData/Local/Temp/codex-clipboard-94126765-c8f0-4416-83d4-2a41e347ade3.png` (630 × 481).
- Current signup: `local-private/teacher-signup-desktop.png`; 1440 × 1100 CSS viewport, full-page capture 1424 × 1180 (scrollbar excluded, approximately 1× density). Comparison: `local-private/teacher-signup-comparison.png`, reference left and implementation right, implementation proportionally normalized to 630 × 522. Extra vertical content is preserved operational information and optional signup controls.
- Legacy application: `local-private/teacher-application-desktop.png`. Mobile: `local-private/teacher-signup-mobile.png` and `local-private/teacher-application-mobile.png`, captured at 390 × 844 with full-page scrolling. No horizontal overflow.
- Typography/layout: compact form at the top right, 36px heading, 12px labels, 14px inputs, 50px pale input fields, 54px purple pill submit button, and existing provider artwork/branding on the left. Small reference normalized to the existing desktop design scale. Separate readable desktop and mobile captures were inspected for field labels, validation controls, and input bounds.
- Colors/assets/copy: existing original provider illustration, purple text/button, lavender footer, white canvas, subtle input borders, and requested Tell us your story copy. Existing P3 differences in rounded headline font and faint footer overlay remain.
- Intentional contract-preserving differences: current self-signup keeps separate first/last-name fields in one group; both modes keep separate country/time-zone inputs in one group. Optional fields and existing Google/account-type controls remain accessible in disclosures below the primary action. Current signup says Verify email & continue because it starts the existing verification process; the legacy application uses Verify email & submit.
- Iteration 1: initial browser capture showed inherited form margins and label spacing overriding the shared layout. Increased specificity within the teacher-only wrapper and verified corrected alignment. A template conditional inspection also caught verification controls appearing before a token; restored the explicit token gate and verified those controls are absent initially and present only after the local challenge response.
- Iteration 2: moved optional disclosures after the primary action, retained their disabled state during verification, and kept the story panel at its reference height. Final combined comparison shows no actionable P0/P1/P2 findings under the requirement to preserve all existing fields and operations.
- Browser checks: empty-form validation, optional controls, current signup challenge → email verification → phone request → phone verification, save remaining disabled without a password, and reset restoring editable fields. Legacy application challenge → code verification → review-reference screen also passed. All calls used an isolated local fixture service, fictitious values, and test codes; no real email/SMS/account creation occurred and no passwords were entered.
- Captured local requests preserve all 19 data keys and Individual Teacher role in both signup modes. Compared every existing function and form-model declaration against pre-change copies: unchanged. API payload construction, verification handlers, backend code, and models were not edited.
- At this stage, institute signup remained on its original layout; it is now updated by the institute section above. Google-authenticated completion retains its existing layout.
- Final checks: 116 frontend tests passed, production build passed (existing chunk warnings), browser console error check empty, `git diff --check` passed.

## Teacher provider-account screen

- Source: `C:/Users/nim20/AppData/Local/Temp/Redesign.png` (1440 × 1100).
- Desktop evidence: `local-private/provider-desktop.png`, at 1440 × 1100 CSS pixels and approximately 1× density. Source and capture were compared together in `local-private/provider-comparison.png` (2880 × 1100, source left); the desktop capture was also inspected at readable size for card text and controls.
- Mobile evidence: `local-private/provider-mobile.png` (390 × 844). Both options are readable, with no horizontal overflow.
- State: guest, Teacher selected, temporary local policy fixtures. Production APIs are unchanged.
- Typography/layout: bundled Manrope, 36px provider heading, 20px option labels, 14px descriptions, two 102px cards with 20px spacing, original restored desktop positioning, and responsive single-column controls.
- Colors/assets/copy: requested provider copy, purple headings, pale option cards, and lavender footer. The supplied illustration was extracted without UI text at 460 × 460 and displayed at native desktop size. Footer reuses the existing vector with a lavender fill.
- No P0/P1/P2 findings. P3: existing bundled headline font is less rounded than the reference and the reused footer lacks its faint lower-right overlay. No correction iteration was needed for the new screen.
- Individual teacher and Institute or school open existing registration with `Individual Teacher` and `Institute` respectively. Verified for both current self-signup and legacy provider application modes without submitting either form. Returning from registration restores the provider screen.
- The legacy registration component accepts an optional initial provider selection to avoid asking users to choose twice; its default behavior, fields, validation, and API payloads remain unchanged.
- All 116 frontend tests passed; production build passed with existing chunk warnings; `git diff --check` passed. Live registration/authentication was not exercised.

## Learner sign-in addition

- Source: `C:/Users/nim20/Downloads/Sisu (1)/03 · Learner signup/Redesign.png`.
- Implementation: `local-private/learner-desktop.png`; both source and screenshot are 1440 × 1100, matching CSS viewport at approximately 1× density.
- Full comparison: `local-private/learner-comparison.png` (2880 × 1100, source left, implementation right). Both assets were opened together and compared; the separate desktop capture was inspected at readable size for the right-panel controls.
- Mobile: `local-private/learner-mobile.png`, 390 × 844, no horizontal overflow.
- State: guest, learner selected, Google enabled by temporary local QA fixtures. Production availability remains controlled by the existing policy response.
- Typography/layout: existing bundled Manrope, 36px desktop heading, 14px body/buttons, centered right panel, full-width 54px pill CTA, and separate alternate-path action match the supplied layout. Mobile heading wraps cleanly.
- Colors/assets/copy: purple CTA and back link, dark heading, muted subtitle, exact requested learner copy; shared logo, illustration, and left panel are unchanged.
- No new P0/P1/P2 differences. Existing left-panel font/footer P3 differences documented below remain outside this follow-up's scope. No visual correction iteration was needed for the new panel.
- Selecting learner by mouse or keyboard opens the new screen and focuses its heading. Choose another path restores the role chooser. Teacher and Institute still show their existing panels.
- Back to sign in retains `/login?redirect-to=/campus`. The Google button invokes the unchanged parent `google()` action. A local invalid-redirect fixture confirmed the existing error handling remains visible. Google-unavailable state disables the button and explains why.
- All 116 frontend tests pass; production Vite build passes with existing chunk warnings; browser console error check returned none; whitespace check passes.
- No live Google authentication, account creation, or backend writes were performed. API functions, payloads, models, and authenticated routing remain unchanged.

The following section records the earlier role-selection work; its learner interaction has now been replaced by the screen above.

## Evidence

- Source: `C:/Users/nim20/Downloads/Sisu/02 · Choose your path/Redesign.png` (1440 × 1100).
- Desktop: `local-private/role-selection-desktop.png` (1440 × 1100 CSS/pixel dimensions, approximately 1× density).
- Same-size combined comparison: `local-private/role-selection-comparison.png` (source left, implementation right; 2880 × 1100). No density scaling in the comparison.
- Mobile: `local-private/role-selection-mobile.png` (390 × 844).
- Tablet: `local-private/role-selection-tablet.png` (1024 CSS pixels wide; full-page capture).
- Preview: http://127.0.0.1:5181/ — local guest fixtures, light theme, no role selected. Fixtures are confined to ignored `local-private/`; they are not part of production code.

## Findings and fidelity

No outstanding P0/P1/P2 issues.

- Typography: bundled Manrope retains the reference's hierarchy, two-line introduction, readable card labels, and body copy. Mobile explicitly uses the same bundled font.
- Layout: white two-column desktop layout, original SISU logo and illustration, purple closing panel, three rounded cards, and back link. Mobile uses one column with all role controls visible and no horizontal overflow.
- Colors: purple branding, dark role headings, muted descriptions, pale card backgrounds, and subtle borders match the reference's palette.
- Images: existing source logo, illustration, and footer asset are reused without generated substitutes or screenshot-based UI.
- Copy: role headings, descriptions, welcome copy, and subtitle match the reference. Existing operational messages remain available.
- P3: the existing welcome heading font is less rounded than the reference; the existing footer asset lacks the reference's faint lower-right decorative overlay. These do not affect layout or use.

The full comparison was sufficient for composition; desktop and mobile screenshots were also inspected separately at readable size for headings, role labels, borders, and text wrapping.

## Comparison history

1. Initial desktop capture identified oversized card height, a baseline-shifted logo, excess illustration/footer spacing, and an unavailable back-arrow name. Fixed card padding/gaps, logo alignment, story spacing, and used the existing Lucide package's ArrowLeft directly.
2. The revised same-size desktop comparison confirmed aligned columns, image scale, and card spacing, with only the P3 differences above.
3. Mobile inspection found a global heading-font fallback; explicitly bound the role heading to Manrope.
4. Tablet inspection found words joining across a hidden line break. Removed the hiding rule and inspected the saved post-fix tablet capture.

## Interaction and regression checks

- All three cards select their existing internal roles and expose existing sign-in and account-creation controls.
- Keyboard Enter activates the learner card.
- Teacher account creation still hands off as `Individual Teacher`; Institute still hands off as `Institute`.
- Sign-in retains `/login?redirect-to=/campus`; Google availability remains policy-controlled.
- Existing connection error and retry UI remains visible when the backend is unavailable.
- Browser console error check: none in the fixture-backed preview.
- Frontend tests: 116 passed, 0 failed.
- Production Vite build passed, using an ignored output directory; existing chunk-size and mixed-import warnings remain.
- `git diff --check` passed.
- API functions, payloads, backend files, models, and authenticated routing branches are unchanged.

Live Frappe authentication and account submission were not exercised: the preview uses temporary guest responses and no account was created.
