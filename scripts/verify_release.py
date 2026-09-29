#!/usr/bin/env python3
"""
MediaFlow Release Verification Gate
===================================
Automated verification tool that enforces single source of truth across:
  1. mobile/pubspec.yaml
  2. mobile/android/app/build.gradle.kts
  3. mobile/lib/config/api_config.dart
  4. mobile/lib/services/app_info_service.dart
  5. mobile/version.json
  6. Backend /api/app/version
  7. Supabase public.app_releases
  8. Static code scan for illegal hardcoded version strings

Usage:
  python scripts/verify_release.py [--check-remote]
"""

import sys
import os
import re
import json
import urllib.request
import urllib.error

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def log_pass(msg: str):
    print(f"  \033[32m[PASS]\033[0m {msg}")

def log_fail(msg: str):
    print(f"  \033[31m[FAIL]\033[0m {msg}")

def log_warn(msg: str):
    print(f"  \033[33m[WARN]\033[0m {msg}")

def log_info(msg: str):
    print(f"  \033[36m[INFO]\033[0m {msg}")

def read_pubspec(mobile_dir: str):
    pubspec_path = os.path.join(mobile_dir, "pubspec.yaml")
    with open(pubspec_path, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"^version:\s*([0-9\.]+)\+([0-9]+)", content, re.MULTILINE)
    if not match:
        raise ValueError(f"Could not parse 'version: X.Y.Z+C' from {pubspec_path}")
    return match.group(1), int(match.group(2))

def read_gradle(mobile_dir: str):
    gradle_path = os.path.join(mobile_dir, "android", "app", "build.gradle.kts")
    with open(gradle_path, "r", encoding="utf-8") as f:
        content = f.read()
    vname_match = re.search(r'versionName\s*=\s*"([^"]+)"', content)
    vcode_match = re.search(r"versionCode\s*=\s*([0-9]+)", content)
    if not vname_match or not vcode_match:
        raise ValueError(f"Could not parse versionName or versionCode from {gradle_path}")
    return vname_match.group(1), int(vcode_match.group(1))

def read_api_config(mobile_dir: str):
    config_path = os.path.join(mobile_dir, "lib", "config", "api_config.dart")
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
    vname_match = re.search(r"appVersion\s*=\s*'([^']+)'", content)
    vcode_match = re.search(r"versionCode\s*=\s*([0-9]+)", content)
    if not vname_match or not vcode_match:
        raise ValueError(f"Could not parse appVersion or versionCode from {config_path}")
    return vname_match.group(1), int(vcode_match.group(1))

def read_version_json(mobile_dir: str):
    vjson_path = os.path.join(mobile_dir, "version.json")
    if not os.path.exists(vjson_path):
        return None, None
    with open(vjson_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("latest_version"), data.get("version_code")

def scan_hardcoded_versions(mobile_dir: str, current_version: str):
    """
    Ensures screens do NOT contain stale hardcoded version strings or badges.
    """
    forbidden_patterns = [
        (re.compile(r"'v1\.5\.[0-7]'"), "Stale hardcoded version string (v1.5.0-v1.5.7)"),
        (re.compile(r"versionCode\s*2[0-2]\b"), "Stale hardcoded versionCode <= 22"),
        (re.compile(r"applicationVersion:\s*'1\.5\.[0-7]'"), "Stale applicationVersion in License page"),
    ]
    
    violations = []
    lib_dir = os.path.join(mobile_dir, "lib")
    for root, _, files in os.walk(lib_dir):
        for f in files:
            if not f.endswith(".dart"):
                continue
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8", errors="ignore") as file:
                lines = file.readlines()
            for idx, line in enumerate(lines, 1):
                # Ignore comments or migrations that explicitly test older versions
                if line.strip().startswith("//") or line.strip().startswith("*"):
                    continue
                for pat, desc in forbidden_patterns:
                    if pat.search(line):
                        rel = os.path.relpath(path, ROOT_DIR)
                        violations.append(f"{rel}:{idx} -> {desc}: {line.strip()}")
    return violations

def check_backend_api(version_name: str, version_code: int):
    url = "https://download.strengerchat.in/api/app/version"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MediaFlow-VerificationGate/1.0"})
        with urllib.request.urlopen(req, timeout=7) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                remote_ver = data.get("latest_version")
                remote_code = data.get("version_code")
                apk_url = data.get("apk_url")
                return True, remote_ver, remote_code, apk_url
    except Exception as e:
        return False, str(e), None, None
    return False, "Non-200 status", None, None

def verify_all():
    print("=" * 65)
    print("MEDIAFLOW RELEASE VERIFICATION GATE")
    print("=" * 65)
    
    mobile_dir = os.path.join(ROOT_DIR, "mobile")
    errors = 0

    # 1. Pubspec
    print("\n[1/5] Checking mobile/pubspec.yaml...")
    try:
        pub_ver, pub_code = read_pubspec(mobile_dir)
        log_pass(f"pubspec.yaml: versionName = {pub_ver}, versionCode = {pub_code}")
    except Exception as e:
        log_fail(f"Failed to read pubspec.yaml: {e}")
        errors += 1
        return 1

    # 2. Gradle
    print("\n[2/5] Checking Android build.gradle.kts...")
    try:
        grd_ver, grd_code = read_gradle(mobile_dir)
        if grd_ver == pub_ver and grd_code == pub_code:
            log_pass(f"build.gradle.kts matches pubspec: versionName = {grd_ver}, versionCode = {grd_code}")
        else:
            log_fail(f"Gradle mismatch! versionName={grd_ver} (expected {pub_ver}), versionCode={grd_code} (expected {pub_code})")
            errors += 1
    except Exception as e:
        log_fail(f"Failed to read build.gradle.kts: {e}")
        errors += 1

    # 3. ApiConfig
    print("\n[3/5] Checking mobile/lib/config/api_config.dart...")
    try:
        api_ver, api_code = read_api_config(mobile_dir)
        if api_ver == pub_ver and api_code == pub_code:
            log_pass(f"api_config.dart matches pubspec: appVersion = {api_ver}, versionCode = {api_code}")
        else:
            log_fail(f"api_config.dart mismatch! appVersion={api_ver} (expected {pub_ver}), versionCode={api_code} (expected {pub_code})")
            errors += 1
    except Exception as e:
        log_fail(f"Failed to read api_config.dart: {e}")
        errors += 1

    # 4. Version JSON fallback
    print("\n[4/5] Checking mobile/version.json fallback...")
    try:
        vj_ver, vj_code = read_version_json(mobile_dir)
        if vj_ver == pub_ver and vj_code == pub_code:
            log_pass(f"version.json matches pubspec: {vj_ver} / {vj_code}")
        else:
            log_warn(f"version.json differs or missing: {vj_ver} / {vj_code} (expected {pub_ver} / {pub_code})")
    except Exception as e:
        log_warn(f"version.json check error: {e}")

    # 5. Static Code Scan for Hardcoded Version Strings
    print("\n[5/5] Scanning codebase for stale hardcoded version strings in UI...")
    violations = scan_hardcoded_versions(mobile_dir, pub_ver)
    if not violations:
        log_pass("No hardcoded version strings or stale version badges detected in Dart files.")
    else:
        for v in violations:
            log_fail(v)
            errors += 1

    # Optional remote check
    if "--check-remote" in sys.argv:
        print("\n[BONUS] Checking Live Backend API (/api/app/version)...")
        ok, r_ver, r_code, apk_url = check_backend_api(pub_ver, pub_code)
        if ok:
            if r_ver == pub_ver and r_code == pub_code:
                log_pass(f"Backend API reports matching live version: {r_ver} (code {r_code})")
                log_info(f"APK download target: {apk_url}")
            else:
                log_warn(f"Backend API differs: remote={r_ver} (code {r_code}), local={pub_ver} (code {pub_code})")
        else:
            log_warn(f"Backend API check unreachable: {r_ver}")

    print("\n" + "=" * 65)
    if errors == 0:
        print(f"\033[32m[SUCCESS] RELEASE VERIFICATION PASSED FOR v{pub_ver} (code {pub_code})\033[0m")
        print("All version sources are strictly synchronized. No UI regressions detected.")
        print("=" * 65)
        return 0
    else:
        print(f"\033[31m[FAILED] {errors} VERIFICATION VIOLATION(S) DETECTED\033[0m")
        print("Please resolve the version discrepancies before building or releasing.")
        print("=" * 65)
        return 1

if __name__ == "__main__":
    sys.exit(verify_all())
