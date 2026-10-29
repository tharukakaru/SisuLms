# SISU V2 web preview

**PREVIEW ONLY — deterministic fictional data, no real provider calls.** Production build and permission code are separate from the preview entry graph. This is UI evidence only.

Exact folder: `C:\Users\THARUKA KARUNARATHNE\Documents\Codex\2026-10-01\dan-wada-karnna-gg-good-luck-3\outputs\SISU_FINAL_RELEASE_V2`
```powershell
cd "C:\Users\THARUKA KARUNARATHNE\Documents\Codex\2026-10-01\dan-wada-karnna-gg-good-luck-3\outputs\SISU_FINAL_RELEASE_V2"
.\Start-Preview.ps1 -Port 5196
```
URL: http://127.0.0.1:5196/preview.html?preview=1

Packaged `preview-dist` runs with Node.js and no backend. Rebuild with `npm ci` then `npm run build:preview` inside frontend, or launcher `-Rebuild`. Production uses `npm run build`, never preview-dist.

Use the preview toolbar for Student, Teacher, Institute Admin and Platform Owner. Inspect Starter, Premium active/expired, payment pending and renewal-failed-with-valid-paid-period states; Individual/Shared AI credits and exhaustion; free/locked/purchased lessons; draft/published/archive library; live/recording status; paper queue/draft review; subscription offer/history/receipt. All demonstration prices are fictional, not commercial quotes. The primary default is #6C6AEE; semantic status and organization brand colors remain independent.

Teacher media/provider buttons do not initiate real uploads, OpenAI, RTC or payments. Refund preview returns Review rather than provider success. Owner commerce shows minimized fictional metadata only. Local role switching grants no production authority.

Verified with headless Chrome/Playwright: four roles and 19 pages; 390px viewport; no JavaScript errors or external requests in the recorded walk. See browser evidence and screenshot folders. It does not prove all real-provider workflows or complete accessibility.
