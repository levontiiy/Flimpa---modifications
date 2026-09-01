#!/usr/bin/env bash
# Build FLIMPA release artifacts (macOS .app + .dmg, or Windows folder for .exe packaging).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
VERSION="${1:-1.5.0}"
VENV_PY="${ROOT}/.venv/bin/python"

if [[ ! -x "$VENV_PY" ]]; then
  echo "Missing .venv — run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

echo "==> PyInstaller build"
"$VENV_PY" -m PyInstaller --clean --noconfirm FLIMPA.spec

RELEASE_DIR="${ROOT}/release"
mkdir -p "$RELEASE_DIR"

if [[ "$(uname -s)" == "Darwin" ]]; then
  APP="${ROOT}/dist/FLIMPA.app"
  DMG="${RELEASE_DIR}/FLIMPA.v${VERSION}.dmg"
  if [[ ! -d "$APP" ]]; then
    echo "Expected ${APP} — build failed?"
    exit 1
  fi
  echo "==> Creating DMG: ${DMG}"
  rm -f "$DMG"
  hdiutil create -volname "FLIMPA ${VERSION}" -srcfolder "$APP" -ov -format UDZO "$DMG"
  echo "Done: $DMG"
  ls -lh "$DMG"
else
  echo "==> Windows/Linux: built folder at dist/FLIMPA/"
  echo "Zip dist/FLIMPA as FLIMPA.v${VERSION}.zip or use Inno Setup for an installer."
fi
