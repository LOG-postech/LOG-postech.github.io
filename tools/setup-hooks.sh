#!/usr/bin/env bash
#
# Point git at the version-controlled hooks in .githooks/.
# Run this once after cloning:  tools/setup-hooks.sh

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

git config core.hooksPath .githooks
chmod +x .githooks/* tools/*.sh

echo "Hooks enabled (core.hooksPath = .githooks)."
echo

if command -v convert >/dev/null 2>&1; then
    echo "ImageMagick: $(convert --version | head -1 | cut -d' ' -f1-3)"
else
    cat <<'EOF'
ImageMagick is NOT installed. The pre-commit hook needs it to optimize images.

  Ubuntu/Debian : sudo apt install imagemagick
  macOS         : brew install imagemagick
EOF
fi
