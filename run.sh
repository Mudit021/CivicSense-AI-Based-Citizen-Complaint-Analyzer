#!/usr/bin/env bash
# CivicSense — one-command setup and run.
#
#   ./run.sh          install deps, download NLTK data, start the app
#   ./run.sh test     install deps, download NLTK data, run the smoke suite
#
# Requires Python 3.10+ on PATH as "python" (or "py" on Windows).

set -euo pipefail
cd "$(dirname "$0")"

PY=python
command -v python >/dev/null 2>&1 || PY=py

echo "==> Installing dependencies"
"$PY" -m pip install --quiet --disable-pip-version-check -r requirements.txt

echo "==> Downloading NLTK data (first run only)"
"$PY" - <<'EOF'
import nltk
for pkg in ("stopwords", "wordnet", "vader_lexicon", "punkt"):
    try:
        nltk.download(pkg, quiet=True)
    except Exception as exc:
        print("  (nltk:", pkg, "->", exc, ")")
EOF

if [ "${1:-}" = "test" ]; then
  echo "==> Running end-to-end smoke suite"
  exec "$PY" smoke_test.py
fi

echo "==> Starting CivicSense on http://127.0.0.1:5000"
exec "$PY" app.py
