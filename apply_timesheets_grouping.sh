#!/usr/bin/env bash
set -euo pipefail
echo "[gd] Timesheets grouping — applying"
cp -f timesheets_enhance.css ./timesheets_enhance.css
cp -f timesheets_enhance.js ./timesheets_enhance.js
if grep -q "timesheets_enhance.js" timesheets.html 2>/dev/null; then
  echo " - scripts already present"
else
  sed -i.bak 's#</head>#  <link rel="stylesheet" href="/timesheets_enhance.css" />\n</head>#' timesheets.html || true
  sed -i.bak 's#</body>#  <script src="/timesheets_enhance.js"></script>\n</body>#' timesheets.html || true
  echo " - tags injected"
fi
echo "[gd] Done"
