# Open Heart — CLAUDE.md

## Project
Balatro deep mods via LÖVE 2D engine (C++/ObjC++) modifications paired with Lua game mods. We build LÖVE from source, add new engine capabilities, and write Lua mods that use them.

## Build
```
make build      # clone deps + compile LÖVE from source (~2-5 min first time)
make test       # 7 smoke tests (build artifacts, LÖVE runs, HTTPS module, Balatro launches, clean shutdown)
make clean-all  # nuke build/ and deps/ for full rebuild
```

## Architecture
- `engine/` — our engine module source (version-controlled), copied into `deps/love/` at build time
- `scripts/common.sh` — shared paths, config, logging
- `scripts/build-love.sh` — clone love2d repos, copy frameworks, patch, xcodebuild
- `scripts/patch-love.sh` — idempotent script that integrates `engine/` mods into LÖVE source
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

## Conventions
- Shell scripts use `set -euo pipefail` and `die()` for fatal errors
- Balatro requires `steam_appid.txt` (containing `2379780`) in the working directory when launched outside Steam
- Build is arm64-only (Apple Silicon)
- Engine mods: source lives in `engine/<name>/`, patched into `deps/love/src/modules/<name>/` by `scripts/patch-love.sh`
- LÖVE module pattern: C++ implementation + Lua bindings in `wrap_*.cpp`, registered via `WrappedModule` in `luaopen_love_<name>`
