# Balatro Deep Mods

## Goal

Generate Balatro mods that are impossible with existing tools. Every mod ever made for Balatro (~400+) operates at the Lua scripting layer. We go deeper: modify the LÖVE 2D engine's C++ source code to add entirely new capabilities, then write Lua mods that use them. The AI generates both halves — engine code and game code — as coherent pairs.

## Why This Is Interesting

Balatro is a poker roguelike built on LÖVE (an open-source Lua game engine). The full game is ~30k lines of readable Lua. The modding community is active but constrained: they can create new Jokers, Decks, Consumables, and UI tweaks, but they can never escape LÖVE's built-in capabilities. No one has ever shipped a Balatro mod that modifies the engine itself.

We build LÖVE from source with new modules baked in, and write Lua mods that call APIs that didn't exist before.

## Architecture

```
Balatro game logic (Lua, ~30k lines)         ← We write mods here too
        ↕
LÖVE 11.5 engine (C++/ObjC++, open source)   ← We modify and rebuild this
        ↕
macOS / Apple Silicon (AppKit, OpenAL, OpenGL, SDL2)
```

LÖVE is MIT-licensed. We clone the `11.x` branch, add our modifications, build with Xcode, and run Balatro on the custom binary. The game doesn't care — it just needs a LÖVE-compatible runtime. No DYLD injection, no code signing hacks. Build from source, ad-hoc sign, run.

## macOS Build Workflow

1. Clone `https://github.com/love2d/love.git` (branch `11.x`)
2. Clone `https://github.com/love2d/love-apple-dependencies.git` and place the macOS Frameworks and shared dependencies into the Xcode project directories
3. Open `platform/xcode/love.xcodeproj`, build the `love-macosx` target
4. Run: `./love.app/Contents/MacOS/love /path/to/Balatro.love`

Balatro's game data (`Balatro.love`) is extracted from the Steam install at `~/Library/Application Support/Steam/steamapps/common/Balatro/Balatro.app/Contents/Resources/`. It's a zip archive containing all the Lua source and assets.

Lua-side mods install to `~/Library/Application Support/Balatro/Mods/` and use the Steamodded (SMODS) framework.

## LÖVE Engine Modification Pattern

Every LÖVE module lives in `src/modules/<name>/` and follows the same structure:

- `Module.h/.cpp` — the C++ implementation
- `wrap_Module.cpp` — Lua bindings (a `luaL_Reg` function table that defines what's available as `love.<module>.<function>()`)

To add a new Lua-callable engine feature: implement it in C++, write a thin wrapper function in `wrap_*.cpp`, and register it in the function table. That's it.

---

## Engine-Level Mods (Things Nobody Has Built)

### Real-Time Audio Synthesis & DSP

LÖVE's audio module can play pre-recorded sounds. It cannot generate audio. We add a `SynthSource` — a new audio source type that produces PCM waveforms procedurally (sine, saw, square oscillators with envelope, frequency, and distortion controls). The Lua API looks like:

```lua
local synth = love.audio.newSynthSource()
synth:setWaveform("saw")
synth:setFrequency(440)
synth:setDistortion(0.3)
synth:play()
```

The Balatro integration: hook into the scoring pipeline so every hand produces unique procedural audio. Card chip values control pitch, mult controls harmonic richness, xMult adds overtones. A big scoring combo sounds like a rising, distorted crescendo. Every hand sounds different.

### Multi-Window Rendering

LÖVE exposes exactly one window. SDL2 supports many, but LÖVE doesn't surface this. We add secondary window creation and a graphics context-switching API:

```lua
love.window.createSecondary("Dashboard", 400, 600)
love.graphics.setTargetWindow(2)
-- draw with normal love.graphics calls
love.graphics.setTargetWindow(1)  -- back to main game
```

The Balatro integration: a Joker that opens a second macOS window showing a live analytics dashboard — score accumulation graph, per-joker contribution breakdown, and a predictive curve for whether your build can beat the next blind. Updates in real-time as you play.

### Time Dilation

We add `love.timer.setTimeScale(n)` by modifying the timer module's `step()` function to scale delta-time before it reaches Lua. When a Joker calls `setTimeScale(0.25)`, the entire game — every animation, tween, and particle — decelerates uniformly. No split-brain timing issues that plague Lua-only hacks.

The Balatro integration: as your score approaches the blind threshold, time slows to a crawl. Cross the threshold and it snaps back. Running out of hands? Time accelerates. Panic mode.

### Force Touch Haptics

MacBooks with Force Touch trackpads support `NSHapticFeedbackManager`. LÖVE has zero haptic support. We add `love.system.hapticTap(intensity)` via a small Objective-C++ bridge (~50 lines).

The Balatro integration: each scored card produces a light tap, mult applications a medium pulse, boss blind defeat a heavy thud. You feel the scoring.

---

## Lua-Level Mods (Pushing the Existing Layer Further)

### Physics-Driven Card Animation

After scoring, played cards explode outward with real physics — tumbling, bouncing off screen edges and each other, settling into piles. Uses `love.physics` (Box2D), which is compiled into LÖVE but no Balatro mod has ever used. Cards that collide award bonus chips.

This is pure Lua — no engine modification — but it's a novel use of an engine capability the modding community has ignored entirely.

### Themed Content Generation: "Pharaoh's Court"

A coherent ancient Egypt-themed mod pack: 8-10 Jokers, 2 Decks, and custom enhancements. The AI generates balanced effects with thematic flavor text, and designs jokers that synergize with each other to create new build archetypes. Examples:

- **Scarab** — Gold Seal synergy, chip bonus
- **Ankh** — Joker resurrection (destroyed jokers come back with Eternal)
- **Eye of Horus** — Mult scaling based on suit diversity
- **Pharaoh's Crook** — Reverses card evaluation order (right-to-left scoring)

The point isn't just "make some jokers" — it's generating a pack where the effects interlock, the theming is consistent, and the balance is reasonable. This is content design, not just code generation.

---

## What Makes This a System

Each engine mod is a pair: C++ that adds a capability + Lua that uses it in a game-meaningful way. The AI reads both the LÖVE engine source and Balatro's game code, then generates modifications that span both layers. That cross-layer synthesis — understanding where the engine boundary is and designing mods that deliberately cross it — is the core contribution.

The Lua-only mods prove the AI can also generate high-quality content within existing constraints. Together, they show a system that operates at every level of the stack.
