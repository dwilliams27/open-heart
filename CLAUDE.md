# Open Heart — CLAUDE.md

## Project
Balatro deep mods via LÖVE 2D engine (C++/ObjC++) modifications paired with Lua game mods. We build LÖVE from source, add new engine capabilities, and write Lua mods that use them.

## Build
```
make build              # build LÖVE with all engine modules needed by all mods
make build MOD=example  # build LÖVE with only engine modules needed by a specific mod
make test               # 7 smoke tests (build artifacts, LÖVE runs, HTTPS module, Balatro launches, clean shutdown)
make install            # install all mods' Lua files to Balatro Mods/
make install MOD=example  # install a specific mod
make clean-all          # nuke build/ and deps/ for full rebuild
```

## Architecture
- `engine/` — engine module source (version-controlled), each with a `module.conf` manifest
- `mods/` — Lua mods, each with a `mod.conf` manifest declaring engine dependencies
- `scripts/common.sh` — shared paths, config, logging, `xcode_id()`, `xcode_filetype()`
- `scripts/build-love.sh` — clone love2d repos, resolve engine deps from mod configs, patch, xcodebuild
- `scripts/patch-love.sh` — generic data-driven script: takes module names as args, sources each `module.conf`
- `scripts/install-mod.sh` — copy mod Lua files to `~/Library/Application Support/Balatro/Mods/`
- `scripts/smoke-test.sh` — verify binary + Balatro compatibility
- `deps/love/` — LÖVE source (11.x branch), patched at build time (not version-controlled)
- `build/love.app` — compiled output
- Balatro.love is at `~/Library/Application Support/Steam/steamapps/common/Balatro/Balatro.app/Contents/Resources/Balatro.love`

## No Silent Fallbacks (in tooling/build/test code)

For build scripts, tests, code generation, and all infrastructure: **fail hard and visibly when something is wrong.** No sneaky defaults that hide errors.

- If a value is missing, error loudly. Do NOT substitute a default and continue silently.
- If a test can't determine its result, FAIL — don't show "PASSED" or "SKIPPED" without clear reason.
- If a build step fails, abort with a clear error. Do NOT proceed with partial state.
- No `x or default_value` patterns unless the default is obviously correct and expected.

**Exception: mod runtime code.** Lua mods that run inside Balatro should be defensive — the game crashing is a bad user experience. Graceful fallbacks are fine there (e.g., nil-checks on game state, pcall around risky operations). The distinction: tooling lies to the developer, mods protect the player.

## Engine Module Manifest: `module.conf`

Each engine module in `engine/<name>/` has a shell-sourceable `module.conf`:

```bash
MODULE_NAME="https"           # module name (matches directory)
MODULE_ENUM="M_HTTPS"         # Module.h enum value
MODULE_DEFINE="LOVE_ENABLE_HTTPS"  # config.h #define
MODULE_LUAOPEN="luaopen_love_https" # Lua module opener function
MODULE_FILES="Https.h Https.mm ..." # all files (headers + sources)
MODULE_SOURCES="Https.mm ..."       # compilable files only (.cpp/.mm/.c/.m)
```

All 6 fields are required. `patch-love.sh` validates them and fails hard on missing fields. Xcode project IDs are generated deterministically via `xcode_id()` (md5 hash) — no hand-picking IDs.

### Adding a new engine module
1. Create `engine/<name>/` with C++/ObjC++ source files
2. Create `engine/<name>/module.conf` with all 6 fields
3. `make clean-all && make build` — patches are applied automatically

## Mod Manifest: `mod.conf`

Each mod in `mods/<id>/` has a shell-sourceable `mod.conf`:

```bash
MOD_NAME="Example"          # display name (used as Mods/ subdirectory)
MOD_ID="example"            # identifier (matches directory)
MOD_DESCRIPTION="..."       # human-readable description
MOD_ENGINE_DEPS="https"     # space-separated engine module names (or "" for Lua-only)
MOD_LUA_ENTRY="Example.lua" # entry point Lua file
```

Mod Lua files live in `mods/<id>/lua/` and get installed to `~/Library/Application Support/Balatro/Mods/<MOD_NAME>/`.

## Engine Modules

### love.https
Async HTTPS client using macOS NSURLSession. Source in `engine/https/` (8 files). HTTPS-only (throws on `http://`).

```lua
-- Fire request (non-blocking, returns immediately)
local req = love.https.request("https://example.com/api")

-- With options
local req = love.https.request("https://example.com/api", {
    method = "POST",
    headers = { ["Content-Type"] = "application/json" },
    body = '{"key": "value"}',
    timeout = 10,
})

-- Poll in update loop
function love.update(dt)
    if req and req:isComplete() then
        local status, body, headers = req:getResponse()
        -- status: HTTP code (200, 404...) or 0 on network error
        -- body: response string, or error message if status == 0
        -- headers: table of response headers
        req = nil
    end
end
```

**In mods:** wrap `love.https.request()` in `pcall` and handle status 0 (network error) gracefully — the player may be offline.

## Asset Generation

AI-powered sprite generation for mod assets using Google Gemini.

### Setup
Set `GEMINI_API_KEY` environment variable (Google AI API key). Requires `jq` (`brew install jq`).

### Usage
```
make generate MOD=weatherdeck ASSET=j_weatherman PROMPT="cheerful weatherman with umbrella"
make generate MOD=weatherdeck ASSET=j_weatherman PROMPT="..." MODEL=gemini-3-pro-image-preview
```

Or directly:
```bash
scripts/generate-asset.sh <mod_id> <asset_key> "<prompt>" [--model MODEL]
```

Asset key prefixes: `j_` (joker), `b_` (back), `t_` (tarot).

Models: `gemini-2.5-flash-image` (default, fast/cheap for iteration), `gemini-3-pro-image-preview` (higher quality for final art).

### Asset directory convention
```
mods/<mod_id>/assets/
├── 1x/          # 71x95 per sprite
│   └── j_key.png
└── 2x/          # 142x190 per sprite
    └── j_key.png
```

Assets are installed alongside Lua files by `make install`.

### Lua sprite loading pattern
```lua
-- oh_load_sprite(center_key, asset_key, mod_dir)
-- Loads a custom sprite atlas and points the center at it.
-- Graceful fallback: if asset missing, vanilla sprite remains.
oh_load_sprite("j_weatherman", "j_weatherman", "Mods/WeatherDeck")
```

Call after registering the center in `init_item_prototypes`. Uses `pcall` (mod runtime = defensive).

**Important:** Vanilla `Card:set_sprites` hardcodes `G.ASSET_ATLAS[_center.set]` for jokers/consumables/vouchers on initial sprite creation, ignoring `_center.atlas`. WeatherDeck includes a `Card:set_sprites` post-hook that fixes this — any mod using custom sprites should include the same hook (or it should be extracted to a shared helper if multiple mods need it).

## Conventions
- Shell scripts use `set -euo pipefail` and `die()` for fatal errors
- Balatro requires `steam_appid.txt` (containing `2379780`) in the working directory when launched outside Steam
- Build is arm64-only (Apple Silicon)
- Engine mods: source lives in `engine/<name>/`, patched into `deps/love/src/modules/<name>/` by `scripts/patch-love.sh`
- LÖVE module pattern: C++ implementation + Lua bindings in `wrap_*.cpp`, registered via `WrappedModule` in `luaopen_love_<name>`
