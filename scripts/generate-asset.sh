#!/usr/bin/env bash
# generate-asset.sh — generate mod art via Gemini image generation API
# Usage: generate-asset.sh <mod_id> <asset_key> "<prompt>" [--model MODEL]

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# --- Parse arguments ---
[ $# -ge 3 ] || die "Usage: generate-asset.sh <mod_id> <asset_key> \"<prompt>\" [--model MODEL]"

MOD_ID="$1"
ASSET_KEY="$2"
PROMPT="$3"
shift 3

MODEL="gemini-2.5-flash-image"
while [ $# -gt 0 ]; do
    case "$1" in
        --model) [ -n "${2:-}" ] || die "--model requires a value"; MODEL="$2"; shift 2 ;;
        *) die "Unknown option: $1" ;;
    esac
done

# --- Validate mod exists ---
MOD_DIR="$PROJECT_ROOT/mods/$MOD_ID"
[ -d "$MOD_DIR" ] || die "Mod directory not found: $MOD_DIR"
[ -f "$MOD_DIR/mod.conf" ] || die "mod.conf not found in $MOD_DIR"

# --- Validate asset key prefix ---
case "$ASSET_KEY" in
    j_*) ;; # joker
    b_*) ;; # back
    t_*) ;; # tarot
    *) die "Asset key must start with a known prefix (j_, b_, t_), got: $ASSET_KEY" ;;
esac

# --- Validate dependencies ---
[ -n "${GEMINI_API_KEY:-}" ] || die "GEMINI_API_KEY environment variable is not set"
command -v jq >/dev/null 2>&1 || die "jq is required but not installed (brew install jq)"

# --- Temp dir with cleanup ---
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

# --- Build prompt with style suffix ---
FULL_PROMPT="${PROMPT}, digital card art, vibrant colors, clean simple background, game asset"
log_info "Prompt: $FULL_PROMPT"
log_info "Model: $MODEL"

# --- Call Gemini API ---
log_info "Generating image..."

API_URL="https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent"

REQUEST_BODY=$(jq -n \
    --arg prompt "$FULL_PROMPT" \
    '{
        contents: [{parts: [{text: $prompt}]}],
        generationConfig: {
            responseModalities: ["IMAGE"],
            imageConfig: { aspectRatio: "3:4" }
        }
    }')

HTTP_CODE=$(curl -s -o "$TEMP_DIR/response.json" -w "%{http_code}" \
    -X POST "$API_URL" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$REQUEST_BODY")

[ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ] || {
    log_error "API returned HTTP $HTTP_CODE"
    cat "$TEMP_DIR/response.json" >&2
    die "Gemini API request failed"
}

# --- Check for API error in response ---
API_ERROR=$(jq -r '.error.message // empty' "$TEMP_DIR/response.json")
[ -z "$API_ERROR" ] || die "Gemini API error: $API_ERROR"

# --- Extract base64 image data ---
IMAGE_DATA=$(jq -r '.candidates[0].content.parts[0].inlineData.data // empty' "$TEMP_DIR/response.json")
[ -n "$IMAGE_DATA" ] || {
    # Try alternate response path
    IMAGE_DATA=$(jq -r '.candidates[0].content.parts[0].inline_data.data // empty' "$TEMP_DIR/response.json")
    [ -n "$IMAGE_DATA" ] || die "No image data in API response. Response: $(cat "$TEMP_DIR/response.json")"
}

MIME_TYPE=$(jq -r '.candidates[0].content.parts[0].inlineData.mimeType // .candidates[0].content.parts[0].inline_data.mimeType // "image/png"' "$TEMP_DIR/response.json")
log_info "Received image (${MIME_TYPE})"

# --- Decode base64 to PNG ---
echo "$IMAGE_DATA" | base64 -D > "$TEMP_DIR/raw_image.png"
[ -s "$TEMP_DIR/raw_image.png" ] || die "Failed to decode base64 image data"

# --- Resize to Balatro sprite dimensions ---
ASSETS_1X="$MOD_DIR/assets/1x"
ASSETS_2X="$MOD_DIR/assets/2x"
mkdir -p "$ASSETS_1X" "$ASSETS_2X"

# 2x: 142x190
cp "$TEMP_DIR/raw_image.png" "$TEMP_DIR/2x.png"
sips -z 190 142 "$TEMP_DIR/2x.png" >/dev/null 2>&1
cp "$TEMP_DIR/2x.png" "$ASSETS_2X/${ASSET_KEY}.png"

# 1x: 71x95
cp "$TEMP_DIR/raw_image.png" "$TEMP_DIR/1x.png"
sips -z 95 71 "$TEMP_DIR/1x.png" >/dev/null 2>&1
cp "$TEMP_DIR/1x.png" "$ASSETS_1X/${ASSET_KEY}.png"

# --- Verify dimensions ---
verify_dims() {
    local file="$1" expected_w="$2" expected_h="$3"
    local w h
    w=$(sips -g pixelWidth "$file" | awk '/pixelWidth/{print $2}')
    h=$(sips -g pixelHeight "$file" | awk '/pixelHeight/{print $2}')
    [ "$w" = "$expected_w" ] && [ "$h" = "$expected_h" ] || \
        die "Dimension mismatch for $file: got ${w}x${h}, expected ${expected_w}x${expected_h}"
}

verify_dims "$ASSETS_1X/${ASSET_KEY}.png" 71 95
verify_dims "$ASSETS_2X/${ASSET_KEY}.png" 142 190

# --- Done ---
log_success "Generated asset: ${ASSET_KEY}"
log_info "  1x: $ASSETS_1X/${ASSET_KEY}.png (71x95)"
log_info "  2x: $ASSETS_2X/${ASSET_KEY}.png (142x190)"
log_info ""
log_info "Next steps:"
log_info "  1. Review the generated images"
log_info "  2. Run 'make install MOD=$MOD_ID' to install with assets"
log_info "  3. Re-generate with a different prompt if needed"
