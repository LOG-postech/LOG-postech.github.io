#!/usr/bin/env bash
#
# Optimize site images to the size they are actually displayed at.
#
#   tools/optimize-images.sh              # optimize everything that needs it
#   tools/optimize-images.sh --check      # report only, change nothing
#   tools/optimize-images.sh path/to.jpg  # optimize specific files
#
# Photos land in the repo straight from a camera at 5000px / 10MB, but the site
# never displays them larger than ~800px. This resizes each image to a sensible
# multiple of its display size, re-encodes it, and strips EXIF (which also drops
# GPS coordinates from lab photos).
#
# Gallery thumbnails are not stored at all: tools/build.py makes them from the
# photos at build time (settings in data/gallery/config.toml).
#
# Every processed file is stamped with a marker in its image comment, so running
# this repeatedly is safe: already-optimized files are skipped rather than
# re-compressed. Bump MARKER if you change the rules and want a full re-pass.

set -euo pipefail

MARKER="log-opt-v1"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

CHECK_ONLY=0
declare -a TARGETS=()

for arg in "$@"; do
    case "$arg" in
        --check) CHECK_ONLY=1 ;;
        --help|-h) sed -n '2,20p' "$0" | sed 's/^# \?//'; exit 0 ;;
        -*) echo "unknown option: $arg" >&2; exit 2 ;;
        *) TARGETS+=("$arg") ;;
    esac
done

if ! command -v convert >/dev/null || ! command -v identify >/dev/null; then
    cat >&2 <<'EOF'
ImageMagick is required but was not found.

  Ubuntu/Debian : sudo apt install imagemagick
  macOS         : brew install imagemagick

EOF
    exit 1
fi

# ---------------------------------------------------------------------------
# Per-directory rules: max long edge, JPEG quality, output format, square crop.
#
# Sizes are ~3x the CSS display size so the images stay sharp on retina screens
# and when the layout grows:
#   data/gallery/photos/   click-through "full size" view      -> 2560px
#   static/lab_photo/      home page hero, <=800px wide        -> 1600px
#   data/members/photos/   member avatars, 140px square        ->  512px
#   data/research/icons/   research cards, ~124px square       ->  500px
#   static/logo/           left alone; small already, and logos need to stay crisp
# ---------------------------------------------------------------------------
IMAGE_DIRS="data/gallery/photos static/lab_photo data/members/photos data/research/icons"

rule_for() {
    case "$1" in
        data/gallery/photos/*)  echo "2560 82 jpg fit" ;;
        static/lab_photo/*)     echo "1600 85 jpg fit" ;;
        data/members/photos/*)  echo "512 85 jpg fit" ;;
        data/research/icons/*)  echo "500 85 keep fit" ;;
        *)                      echo "" ;;
    esac
}

# The file that refers to images in a directory, by file name.
references_for() {
    case "$1" in
        data/gallery/photos/*)  echo "data/gallery/gallery.yaml" ;;
        data/members/photos/*)  echo "data/members/members.yaml" ;;
        data/research/icons/*)  echo "data/research/topics.yaml" ;;
        static/lab_photo/*)     echo "pages/index.html" ;;
    esac
}

is_raster() {
    case "$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')" in
        *.jpg|*.jpeg|*.png) return 0 ;;
        *) return 1 ;;
    esac
}

human() { awk -v b="$1" 'BEGIN { printf "%.0fKB", b/1024 }'; }

# stat(1) takes different flags on Linux and macOS.
filesize() { stat -c%s "$1" 2>/dev/null || stat -f%z "$1"; }

declare -a RENAMES=()
saved_total=0
processed=0
skipped=0

optimize_one() {
    local src="$1"
    is_raster "$src" || return 0
    [ -f "$src" ] || return 0

    local rule; rule="$(rule_for "$src")"
    [ -n "$rule" ] || return 0
    read -r max quality outfmt mode <<<"$rule"

    # Already stamped by a previous run -> nothing to do.
    if [ "$(identify -format '%c' "$src" 2>/dev/null || true)" = "$MARKER" ]; then
        skipped=$((skipped + 1))
        return 0
    fi

    # Destination extension: normalize to lowercase .jpg unless the rule says keep.
    local dst="$src"
    if [ "$outfmt" = "jpg" ]; then
        dst="${src%.*}.jpg"
    fi

    local before; before=$(filesize "$src")

    if [ "$CHECK_ONLY" = 1 ]; then
        local dim; dim="$(identify -format '%wx%h' "$src" 2>/dev/null || echo '?')"
        printf "  would optimize  %-46s %8s  %s -> max %spx\n" \
            "$src" "$(human "$before")" "$dim" "$max"
        processed=$((processed + 1))
        return 0
    fi

    local tmpdir; tmpdir="$(mktemp -d)"
    local tmp="$tmpdir/out.${dst##*.}"

    # -auto-orient must run before -strip, otherwise the EXIF rotation flag is
    # discarded and sideways phone photos stay sideways.
    local -a geometry
    if [ "$mode" = "square" ]; then
        geometry=(-resize "${max}x${max}^" -gravity center -extent "${max}x${max}")
    else
        geometry=(-resize "${max}x${max}>")
    fi

    local -a encode=()
    if [ "${dst##*.}" = "jpg" ]; then
        encode=(-interlace Plane -sampling-factor 4:2:0 -quality "$quality")
    else
        encode=(-quality 95 -define png:compression-level=9)
    fi

    convert "$src" -auto-orient "${geometry[@]}" -strip "${encode[@]}" \
        -set comment "$MARKER" "$tmp"

    local after; after=$(filesize "$tmp")

    # Only accept the result if it is actually smaller. If it is not, keep the
    # original as-is (including its format) and stamp it, so we do not
    # reconsider it on every future run.
    if [ "$after" -ge "$before" ]; then
        convert "$src" -set comment "$MARKER" "$src"
        rm -rf "$tmpdir"
        skipped=$((skipped + 1))
        return 0
    fi

    mv "$tmp" "$dst"
    rm -rf "$tmpdir"
    chmod 644 "$dst"
    if [ "$dst" != "$src" ]; then
        rm -f "$src"
        RENAMES+=("$src=>$dst")
    fi

    saved_total=$((saved_total + before - after))
    processed=$((processed + 1))
    printf "  %-46s %8s -> %8s\n" "$dst" "$(human "$before")" "$(human "$after")"
}

# When a file changes extension (photo.png -> photo.jpg), update the data file
# that names it, so the build still finds it.
rewrite_references() {
    [ "${#RENAMES[@]}" -gt 0 ] 2>/dev/null || return 0
    local pair old new ref
    for pair in "${RENAMES[@]}"; do
        old="${pair%%=>*}"
        new="${pair#*=>}"
        ref="$(references_for "$old")"
        [ -n "$ref" ] && [ -f "$ref" ] || continue
        python3 - "$ref" "$old" "$new" <<'PY'
import os, re, sys
ref, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
text = open(ref, encoding="utf-8").read()
if ref.endswith(".html"):
    # Templates refer to static files by their published path (lab_photo/x.jpg).
    pairs = [(old.split("/", 1)[1], new.split("/", 1)[1])]
else:
    pairs = [(os.path.basename(old), os.path.basename(new))]
for a, b in pairs:
    # Whole values only, so a.png cannot match inside another name.
    text = re.sub(r"(?<![\w./-])%s(?![\w.-])" % re.escape(a), b, text)
open(ref, "w", encoding="utf-8").write(text)
PY
        echo "  updated reference in $ref: $(basename "$old") -> $(basename "$new")"
    done
}

echo "Optimizing images..."

if [ "${#TARGETS[@]}" -gt 0 ]; then
    for t in "${TARGETS[@]}"; do
        optimize_one "$t"
    done
else
    # shellcheck disable=SC2086  # IMAGE_DIRS is a word list on purpose
    while IFS= read -r f; do
        optimize_one "$f"
    done < <(find $IMAGE_DIRS -type f 2>/dev/null | LC_ALL=C sort)
fi

rewrite_references

echo
if [ "$CHECK_ONLY" = 1 ]; then
    echo "$processed file(s) would be optimized, $skipped already optimized."
    echo "Run without --check to apply."
else
    echo "$processed file(s) optimized, $skipped skipped, $(human "$saved_total") saved."
fi
