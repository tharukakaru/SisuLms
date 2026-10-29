# Safe interactive SISU web preview

## Launch on Windows

Extract `SISU_FINAL_RELEASE_WITH_PREVIEW.zip` into a new folder. Keep its `institute_lms` directory and included `preview-dist` assets together. Open PowerShell in that `institute_lms` directory and run:

```powershell
.\Start-Preview.ps1
```

Requires Node.js 22 or newer; tested here with Node 24.14.1. The packaged static preview requires no Frappe, database, merchant account, OpenAI key or dependency installation. The launcher opens the browser at `http://127.0.0.1:5178/preview.html?preview=1`. Press Ctrl+C in the terminal to stop it. If the port is occupied:

```powershell
.\Start-Preview.ps1 -Port 5186
```

If local PowerShell policy prevents a script from running, follow your organization's approved script policy. The equivalent tested Node server entry can be run without changing execution policy:

```powershell
cd frontend
node scripts/serve-preview.mjs 5178
```

Open the URL printed by that command. The launcher itself was tested with `-NoBrowser -Port 5186`; browser navigation and interactions were separately tested in installed Chrome through Playwright. The automatic default-browser launch branch was not separately exercised.

## Choose a role and a screen

The landing page explicitly says it is fictional. Click Student, Teacher, Institute Admin or Super Admin. No password or genuine login is required. Existing legacy email/password-looking inputs are visual preview controls only; do not enter real credentials. After entry, use **View as** and **Open screen** in the purple preview toolbar.

| Role | Useful walkthrough |
|---|---|
| Student | Dashboard → Classrooms → Schedule → Class fees → Notifications → Plan & usage → Premium AI → SMS/WhatsApp verification |
| Teacher | Dashboard/classes → Papers → open the fictional paper → Request AI feedback draft → Premium AI / Knowledge / Study tools → Wallet |
| Institute Admin | Teaching team/classes/programmes → Plan & usage → Premium AI / Insights → Notifications |
| Platform Owner / Super Admin | Platform control plane → Organizations / Plans / Provisioning / Billing / Readiness; separate legacy provider-review console remains available |

The displayed role selects fixtures, never a server identity. Local admin and platform owner remain visibly distinct. Tenant usage displays fictional local data; control-plane screens explicitly avoid fake cross-site academic analytics.

## Scenarios

Open **Preview scenarios — change UI state without calling a server**. Changing a scenario remounts the relevant screen; reselect a classroom afterward if necessary.

| Selector | Available states and purpose |
|---|---|
| Plan | STARTER, PREMIUM AI, CUSTOM; inspect resolved-feature display/locked AI |
| Subscription | trial, active, grace, past_due, suspended, cancelled, expired |
| AI | available, locked, quota exhausted, indexing required, supported result, provider unavailable |
| Payment | pending, paid, failed, cancelled; display only, no settlement |
| Notifications | unread, read, empty, provider disabled |
| OTP | ready, cooldown, expired, provider unavailable |

Subscription scenarios display states in the actual component; they do not emulate all production request guards or automatic PortalRoot recovery routing. CUSTOM uses illustrative configured values, not a commercial offer. The original academy fixtures are retained; source dates and new examples are fixed to 2 October 2026 for repeatability. User edits and transient timers are naturally interactive.

### AI and sources

Choose Premium AI, select an authorized fictional classroom, enter a question and tick the data-processing checkbox. Create a conversation if you want to inspect history. The answer begins **“Preview example — no OpenAI request was made.”** Sources display separately; opening a protected source is deliberately blocked because no backend/file service exists.

Study tools render summary, notes, flashcards and practice questions. Teacher tasks render drafts. Knowledge displays Ready/Queued and an unsupported legacy PPT example. Admin Insights shows clearly fictional aggregate statistics. The Papers preview contains a fictional submitted answer; Request AI feedback draft demonstrates the human-review boundary without changing a grade. Official provider-backed `papers.generate` is deliberately unavailable in the legacy preview adapter; use the AI workspace Quiz draft to inspect draft UI.

Conversation archive/delete scheduling is simulated in memory. New feature state resets on reload; the older academy editor stores some fictional data in this tab's sessionStorage. **Reset scenarios** resets scenario values/AI conversations/preferences, not every legacy academy edit. A fresh private browser window starts a clean preview.

### Notifications, OTP, payments and provisioning

Mark read changes the local inbox count. Preferences can be inspected; disabled SMS/push channels stay unavailable. OTP uses the explicitly labelled preview code `123456` only in this isolated artifact; no SMS/WhatsApp message is sent. Try both channels, expiry and unavailable states. The production OTP implementation remains secure and unchanged.

Payment status examples never call checkout or activate access. No commercial quote is fabricated: Get server quote reports preview checkout disabled. Older class fee amounts are fictional existing fixtures. Platform buttons may mutate illustrative local metadata; they do not reproduce all production validation, create infrastructure, send invitations or issue real signed policy. Plan configuration/override save acknowledgments are UI simulations, not persistent commercial administration.

Some account settings, provider connections, upload/download, real checkout and old actions without fixtures show **connected backend required**. This is intentional. It is not an unexpected provider success or a live system failure. The main role navigation remains available.

## Isolation from production

1. Existing preview support was reused: `preview/mode.js` and the existing client preview adapter were already DEV + loopback + query gated.
2. The added `preview.html` / `preview/main.js` entry mounts PreviewShell directly. It does not mount the real authentication bootstrap.
3. `vite.preview.config.js` is separate from normal `vite.config.js` and writes only `preview-dist`. Only the explicit preview build defines DEV for the isolated bundle; `npm run build` keeps the original production configuration.
4. `serve-preview.mjs` binds only `127.0.0.1`, serves read-only assets and rejects API/login/private-file paths. It has no backend proxy or database connection.
5. Preview-only runtime guards block external/API fetch, XHR, beacon, popups and ordinary form navigation. CSP blocks external scripts/fonts/images/frames and form destinations. External Google Fonts imports are removed only during preview build; installed/system font fallback preserves layout without network calls.
6. The normal production bundle was rebuilt and scanned: distinctive new fictional fixtures, preview activation and scenario markers were absent. All normal production assets matched the original release archive byte-for-byte in this environment.

The packaged preview is local-only and must never be deployed as the production portal. It is a visual interaction aid, not a permission/security simulator. Preview selector values are not sent to Frappe and cannot authorize an operation. Real backend authorization was not changed.

## Rebuild and developer commands

```powershell
# From release root: installs locked frontend packages only if missing, then builds preview
.\Start-Preview.ps1 -Rebuild -NoBrowser -Port 5186

# Or from frontend:
npm ci
npm test
npm run build:preview
npm run serve:preview
```

Explicit dev mode is also configured as `npm run dev:preview`; the static build/launcher is the tested delivery path. The dev-server branch was not separately acceptance-tested. Do not host any preview server publicly.

The normal production build succeeded here using Vite's native config loader because the environment blocked esbuild's bundled config loader:

```powershell
# From frontend; fail before copy if build fails
node node_modules/vite/bin/vite.js build --configLoader native
if ($LASTEXITCODE -ne 0) { throw 'Production build failed' }
node scripts/copy-entry.mjs
```

This uses the unchanged normal production Vite config. The default `npm run build` script is preserved. Tested commands/results are in [FINAL_SYSTEM_STATUS.md](FINAL_SYSTEM_STATUS.md).

## Screenshots and evidence

Actual Chrome screenshots are in `preview-screenshots/`: role dashboards/AI/subscription/notifications, platform tabs, teacher feedback/knowledge, student conversation/locked AI, OTP unavailable and mobile AI. These are screenshots of fictional preview data, not production screenshots. `PREVIEW_BROWSER_RESULTS.json` and `PREVIEW_SCENARIO_RESULTS.json` preserve browser observations, including intentionally unavailable legacy settings actions.
