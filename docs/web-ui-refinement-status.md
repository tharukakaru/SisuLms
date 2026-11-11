# Web UI refinement — work in progress

Source: Figma w0E7gacghSejjIjXJxwfnh, session a844b44f-24ef-4556-9fa8-6db44f131427.
Reference nodes: student 210:3091, sidebar 210:4071, header 210:3094, teacher 16:14, owner 24:14, sign-in 88:4031.

Scope: desktop web presentation only. Current role permissions, route handlers, payment holds, subscription visibility and programme completion rules remain authoritative over older Figma content. New pages or workflow changes require user confirmation. Mobile app is out of scope; existing compact web layout retained.

Local edits: desktop Manrope typography, spacing/cards/tables, owner navigation, original sign-in illustration. Existing logo hash matches Figma exactly. No backend source changed for this work. No production deployment, Git commit or push yet.

Assets: discover.png from Figma Story / Discover (87:3858 / 113:18); story-footer.svg from 116:4554. Original unmodified downloads. Existing sisu-original-light.png SHA256 702982bd76b1c42c687ad912101ec180f20f3b4df6659b9ebf3b44c0862f725f is identical to the Figma logo.

Validation: 116 frontend tests pass; production build passes; static validation passes (665 Python, 126 JSON). Mock owner navigation/billing/provisioning/access checks pass with global production styles; sign-in bundle role selection/login destinations/artwork/compact layout pass. Full role screenshot acceptance remains pending. Older student-flow-check.cjs is stale (expects a verification dialog on load) and did not pass; do not count it as acceptance.

User approved demo display names/photos and covers on named test classrooms only. Eight supplied images are copied unchanged into institute_lms/public/demo. No external web images were needed. Mapping: brown-shirt portrait → independent teacher Kasun; blue-blouse portrait → institute teacher Dilini; blue-suit portrait → institute admin Ravindu; black-suit/glasses portrait → student Navodya. Physics/Biology/Economics covers target three named test classrooms; Accounting is available but not assigned speculatively.

The separate update-demo-presentation.py previews by default; --apply changes only allowlisted presentation fields on exact demo accounts/classrooms after all guards pass, with a private before/after backup. Credentials, access, invoices and enrolments remain unchanged. NOT APPLIED to production.

Additional validation: production bundle browser smoke checks pass for Student, Teacher and Admin overview rendering, classroom/schedule navigation, student subscription-link absence, and desktop/compact overflow using mocked read APIs. This does not replace live account acceptance.

Figma further reads remain quota-limited. This is a conservative shared desktop visual refinement using retrieved references, not a claim of pixel-perfect implementation of every Figma frame. Existing workflows override older design concepts.

Release: ../release-candidate/sisu-web-refinement.tgz and scripts/deploy-web-refinement.py. Source hashes are guarded; previous sources and built assets are backed up, old hashed assets retained for open tabs. No production deployment, commit or push performed. Live acceptance and payment gateway testing remain pending.
