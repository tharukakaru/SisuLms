# SISU V2 Flutter build guide

Verified SDK: Flutter 3.47.0 / Dart 3.13.0; retain pubspec.lock. New direct packages: livekit_client 2.13.0, file_selector 1.1.0, flutter_background 1.3.1, flutter_webrtc 1.6.2+hotfix.3, app_links 7.2.1. Existing state/navigation, AppAuth, video/audio/music and HTTP services remain.

```powershell
flutter pub get
flutter analyze --no-pub
flutter test --no-pub
flutter build web --no-pub --target lib/main.dart --no-web-resources-cdn --output build/production-web
flutter build web --no-pub --target lib/main_preview.dart --no-web-resources-cdn --output preview-web
flutter build web --no-pub --target lib/main_presentation.dart --no-web-resources-cdn --output presentation-web
flutter build apk --debug --no-pub --target lib/main_presentation.dart
```

The verification machine resolved packages from cache with `flutter pub get --offline`. The Android attempt returned **No Android SDK found**: **ANDROID ARTIFACT NOT PRODUCED — TOOLCHAIN UNAVAILABLE**. No APK or AAB is supplied. Install supported Android SDK/licenses and JDK17; current minSdk24, targetSdk36, Flutter compileSdk. Validate new camera/audio/mediaProjection foreground-service permissions on real target Android versions.

Production build, after acceptance:
```powershell
flutter build appbundle --release --target lib/main.dart --dart-define=SISU_SERVER=https://tenant.example --dart-define=SISU_AUTH_PROTOCOL=sisu
```

Existing signing environment variables remain owner-controlled; no signing credentials changed. `sisu.payments://return` is a refresh signal only, never payment proof. Test cold/warm/resume behavior and spoofed returns. Existing AppAuth redirect `lk.sisulearning.app:/oauthredirect` remains separate. iOS runner is absent from the supplied project: add a platform runner, callback configuration, permissions and any ReplayKit extension on macOS; do not infer iOS readiness from web compilation.

Presentation preview files are static compiled UI, not production APKs. They must never be used as a production deployment.
