# Open Heart — CLAUDE.md

## Project
Balatro deep mods via LÖVE 2D engine (C++/ObjC++) modifications paired with Lua game mods. We build LÖVE from source, add new engine capabilities, and write Lua mods that use them.

## Build
```
make build      # clone deps + compile LÖVE from source (~2-5 min first time)
make test       # 5 smoke tests (build artifacts, LÖVE runs, Balatro launches, clean shutdown)
make clean-all  # nuke build/ and deps/ for full rebuild
```

## Architecture
- `scripts/common.sh` — shared paths, config, logging
- `scripts/build-love.sh` — clone love2d repos, copy frameworks, xcodebuild
- `scripts/smoke-test.sh` — verify binary + Balatro compatibility
- `deps/love/` — LÖVE source (11.x branch), where engine mods go (`src/modules/`)
- `build/love.app` — compiled output
- Balatro.love is at `~/Library/Application Support/Steam/steamapps/common/Balatro/Balatro.app/Contents/Resources/Balatro.love`

## No Silent Fallbacks (in tooling/build/test code)

For build scripts, tests, code generation, and all infrastructure: **fail hard and visibly when something is wrong.** No sneaky defaults that hide errors.

- If a value is missing, error loudly. Do NOT substitute a default and continue silently.
- If a test can't determine its result, FAIL — don't show "PASSED" or "SKIPPED" without clear reason.
- If a build step fails, abort with a clear error. Do NOT proceed with partial state.
- No `x or default_value` patterns unless the default is obviously correct and expected.

**Exception: mod runtime code.** Lua mods that run inside Balatro should be defensive — the game crashing is a bad user experience. Graceful fallbacks are fine there (e.g., nil-checks on game state, pcall around risky operations). The distinction: tooling lies to the developer, mods protect the player.

## Conventions
- Shell scripts use `set -euo pipefail` and `die()` for fatal errors
- Balatro requires `steam_appid.txt` (containing `2379780`) in the working directory when launched outside Steam
- Build is arm64-only (Apple Silicon)
- LÖVE engine mods follow the pattern: C++ implementation in `src/modules/<name>/` + Lua bindings in `wrap_*.cpp`
