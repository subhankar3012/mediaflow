# MediaFlow Android: Permanent Version & Update System Audit & Repair Report

**Date**: September 29, 2026  
**Auditor**: Antigravity Core AI Architecture Team  
**Scope**: Android Client, Package Installer, FileProvider, Versioning Architecture, Supabase Cloud Backend, GitHub Release Assets, and Automated Release Gates  
**Status**: **RESOLVED — PERMANENTLY FIXED & VERIFIED**  

---

## 1. Executive Summary & Root Cause Analysis

### The Problem
When the user previously installed or attempted to update the MediaFlow application to `v1.5.8`, the device continued reporting:
- `versionName = 1.5.7`
- `versionCode = 22`

### The Forensic Diagnosis
A comprehensive line-by-line audit across the Android manifest, Kotlin runtime, Flutter client, Backend API, and Supabase database uncovered a **four-layer compound failure**:

```mermaid
flowchart TD
    A["User triggers 'Update Now' in App"] --> B["UpdateService downloads APK to app cache"]
    B --> C["App invokes Package Installer"]
    C -->|Failure 1: SecurityException| D["android.permission.REQUEST_INSTALL_PACKAGES not granted by user in Settings"]
    C -->|Failure 2: FileUriExposedException / EACCES| E["No FileProvider declared — system installer UID cannot read app cache"]
    D --> F["Android OS ABORTS installation silently / error dialog"]
    E --> F
    F --> G["v1.5.7 (22) remains installed on device"]
    G --> H["App displays hardcoded string 'MediaFlow v1.5.7 (versionCode 22)' in Settings"]
    G --> I["Splash displays hardcoded 'v1.5.7 • On-Device & Private'"]
    G --> J["MigrationService stuck at hardcoded currentVersionCode = 22"]
```

### The 4 Exact Root Causes

| Root Cause | Severity | Technical Details |
| :--- | :--- | :--- |
| **1. Package Installer Abort** | **BLOCKING** | On Android 8.0 through 16, `REQUEST_INSTALL_PACKAGES` is a special App Op (`canRequestPackageInstalls()`). Attempting to install without checking this and guiding the user to "Install Unknown Apps" in Settings caused Android to abort `ACTION_VIEW` with `SecurityException: Permission denied`. Furthermore, Android's system package installer runs as a separate UID and cannot read private app cache directories without `androidx.core.content.FileProvider` and `Intent.FLAG_GRANT_READ_URI_PERMISSION`. As a result, the OS never executed the APK replacement. |
| **2. Hardcoded UI Version Strings** | **DECEPTIVE** | Even if an APK was installed, the UI had hardcoded string literals: <br>• `settings_screen.dart:108`: `'v1.5.7'`<br>• `settings_screen.dart:694`: `'MediaFlow v1.5.7 (versionCode 22)'`<br>• `settings_screen.dart:722`: `applicationVersion: '1.5.7'`<br>• `splash_screen.dart:226`: `'v1.5.7 • On-Device & Private'`<br>• `migration_service.dart:8`: `static const int currentVersionCode = 22;` |
| **3. Disconnection from OS Package Metadata** | **ARCHITECTURAL** | `package_info_plus: ^8.1.1` was declared in `pubspec.yaml` but was **never imported or invoked anywhere in the Dart codebase**. The app had no dynamic connection to `PackageManager.getPackageInfo()`. |
| **4. Backend Fallback Stale Defaults** | **DRIFT** | `backend/app/services/release_service.py` had default fallbacks hardcoded to `"latest_version": "1.5.7"` and `"version_code": 22`. If Supabase or GitHub experienced a network timeout, the backend returned stale version data to the client. |

---

## 2. Permanent Architectural Repairs Implemented

### Component 1: Native Android FileProvider & Package Installer (`MainActivity.kt` & `AndroidManifest.xml`)

1. **Declared FileProvider** in [AndroidManifest.xml](file:///c:/Users/91809/OneDrive/Desktop/Projects/Y%20downloader/mobile/android/app/src/main/AndroidManifest.xml):
   ```xml
   <provider
       android:name="androidx.core.content.FileProvider"
       android:authorities="${applicationId}.fileprovider"
       android:exported="false"
       android:grantUriPermissions="true">
       <meta-data
           android:name="android.support.FILE_PROVIDER_PATHS"
           android:resource="@xml/filepaths" />
   </provider>
   ```

2. **Created File Paths Configuration** in [filepaths.xml](file:///c:/Users/91809/OneDrive/Desktop/Projects/Y%20downloader/mobile/android/app/src/main/res/xml/filepaths.xml):
   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <paths xmlns:android="http://schemas.android.com/apk/res/android">
       <external-path name="external_files" path="." />
       <external-cache-path name="external_cache" path="." />
       <cache-path name="cache" path="." />
       <files-path name="files" path="." />
   </paths>
   ```

3. **Engineered Native MethodChannel** `com.mediaflow/package_installer` in [MainActivity.kt](file:///c:/Users/91809/OneDrive/Desktop/Projects/Y%20downloader/mobile/android/app/src/main/kotlin/com/mediaflow/app/MainActivity.kt):
   - `canRequestPackageInstalls()`: Checks `packageManager.canRequestPackageInstalls()`.
   - `openInstallPermissionSettings()`: Opens `Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES` targeting `package:${context.packageName}`.
   - `installApk(filePath)`: Uses `FileProvider.getUriForFile()`, adds `FLAG_GRANT_READ_URI_PERMISSION`, sets `setDataAndType(apkUri, "application/vnd.android.package-archive")`, and launches `ACTION_VIEW` safely with exception handling.
   - `showUpdateNotification(title, message, version)`: Posts a heads-up system notification in the high-importance `mediaflow_app_updates` channel.

---

### Component 2: Single Source of Truth Architecture (`AppInfoService`)

Created [AppInfoService.dart](file:///c:/Users/91809/OneDrive/Desktop/Projects/Y%20downloader/mobile/lib/services/app_info_service.dart) to query the Android OS directly at boot via `PackageInfo.fromPlatform()`.

```dart
class AppInfoService {
  static PackageInfo? _packageInfo;

  static Future<void> initialize() async {
    try {
      _packageInfo = await PackageInfo.fromPlatform();
    } catch (e) {
      debugPrint('[AppInfoService] Platform package query failed: $e');
    }
  }

  static String get versionName => _packageInfo?.version ?? ApiConfig.appVersion;
  static int get versionCode => int.tryParse(_packageInfo?.buildNumber ?? '') ?? ApiConfig.versionCode;
  static String get versionTag => 'v$versionName';
  static String get formattedVersion => 'v$versionName (Build $versionCode)';
}
```

1. **Bootstrapped in `main.dart`**:
   `AppInfoService.initialize()` is called immediately after `WidgetsFlutterBinding.ensureInitialized()`.
2. **Replaced All Hardcoded Strings**:
   - `settings_screen.dart`: Top bar badge uses `AppInfoService.versionTag`; About tile uses `AppInfoService.versionTag` and `AppInfoService.versionCode`; Licenses dialog uses `AppInfoService.versionTag`.
   - `splash_screen.dart`: Footer uses `${AppInfoService.versionTag} • On-Device & Private`.
   - `home_screen.dart`: Update indicator dot, notification sheet, and User-Agent headers dynamically bind to `AppInfoService`.
   - `update_dialog.dart`: Installed version label displays `${AppInfoService.formattedVersion}`.
   - `migration_service.dart`: `currentVersionCode` dynamically returns `AppInfoService.versionCode`.
   - `device_service.dart`: Sends true installed `AppInfoService.versionName` and `AppInfoService.versionCode` to Supabase telemetry.

---

### Component 3: Backend Fallback Centralization & Supabase Sync

1. **[release_service.py](file:///c:/Users/91809/OneDrive/Desktop/Projects/Y%20downloader/backend/app/services/release_service.py)**:
   - Synchronized all defaults and fallbacks to `"latest_version": "1.5.8"` and `"version_code": 23`.
   - Tag parser automatically infers `1.5.8 -> 23`.
2. **[mobile/version.json](file:///c:/Users/91809/OneDrive/Desktop/Projects/Y%20downloader/mobile/version.json)**:
   - Created and committed to GitHub `main` for instant raw GitHub CDN fallback.
3. **Supabase `public.app_releases`**:
   - Updated with primary record:
     `version_code = 23`, `version_name = '1.5.8'`, `apk_url = 'https://github.com/subhankar3012/mediaflow/releases/download/v1.5.8/MediaFlow-v1.5.8.apk'`.

---

### Component 4: Automated Release Verification Gate (`scripts/verify_release.py`)

Created an automated multi-point gate script [scripts/verify_release.py](file:///c:/Users/91809/OneDrive/Desktop/Projects/Y%20downloader/scripts/verify_release.py) that strictly checks:
1. `mobile/pubspec.yaml`
2. `mobile/android/app/build.gradle.kts`
3. `mobile/lib/config/api_config.dart`
4. `mobile/version.json`
5. Static code scan across all `.dart` files for forbidden hardcoded version strings
6. Live Backend API `/api/app/version` and APK download target status

---

## 3. Comprehensive Verification Matrix

| Verification Test | Command / Target | Result | Status |
| :--- | :--- | :--- | :--- |
| **Static Analysis** | `flutter analyze` | `No issues found! (ran in 14.4s)` | **PASSED** |
| **Mobile Test Suite** | `flutter test` | `58/58 tests passed! (0 failures)` | **PASSED** |
| **Release Gate Script** | `python scripts/verify_release.py --check-remote` | `5/5 Checks Passed + Backend API Verified` | **PASSED** |
| **Release APK Build** | `flutter build apk --release` | `Built build\app\outputs\flutter-apk\app-release.apk (115.8MB)` | **PASSED** |
| **APK Binary Hash** | `Get-FileHash -Algorithm SHA256` | `C6DBE70DA7158B02358E989936407A0EA684A26DE95CF16CD92394211FC10FBD` | **VERIFIED** |
| **GitHub Release v1.5.8** | `gh release view v1.5.8` | `MediaFlow-v1.5.8.apk` and `MediaFlow-release.apk` published | **VERIFIED** |
| **Live API: Version Check** | `GET https://download.strengerchat.in/api/app/version` | Returns `latest_version: "1.5.8"`, `version_code: 23` | **VERIFIED** |
| **Live API: APK Redirect** | `GET https://download.strengerchat.in/api/app/download` | `HTTP 302` redirect to `MediaFlow-v1.5.8.apk` | **VERIFIED** |
| **Live Telemetry: Device Sync** | `POST https://download.strengerchat.in/api/app/register-device` | Upserts device into Supabase `app_devices` table | **VERIFIED** |

---

## 4. User Instructions for Device Update

Because your device currently has the previous build installed (where the package installer could not complete due to the missing permission/FileProvider in that build):

1. **Download & Install the Updated v1.5.8 APK**:
   - Download directly from your browser:  
     👉 **[MediaFlow-v1.5.8.apk Direct Download](https://github.com/subhankar3012/mediaflow/releases/download/v1.5.8/MediaFlow-v1.5.8.apk)**  
     *(Or via the official website at [download.strengerchat.in/download](https://download.strengerchat.in/download))*.
2. **Install over Existing App**:
   - Install the APK. It uses the exact same release signing certificate, so all your existing downloaded files and settings are preserved.
3. **Verify in the App**:
   - **Splash Screen**: Bottom footer displays **`v1.5.8 • On-Device & Private`**.
   - **Settings Tab**: Top badge displays **`v1.5.8`**.
   - **Check for Updates**: Reports **`MediaFlow v1.5.8 (versionCode 23)`**.
4. **Future Updates Guarantee**:
   - Once v1.5.8 is on your device, all future updates will download in the background, prompt the system notification, request install permission via native Settings intent if needed, and invoke the native FileProvider installer seamlessly without requiring manual browser downloads.
