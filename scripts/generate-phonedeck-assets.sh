#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
    echo "Usage: GEMINI_API_KEY=your-key ./scripts/generate-phonedeck-assets.sh"
    exit 1
fi

# --- App icon style prompts (square, centered on transparent card) ---
# --square: generates 1:1 image, rounds corners, centers on transparent card

# make generate SQUARE=1 MOD=phonedeck ASSET=j_calculator PROMPT="A simple app icon: dark black background, a clean grid of colorful round calculator buttons with math symbols (plus, minus, multiply, equals), with a tiny jester hat sitting on top. Flat design, bold colors, minimal detail, clean and iconic like an iOS app icon. NO TEXT AT ALL"

# make generate SQUARE=1 MOD=phonedeck ASSET=j_flashlight PROMPT="A simple app icon: dark blue-gray background, a bold white flashlight silhouette pointing upward with a bright golden glow beam radiating from the top, with a tiny jester hat on the flashlight handle. Flat design, bold colors, minimal detail, clean and iconic like an iOS app icon. NO TEXT AT ALL"

# make generate SQUARE=1 MOD=phonedeck ASSET=j_fitness PROMPT="A simple app icon: black background, three colorful concentric activity rings (red outer, green middle, blue inner) like the Apple Fitness icon, with a tiny jester hat perched on top of the rings. Flat design, bold colors, minimal detail, clean and iconic like an iOS app icon. NO TEXT AT ALL"

# make generate SQUARE=1 MOD=phonedeck ASSET=j_camera PROMPT="A simple app icon: medium gray background, a clean white camera silhouette with a circular lens in the center, with a tiny jester hat sitting on top of the camera. Flat design, bold colors, minimal detail, clean and iconic like an iOS app icon. NO TEXT AT ALL"

# make generate SQUARE=1 MOD=phonedeck ASSET=j_maps PROMPT="A simple app icon: green background, a colorful stylized road map with a bright blue navigation arrow pointing forward, with a tiny jester hat on the arrow. Flat design, bold colors, minimal detail, clean and iconic like an iOS app icon. NO TEXT AT ALL"

# make generate SQUARE=1 MOD=phonedeck ASSET=j_alarm PROMPT="A simple app icon: warm orange background, a bold old-fashioned alarm clock with two bells on top and clock hands pointing to midnight, with a tiny jester hat between the bells. Flat design, bold colors, minimal detail, clean and iconic like an iOS app icon. NO TEXT AT ALL"

# make generate SQUARE=1 MOD=phonedeck ASSET=j_playlist PROMPT="A simple app icon: red-to-pink gradient background, a bold white musical note symbol in the center, with a tiny jester hat on top of the note. Flat design, bold colors, minimal detail, clean and iconic like an iOS app icon. NO TEXT AT ALL"

# make generate SQUARE=1 MOD=phonedeck ASSET=j_battery PROMPT="A simple app icon: bright green background, a bold white horizontal battery shape with green charge level bars inside and a small lightning bolt symbol, with a tiny jester hat on top of the battery. Flat design, bold colors, minimal detail, clean and iconic like an iOS app icon. NO TEXT AT ALL"

# make generate SQUARE=1 MOD=phonedeck ASSET=j_stocks PROMPT="A simple app icon: dark navy background, a bold green zigzagging stock chart line trending upward with a few gold coin symbols scattered around, with a tiny jester hat on the peak of the chart. Flat design, bold colors, minimal detail, clean and iconic like an iOS app icon. NO TEXT AT ALL"

# make generate SQUARE=1 MOD=phonedeck ASSET=j_dnd PROMPT="A simple app icon: deep purple background, a bold white crescent moon symbol in the center, with a tiny jester hat resting on the tip of the moon. Flat design, bold colors, minimal detail, clean and iconic like an iOS app icon. NO TEXT AT ALL"

# Deck back uses standard (non-square) mode — fills the whole card
make generate MOD=phonedeck ASSET=b_smartphone PROMPT="A flat illustration of the rear panel of a smartphone, as if the phone IS the image. The entire image is the phone's back surface filling edge to edge. Dark metallic gunmetal body. A camera module with two lenses in the upper left area. The rest of the surface is a decorative phone case skin with an ornate Balatro jester pattern: repeating playing card suits (hearts, spades, diamonds, clubs) and small colorful joker faces in rich reds, golds, and purples. First-person perspective looking directly at the back of the phone. NO TEXT AT ALL"

echo ""
echo "Done! Run 'make install MOD=phonedeck' to install with new assets."
