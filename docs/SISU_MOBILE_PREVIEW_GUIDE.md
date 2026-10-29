# SISU V2 mobile previews

Both are **PREVIEW ONLY**. All identities, prices, credits and academic records are fictional. No backend/provider acceptance is implied. Production `lib/main.dart` does not select either fixture service.

## Presentation preview — recommended for client walkthroughs

Exact release folder:
`C:\Users\THARUKA KARUNARATHNE\Documents\Codex\2026-10-01\dan-wada-karnna-gg-good-luck-3\outputs\SISU_MOBILE_FINAL_V2`

```powershell
cd "C:\Users\THARUKA KARUNARATHNE\Documents\Codex\2026-10-01\dan-wada-karnna-gg-good-luck-3\outputs\SISU_MOBILE_FINAL_V2"
.\Start-Mobile-Presentation-Preview.ps1 -Port 5197
```

Open http://127.0.0.1:5197/ . The launcher serves packaged `presentation-web`; Node.js is required, Flutter is only needed to rebuild. It uses a maximum 440px phone shell, bottom navigation and actual Flutter product components. Choose Student Starter/Premium, Teacher Starter/Premium, Institute Admin Starter/Premium. No developer selectors appear inside the walkthrough. Platform Owner stays web-first.

Additional coherent scenarios use the URL:
- `?preset=student-expired`: Starter fallback, AI hidden.
- `?preset=student-shared`: Premium and shared pool.
- `?preset=student-exhausted`: Premium visible, individual allowance exhausted.
- `?preset=admin-shared`: shared allocation controls.
- `?preset=admin-pending`: Starter during payment processing.
- `?preset=admin-renewal-failed`: failed renewal while paid Premium remains valid.

Home, Classes, Explore and Account preserve role-specific navigation. Account → Leave walkthrough returns to preset choices. Lessons show free, locked and purchased/archived examples. Teacher tools include library, live sessions and paper review; Admin has billing and allocation controls. Requests for real checkout/upload/playback/RTC are blocked with PREVIEW ONLY messages. AI examples are illustrative; unsupported fixture actions return an honest unavailable state.

Screenshots: docs/preview-screenshots-v2. For screenshots use a 390×844 browser viewport or the desktop phone shell. The 320px / 1.5 text-scale widget test is included.

## Developer preview — state harness retained

Same folder:
```powershell
.\Start-Mobile-Preview.ps1 -Port 5198
```
Open http://127.0.0.1:5198/ . Entry `lib/main_preview.dart`, assets `preview-web`. Role/plan/credit/provider selectors are intentional developer controls. Some combinations are stress-test states, not presentation/product authorization.

## Rebuild or Android device preview

```powershell
flutter pub get
flutter build web --target lib/main_presentation.dart --no-web-resources-cdn --output presentation-web
flutter build web --target lib/main_preview.dart --no-web-resources-cdn --output preview-web
flutter devices
flutter run -d <android-device-id> -t lib/main_presentation.dart
# Developer harness:
flutter run -d <android-device-id> -t lib/main_preview.dart
```
These are dedicated entry points, not production flavors. Android execution was not verified here: SDK unavailable. Never publish either entry point as the production app. The production build uses `lib/main.dart` and real tenant configuration. No production keys are needed for previews.
