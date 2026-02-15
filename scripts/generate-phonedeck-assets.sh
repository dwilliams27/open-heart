#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
    echo "Usage: GEMINI_API_KEY=your-key ./scripts/generate-phonedeck-assets.sh"
    exit 1
fi

# --- Balatro-style joker art prompts ---
# Style: expressive cartoon joker characters, vibrant colors, filling edge-to-edge

# make generate MOD=phonedeck ASSET=j_calculator PROMPT="A Balatro-style playing card image: dark purple background filling edge-to-edge to all corners with no border or margin. A mischievous grinning jester hunched over a giant oversized retro calculator, mashing buttons frantically. Glowing golden numbers and math symbols swirl off the calculator screen into the air. The jester wears a classic two-pointed hat with bells. Vibrant colors, bold outlines, cartoony style. NO TEXT AT ALL"

# make generate MOD=phonedeck ASSET=j_flashlight PROMPT="A Balatro-style playing card image: deep dark blue background filling edge-to-edge to all corners with no border or margin. A detective jester in a trenchcoat holding a giant glowing flashlight, casting a dramatic golden cone of light that illuminates a single sparkling playing card floating in darkness. Everything outside the beam is shadowy. The jester peers with one eye squinted. Vibrant colors, bold outlines, cartoony style. NO TEXT AT ALL"

# make generate MOD=phonedeck ASSET=j_fitness PROMPT="A Balatro-style playing card image: bright orange background filling edge-to-edge to all corners with no border or margin. A buff muscular jester wearing a sweatband and tiny running shoes, flexing both arms triumphantly. Small poker chips bounce around like they are being juggled. The jester has an enthusiastic wide grin. Vibrant colors, bold outlines, cartoony style. NO TEXT AT ALL"

# make generate MOD=phonedeck ASSET=j_camera PROMPT="A Balatro-style playing card image: warm magenta background filling edge-to-edge to all corners with no border or margin. A photographer jester peering through a big vintage polaroid camera with a dramatic flash starburst going off. A freshly-taken polaroid photo floats in the air showing a ghostly poker hand. Film strips with card suit symbols curl around the edges. Vibrant colors, bold outlines, cartoony style. NO TEXT AT ALL"

# make generate MOD=phonedeck ASSET=j_maps PROMPT="A Balatro-style playing card image: forest green background filling edge-to-edge to all corners with no border or margin. An adventurer jester wearing an explorer hat, holding up a glowing treasure map that unfurls dramatically. The map shows winding paths connecting card suit landmarks with a dotted trail between them. A golden compass spins nearby. The jester looks excited and determined. Vibrant colors, bold outlines, cartoony style. NO TEXT AT ALL"

# make generate MOD=phonedeck ASSET=j_alarm PROMPT="A Balatro-style playing card image: fiery red-orange background filling edge-to-edge to all corners with no border or margin. A panicked wild-eyed jester slamming both hands down on a giant old-fashioned alarm clock that is ringing violently with visible shockwaves radiating outward. The clock bells shake wildly, lightning bolts and exclamation sparks fly everywhere. The whole scene feels urgent and electric. Vibrant colors, bold outlines, cartoony style. NO TEXT AT ALL"

# make generate MOD=phonedeck ASSET=j_playlist PROMPT="A Balatro-style playing card image: deep magenta-pink background filling edge-to-edge to all corners with no border or margin. A cool DJ jester wearing oversized headphones, spinning a vinyl record on a turntable with one hand raised. Musical notes shaped like card suits flow from the headphones in a repeating pattern. The vinyl record glows with rainbow concentric rings. Equalizer bars rise behind the jester. Vibrant colors, bold outlines, cartoony style. NO TEXT AT ALL"

# make generate MOD=phonedeck ASSET=j_battery PROMPT="A Balatro-style playing card image: electric green background filling edge-to-edge to all corners with no border or margin. A hyperactive jester hugging a massive crackling battery that sparks with electricity. The battery glows bright green at the top fading to dim red at the bottom showing charge level. Electric arcs jump between the battery terminals and nearby playing cards, charging them up. The jester's hat stands on end from static. Vibrant colors, bold outlines, cartoony style. NO TEXT AT ALL"

# make generate MOD=phonedeck ASSET=j_stocks PROMPT="A Balatro-style playing card image: dark navy background filling edge-to-edge to all corners with no border or margin. A wall street trader jester in a pinstripe suit on a chaotic trading floor, gripping a zigzagging stock chart that rockets upward then crashes down. Gold coins and dollar signs rain from the peaks while the valleys scatter broken coins. Other tiny panicked jesters run around in the background. A ticker tape made of miniature playing cards streams across. The main jester has diamond-shaped cufflinks and a manic grin. Vibrant colors, bold outlines, cartoony style. NO TEXT AT ALL"

make generate MOD=phonedeck ASSET=j_dnd PROMPT="A Balatro-style playing card image: deep purple-black background filling edge-to-edge to all corners with no border or margin. A serene zen monk jester sitting cross-legged in perfect meditation, eyes closed, surrounded by a glowing purple bubble shield of silence. Outside the bubble, chaotic boss monsters and dark shadowy claws rage and claw at the shield but cannot break through. A crescent moon floats above the jester's head. Inside the bubble everything is peaceful and still. Vibrant colors, bold outlines, cartoony style. NO TEXT AT ALL"

# make generate MOD=phonedeck ASSET=b_smartphone PROMPT="A Balatro-style playing card back design: a sleek glowing smartphone as the centerpiece on a rich dark background filling edge-to-edge with no border or margin. The phone screen shows a colorful grid of tiny app icons, each icon shaped like a different card suit or joker symbol. The phone frame is ornate and jeweled like a luxury case. Radiating signal waves emanate from the phone in concentric circles. Circuit board trace patterns in the background. Vibrant colors, bold outlines. NO TEXT AT ALL"

echo ""
echo "Done! Run 'make install MOD=phonedeck' to install with new assets."
