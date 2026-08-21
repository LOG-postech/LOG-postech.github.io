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
# Gallery thumbnails under stories/thumbs/ are generated automatically from the
# originals in stories/ — never create them by hand.
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
#   stories/          click-through "full size" view          -> 2560px
#   stories/thumbs/   gallery grid tiles, 112-180px square    ->  600px square
#   lab_photo/        home page hero, <=800px wide            -> 1600px
#   group_profile/    member avatars, 140px square            ->  512px
#   research_focus/   research cards, 165px wide              ->  500px
#   logo/             left alone; small already, and logos need to stay crisp
# ---------------------------------------------------------------------------
rule_for() {
    case "$1" in
        stories/thumbs/*)  echo "600 80 jpg square" ;;
        stories/*)         echo "2560 82 jpg fit" ;;
        lab_photo/*)       echo "1600 85 jpg fit" ;;
        group_profile/*)   echo "512 85 jpg fit" ;;
        research_focus/*)  echo "500 85 keep fit" ;;
        *)                 echo "" ;;
    esac
}

is_raster() {
    case "${1,,}" in
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

# Generate stories/thumbs/<name>.jpg for any original that has no thumbnail.
#
# With no arguments, scans every original in stories/. With arguments, only the
# given paths are considered, so an explicit run still produces thumbnails —
# passing files used to skip thumbnail generation entirely.
generate_thumbs() {
    mkdir -p stories/thumbs
    local made=0
    local orig base thumb
    local sources=()

    if [ "$#" -gt 0 ]; then
        for orig in "$@"; do
            orig="${orig#./}"
            # optimize_one may have renamed the file to .jpg.
            [ -f "$orig" ] || orig="${orig%.*}.jpg"
            sources+=("$orig")
        done
    else
        sources=(stories/*)
    fi

    for orig in ${sources[@]+"${sources[@]}"}; do
        [ -f "$orig" ] || continue
        # Only originals directly under stories/ get a gallery thumbnail.
        case "$orig" in
            stories/thumbs/*) continue ;;
            stories/*) ;;
            *) continue ;;
        esac
        is_raster "$orig" || continue
        base="$(basename "${orig%.*}")"
        thumb="stories/thumbs/${base}.jpg"
        # A thumbnail under any extension counts as present.
        if compgen -G "stories/thumbs/${base}."* >/dev/null; then
            continue
        fi
        if [ "$CHECK_ONLY" = 1 ]; then
            echo "  would generate  $thumb"
        else
            convert "$orig" -auto-orient -resize "600x600^" -gravity center \
                -extent 600x600 -strip -interlace Plane -sampling-factor 4:2:0 \
                -quality 80 -set comment "$MARKER" "$thumb"
            chmod 644 "$thumb"
            echo "  generated thumbnail  $thumb"
        fi
        made=$((made + 1))
    done
    [ "$made" -gt 0 ] || return 0
}

# When a file changes extension, keep the HTML pointing at it.
rewrite_references() {
    [ "${#RENAMES[@]}" -gt 0 ] || return 0
    local pair old new page
    for pair in "${RENAMES[@]}"; do
        old="${pair%%=>*}"
        new="${pair#*=>}"
        for page in *.html; do
            [ -f "$page" ] || continue
            if grep -qF "$old" "$page"; then
                # Match the path inside an attribute so a shorter name cannot
                # partially match a longer one.
                python3 - "$page" "$old" "$new" <<'PY'
import sys
page, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
text = open(page, encoding="utf-8").read()
for quote in ('"', "'"):
    text = text.replace(f"{quote}{old}{quote}", f"{quote}{new}{quote}")
open(page, "w", encoding="utf-8").write(text)
PY
                echo "  updated reference in $page: $old -> $new"
            fi
        done
    done
}

echo "Optimizing images..."

if [ "${#TARGETS[@]}" -gt 0 ]; then
    for t in "${TARGETS[@]}"; do
        optimize_one "$t"
    done
    generate_thumbs "${TARGETS[@]}"
else
    # Originals first, so generated thumbnails come from the optimized source.
    while IFS= read -r f; do
        optimize_one "$f"
    done < <(find stories lab_photo group_profile research_focus -type f 2>/dev/null | LC_ALL=C sort)
    generate_thumbs
fi

rewrite_references

echo
if [ "$CHECK_ONLY" = 1 ]; then
    echo "$processed file(s) would be optimized, $skipped already optimized."
    echo "Run without --check to apply."
else
    echo "$processed file(s) optimized, $skipped skipped, $(human "$saved_total") saved."
fi
