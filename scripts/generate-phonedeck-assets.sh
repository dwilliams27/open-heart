#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
    echo "Usage: GEMINI_API_KEY=your-key ./scripts/generate-phonedeck-assets.sh"
    exit 1
fi

make generate MOD=phonedeck ASSET=j_calculator PROMPT="The Apple iOS Calculator app icon, almost identical to the real thing: solid black background, rounded rectangle shape, a grid of circular buttons — orange buttons on the right column, dark gray buttons in the middle rows, light gray buttons on the top row, white mathematical symbols on each button. Exactly like a screenshot of the real iOS calculator app icon. Add only a very subtle jester hat sitting on top of the icon and tiny card suit watermarks in the corners. NO TEXT AT ALL"

make generate MOD=phonedeck ASSET=j_flashlight PROMPT="The Apple iOS Flashlight icon from Control Center, almost identical to the real thing: a simple bold white flashlight silhouette pointing upward on a blue-gray gradient background, rounded rectangle app icon shape. Clean flat design, exactly like the real iOS flashlight toggle icon. Add only a very subtle jester hat sitting on top of the icon and tiny card suit watermarks in the corners. NO TEXT AT ALL"

echo ""
echo "Done! Run 'make install MOD=phonedeck' to install with new assets."
