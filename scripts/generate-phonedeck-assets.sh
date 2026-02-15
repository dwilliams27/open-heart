#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
    echo "Usage: GEMINI_API_KEY=your-key ./scripts/generate-phonedeck-assets.sh"
    exit 1
fi

# make generate MOD=phonedeck ASSET=j_calculator PROMPT="A playing card style image: solid black background with a very subtle radial gradient (lighter at center, darker at edges) filling edge-to-edge to all corners with no border or margin. In the center, a rounded rectangle box containing the iOS Calculator app icon (orange and gray circular buttons in a grid with white math symbols), with a small colorful jester hat perched on top of the box. Small playing card suit symbols (hearts, spades, diamonds, clubs) in each corner of the image. NO TEXT AT ALL"

# make generate MOD=phonedeck ASSET=j_flashlight PROMPT="A playing card style image: blue-gray background with a very subtle radial gradient (lighter at center, darker at edges) filling edge-to-edge to all corners with no border or margin. In the center, a rounded rectangle box containing the iOS Flashlight icon (bold white flashlight silhouette pointing up), with a small colorful jester hat perched on top of the box. Small playing card suit symbols (hearts, spades, diamonds, clubs) in each corner of the image. NO TEXT AT ALL"

# make generate MOD=phonedeck ASSET=j_camera PROMPT="A playing card style image: medium gray background with a very subtle radial gradient (lighter at center, darker at edges) filling edge-to-edge to all corners with no border or margin. In the center, a rounded rectangle box containing the iOS Camera app icon (white camera outline with circular lens), with a small colorful jester hat perched on top of the box. Small playing card suit symbols (hearts, spades, diamonds, clubs) in each corner of the image. NO TEXT AT ALL"

# make generate MOD=phonedeck ASSET=j_fitness PROMPT="A playing card style image: black background with a very subtle radial gradient (lighter at center, darker at edges) filling edge-to-edge to all corners with no border or margin. In the center, a rounded rectangle box containing the iOS Fitness app icon (colorful concentric activity rings — red, green, blue), with a small colorful jester hat perched on top of the box. Small playing card suit symbols (hearts, spades, diamonds, clubs) in each corner of the image. NO TEXT AT ALL"

# make generate MOD=phonedeck ASSET=j_maps PROMPT="A playing card style image: grass green background with a very subtle radial gradient (lighter at center, darker at edges) filling edge-to-edge to all corners with no border or margin. In the center, a rounded rectangle box containing the Apple Maps app icon (a colorful road map with a blue navigation arrow and roads), with a small colorful jester hat perched on top of the box. Small playing card suit symbols (hearts, spades, diamonds, clubs) in each corner of the image. NO TEXT AT ALL"

# make generate MOD=phonedeck ASSET=j_alarm PROMPT="A playing card style image: warm orange-yellow background with a very subtle radial gradient (lighter at center, darker at edges) filling edge-to-edge to all corners with no border or margin. In the center, a rounded rectangle box containing the iOS Clock app icon (a white clock face with black hour and minute hands on a black background), with a small colorful jester hat perched on top of the box. Small playing card suit symbols (hearts, spades, diamonds, clubs) in each corner of the image. NO TEXT AT ALL"

make generate MOD=phonedeck ASSET=j_playlist PROMPT="A playing card style image: deep magenta-pink background with a very subtle radial gradient (lighter at center, darker at edges) filling edge-to-edge to all corners with no border or margin. In the center, a rounded rectangle box containing the Apple Music app icon (white music note on a red-to-pink gradient), with a small colorful jester hat perched on top of the box. Small playing card suit symbols (hearts, spades, diamonds, clubs) in each corner of the image. NO TEXT AT ALL"

make generate MOD=phonedeck ASSET=j_battery PROMPT="A playing card style image: bright green background with a very subtle radial gradient (lighter at center, darker at edges) filling edge-to-edge to all corners with no border or margin. In the center, a rounded rectangle box containing a battery icon (horizontal battery shape with green charge level bars and a lightning bolt symbol), with a small colorful jester hat perched on top of the box. Small playing card suit symbols (hearts, spades, diamonds, clubs) in each corner of the image. NO TEXT AT ALL"

echo ""
echo "Done! Run 'make install MOD=phonedeck' to install with new assets."
