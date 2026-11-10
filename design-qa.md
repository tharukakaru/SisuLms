# Signup and role selection visual QA

final result: passed

## Direct institute role entry

- “We're an institute” now opens the existing styled Institute signup directly, using the same provider selection handler and signup kind. Back restores role selection. This removes the old intermediate institute login/actions view from this path without modifying signup models, validation, requests or backend code.
- Latest reference: `C:/Users/nim20/AppData/Local/Temp/codex-clipboard-8ce118a5-86cf-42fe-ab25-85733fedbba8.png` (792 x 606). Screenshot: `local-private/institute-direct-entry.png` at 1440 x 1100. Both were visually inspected together; the previously verified institute layout is reused, with the same required-field and font differences documented below.
- Browser checked direct entry for both current and legacy signup, correct Institute fields, and return to role selection. Console errors: none. All 116 tests pass; PortalRoot script/template compile and whitespace checks pass. No live registration performed.

## Institute-owner signup reference update

- Reference: `C:/Users/nim20/AppData/Local/Temp/codex-clipboard-20707688-ffb2-4ca1-adb6-44ced39ca73c.png` (742 x 567). Current signup capture: `local-private/institute-reference-desktop.png` (1440 x 1100 at a 1440 x 1100 CSS viewport, 1x density). Full-view comparison: `local-private/institute-reference-comparison.png`, with the capture proportionally normalized to the source dimensions. Readable full-size form and mobile captures were also inspected; a further focused crop was unnecessary.
- Initial inspection found that institute spacing pushed the submit action below the reference composition (P2). Institute details now use 44px fields, 16px row margins, tighter heading spacing and no button shadow. Existing explanations moved into the optional-details disclosure. A second inspection caught excess bottom spacing; reducing that spacing produced the final capture above with all required controls visible beside the artwork.
- Typography/colors: retained bundled Manrope, 36px heading, purple action, pale fields and lavender footer. The source's rounded display font differs slightly (P3, inherited brand font). Assets: retained the existing source illustration, logo and footer; no generated replacements or placeholders. Copy: reference labels and institute introduction preserved. Current flow truthfully keeps “Verify email & continue”; legacy retains “Verify email & submit”.
- Intentional contract-preserving differences: username remains required and visible; current signup still collects separate administrator first/last names and country/time zone values. These additional fields use compact spacing instead of removing required input. Optional fields and provider explanations remain accessible. Institute-teacher and individual-teacher styles are unaffected by these institute-only selectors; verification pages are excluded.
- Functional checks: current local-fixture institute submission reached email verification with the existing 19-field payload. Current and legacy optional disclosures were opened and inspected. Legacy screenshot: `local-private/institute-reference-legacy.png`. Mobile screenshot: `local-private/institute-reference-mobile.png`; both current and legacy have no horizontal overflow at 390 x 844. Browser error log was empty. No live accounts, emails or SMS were created.
- All script blocks match their pre-change backups exactly, preserving handlers, models and validation. All 116 frontend tests passed via the existing Node test runner; production Vite build passed with existing chunk-size warnings. The local npm launcher was unavailable, so the same test command was invoked directly with Node. No backend or API edits. Final result: passed, with no outstanding P0/P1/P2 findings.

## Institute teacher signup correction

- Corrects the prior misunderstanding: an institute teacher joins an existing institute; an institute owner creates a workspace. Added an explicit Institute teacher choice in both provider menus, using the existing `Individual Teacher` selection and teacher form. No new account kind or payload format.
- Restored the separate institute-owner templates and spacing from the pre-alignment backups. The teacher route retains compact fields, subject/expertise, qualifications and existing optional controls. Institute name, administrator position and recovery contacts remain on the owner form only.
- Browser checks passed for current and legacy teacher routes: both local-fixture submissions reached email verification with the existing `Individual Teacher` payload and no institute details entered. Owner fields remain separately visible. Account-joining components and backend files are untouched; no live accounts or messages were created.
- Desktop evidence: `local-private/institute-teacher-fixed.png`. Mobile evidence: `local-private/institute-teacher-fixed-mobile.png`; provider choices and teacher form have no horizontal overflow at 390px. Browser error log was empty.
- All 116 frontend tests and the production build passed (existing chunk-size warnings). Signup script blocks remain identical to the pre-correction copies; API handlers, models and validations are unchanged.

## Institute signup aligned with individual teacher signup (superseded)

- The correction above reverses this mistaken owner-form alignment; this section is retained as historical QA only.

- Supersedes the institute-specific layout recorded below, per the user's correction. Both provider types now render the same core field template in current and legacy signup: name, email, username, phone, subject/expertise, qualifications, and country/time zone. Removed institute-only 50px fields, 20px row margins and reduced top padding; both now use the existing teacher styling (40px inputs, 12px row margins).
- Preserved institute name, position and recovery contacts as required fields in “Institute details”. Subject remains required only for individual teachers; it is optional for institutes, preserving their existing requirements. Qualifications, website, bio/tagline, account-type and Google options remain available as applicable. No duplicate qualifications input remains.
- Desktop evidence: `local-private/institute-alignment-desktop.png`. Mobile evidence: `local-private/institute-alignment-mobile.png` at 390 × 844, without horizontal overflow. Browser measurements confirmed identical input height and row margins in current and legacy institute forms. Existing artwork, typography and colors are unchanged.
- Both registration script blocks, including every model, handler and API call, match pre-edit copies exactly. A local-fixture current institute submission reached email verification using the unchanged 19-field payload. Legacy institute extras and optional controls were inspected; teacher subject validation and absence of institute-only controls were also checked.
- Build passed with existing chunk warnings; all 116 frontend tests passed; browser error check was empty; whitespace check passed. No live account creation or backend changes.

## Waiting-for-review screen

- Source: `C:/Users/nim20/AppData/Local/Temp/codex-clipboard-4637a4ab-4bd7-4536-b241-1c11d00dd785.png` (802 × 608). Desktop capture: `local-private/review-screen-desktop.png` (1440 × 1100 CSS/pixel dimensions). Source and proportionally normalized capture were inspected together in `local-private/review-screen-comparison.png`; the full-size capture was inspected for readable text and control styling.
- The completed provider application now retains the verification story artwork, purple footer and centered right panel. Added the requested explanatory text, pale “Awaiting review” card and lavender “Back to sign in” action. Uses existing Manrope, purple tokens and artwork; prior P3 font/asset-resolution differences remain.
- Existing application reference and post-approval instructions remain available under “Application details”. This intentional extra control slightly shifts the vertically centered form relative to the reference. Both return controls use the existing back event.
- Initial visual inspection caught the shared primary-button hover overriding the secondary lavender background (P2). Added a matching pale hover treatment and inspected the corrected capture. No outstanding P0/P1/P2 findings.
- Mobile capture: `local-private/review-screen-mobile.png` at 390 × 844, with no horizontal overflow. Local-fixture verification reached the review screen; expanding details showed the original reference and instructions; the return action restored the existing provider selection screen. Browser console contained no errors.
- Registration script, functions and model declarations are byte-for-byte unchanged from the pre-edit copy. No API or backend changes. All 116 frontend tests passed, production build passed with existing chunk warnings, and whitespace check passed.

## Email and mobile verification redesign

- References: `C:/Users/nim20/AppData/Local/Temp/codex-clipboard-712fb59c-34c2-41d4-be8a-20acc56378eb.png` (email, 812 × 618) and `C:/Users/nim20/AppData/Local/Temp/codex-clipboard-7439ae35-00e0-4d68-9c1f-e1b01eec317e.png` (mobile number, 808 × 627).
- Desktop captures: `local-private/verification-email-legacy.png`, `verification-email-desktop.png`, and `verification-phone-standalone.png`. Final legacy email and standalone mobile captures are 1440 × 1100 CSS/pixel dimensions. Compared proportionally normalized screenshots beside each supplied reference in `verification-email-comparison.png` and `verification-phone-comparison.png`. Readable full-size captures were also inspected for labels, buttons, and validation controls.
- Typography: retained bundled Manrope, 36px headings, 12px labels, 14px body/input text. The supplied rounded headline font differs slightly from the existing family (P3). Layout: shared two-column story panel, vertically centered verification form, 50px fields, 54px pill buttons, mobile single column. Colors: purple primary action, pale lavender secondary action, dark-purple wave footer. Assets: exact illustration extracted from the supplied reference; it is softer at large desktop sizes because the source crop is 261 × 261 (P3). No generated replacement or placeholder art.
- Copy: requested headings and story copy are used. Legacy email retains its truthful code-expiry information and “Verify & send for review”. Current signup uses “Verify email & continue” since phone verification and password setup still follow. Current signup exposes resend/edit controls, and standalone mobile keeps channel selection in a disclosure. Disabled controls retain their disabled appearance.
- Iteration 1 found the legacy application's inherited `min-height:100vh` prevented vertical centering (P1). Removed that minimum only within the verification layout and removed the inherited button shadow. The revised email capture and comparison confirm corrected positioning. No remaining actionable P0/P1/P2 issues; retained operational controls cause small intentional vertical-position differences from the mobile reference.
- Responsive evidence: `verification-email-mobile.png` and `verification-phone-mobile.png` at 390 × 844. Labels and actions remain readable without horizontal overflow. Existing compact teacher form and generic settings verification remain outside these new verification styles.
- Local-fixture interactions passed: current signup email → mobile → password setup; invalid email-code feedback; resend rate-limit countdown while code verification remains available; phone-code submission; password action disabled until its existing requirements are met. Legacy email verification reaches the application review reference. Standalone mobile request → cooldown/expiry → verification reaches “Mobile verified”. All values and codes were fictitious; no real email/SMS/account creation or password entry occurred.
- Existing functions and form-model declarations in VerifiedSignup, RegistrationFlow and MobileVerification match pre-change copies. Captured verification calls retain their original token/channel/code, challenge/code and phone payload formats. API contracts, backend logic and models are unchanged. Google-authenticated account completion retains its existing embedded UI.
- Verification: 116 frontend tests passed, production build passed with existing chunk-size warnings, console checks showed no unexpected errors, and `git diff --check` passed.

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
