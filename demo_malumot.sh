#!/bin/sh
# APK tahlil uchun demo hisob va malumot yaratadi (Linux / WSL terminali uchun).
# Ishlatish:  sh demo_malumot.sh          -> yaratadi
#             sh demo_malumot.sh --clear  -> ochiradi
cd "$(dirname "$0")" || exit 1

# Serverni qaysi python bilan ishga tushirsangiz - shuni topamiz
if   [ -x "./venv/bin/python" ];  then PY="./venv/bin/python"
elif [ -x "./.venv/bin/python" ]; then PY="./.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then PY="python3"
else PY="python"; fi

echo "Python: $PY"
"$PY" --version || exit 1
"$PY" -c "import django; print('Django', django.get_version())" || {
  echo "XATO: bu pythonda Django yoq. Serverni qaysi buyruq bilan ishga tushirsangiz,"
  echo "      shu buyruqdagi python bilan ishlating:  <python> manage.py demo_data"
  exit 1
}

echo "--- migrate ---"
"$PY" manage.py migrate || exit 1
echo "--- demo_data ---"
"$PY" manage.py demo_data "$@"
