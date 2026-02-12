#!/usr/bin/env bash
# patch-love.sh — apply Open Heart engine mods to deps/love/ (idempotent)

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

log_info "Patching LÖVE source with engine mods..."

LOVE_SRC="$DEPS_DIR/love/src"
LOVE_MODULES="$LOVE_SRC/modules"
PBXPROJ="$DEPS_DIR/love/platform/xcode/liblove.xcodeproj/project.pbxproj"

# macOS sed doesn't interpret \t in replacement text, so use a literal tab
T="$(printf '\t')"

# --- 1. Copy engine/https/ source files ---
log_info "Copying engine/https/ files..."
ENGINE_HTTPS="$PROJECT_ROOT/engine/https"
DEST_HTTPS="$LOVE_MODULES/https"

if [ ! -d "$ENGINE_HTTPS" ]; then
    die "engine/https/ directory not found at $ENGINE_HTTPS"
fi

mkdir -p "$DEST_HTTPS"
rsync -a "$ENGINE_HTTPS/" "$DEST_HTTPS/"

# --- 2. Patch Module.h: add M_HTTPS before M_MAX_ENUM ---
MODULE_H="$LOVE_SRC/common/Module.h"
if ! grep -q 'M_HTTPS' "$MODULE_H"; then
    log_info "Patching Module.h..."
    sed -i '' "s/${T}${T}M_MAX_ENUM/${T}${T}M_HTTPS,\\
${T}${T}M_MAX_ENUM/" "$MODULE_H"
else
    log_info "Module.h already patched"
fi

# --- 3. Patch config.h: add LOVE_ENABLE_HTTPS ---
CONFIG_H="$LOVE_SRC/common/config.h"
if ! grep -q 'LOVE_ENABLE_HTTPS' "$CONFIG_H"; then
    log_info "Patching config.h..."
    sed -i '' "/#${T}define LOVE_ENABLE_WINDOW/a\\
\\
#${T}define LOVE_ENABLE_HTTPS
" "$CONFIG_H"
else
    log_info "config.h already patched"
fi

# --- 4. Patch love.cpp: add extern and module table entry ---
LOVE_CPP="$LOVE_MODULES/love/love.cpp"
if ! grep -q 'luaopen_love_https' "$LOVE_CPP"; then
    log_info "Patching love.cpp..."
    # Insert extern declaration before luaopen_love_nogame
    sed -i '' "/extern int luaopen_love_nogame/i\\
#if defined(LOVE_ENABLE_HTTPS)\\
${T}extern int luaopen_love_https(lua_State*);\\
#endif
" "$LOVE_CPP"
    # Insert module table entry before { "love.nogame"
    sed -i '' "/{ \"love.nogame\"/i\\
#if defined(LOVE_ENABLE_HTTPS)\\
${T}{ \"love.https\", luaopen_love_https },\\
#endif
" "$LOVE_CPP"
else
    log_info "love.cpp already patched"
fi

# --- 5. Patch boot.lua: add https to module load list and default config ---
BOOT_LUA="$LOVE_MODULES/love/boot.lua"
if ! grep -q '"https"' "$BOOT_LUA"; then
    log_info "Patching boot.lua..."
    # Add to module load list (after "physics")
    sed -i '' "/\"physics\",/a\\
${T}${T}\"https\",
" "$BOOT_LUA"
    # Add to default config (after video = true)
    sed -i '' "/video = true,/a\\
${T}${T}${T}https = true,
" "$BOOT_LUA"
else
    log_info "boot.lua already patched"
fi

# --- 6. Patch project.pbxproj: add https module files to Xcode project ---
if ! grep -q '0F0F0F0F0F000001000E1D17' "$PBXPROJ"; then
    log_info "Patching project.pbxproj..."

    # Deterministic IDs:
    # PBXFileReference IDs:
    #   HttpsRequest.h       = 0F0F0F0F0F000001000E1D17
    #   HttpsRequest.cpp     = 0F0F0F0F0F000002000E1D17
    #   Https.h              = 0F0F0F0F0F000003000E1D17
    #   Https.mm             = 0F0F0F0F0F000004000E1D17
    #   wrap_HttpsRequest.h  = 0F0F0F0F0F000005000E1D17
    #   wrap_HttpsRequest.cpp= 0F0F0F0F0F000006000E1D17
    #   wrap_Https.h         = 0F0F0F0F0F000007000E1D17
    #   wrap_Https.cpp       = 0F0F0F0F0F000008000E1D17
    # PBXBuildFile IDs (macOS target):
    #   HttpsRequest.cpp     = 0F0F0F0F0F000012000E1D17
    #   Https.mm             = 0F0F0F0F0F000014000E1D17
    #   wrap_HttpsRequest.cpp= 0F0F0F0F0F000016000E1D17
    #   wrap_Https.cpp       = 0F0F0F0F0F000018000E1D17
    # PBXGroup for https:
    #   https group          = 0F0F0F0F0F000020000E1D17

    # 6a. Add PBXBuildFile entries
    sed -i '' "/\/\* Begin PBXBuildFile section \*\//a\\
${T}${T}0F0F0F0F0F000012000E1D17 /* HttpsRequest.cpp in Sources */ = {isa = PBXBuildFile; fileRef = 0F0F0F0F0F000002000E1D17 /* HttpsRequest.cpp */; };\\
${T}${T}0F0F0F0F0F000014000E1D17 /* Https.mm in Sources */ = {isa = PBXBuildFile; fileRef = 0F0F0F0F0F000004000E1D17 /* Https.mm */; };\\
${T}${T}0F0F0F0F0F000016000E1D17 /* wrap_HttpsRequest.cpp in Sources */ = {isa = PBXBuildFile; fileRef = 0F0F0F0F0F000006000E1D17 /* wrap_HttpsRequest.cpp */; };\\
${T}${T}0F0F0F0F0F000018000E1D17 /* wrap_Https.cpp in Sources */ = {isa = PBXBuildFile; fileRef = 0F0F0F0F0F000008000E1D17 /* wrap_Https.cpp */; };
" "$PBXPROJ"

    # 6b. Add PBXFileReference entries
    sed -i '' "/\/\* Begin PBXFileReference section \*\//a\\
${T}${T}0F0F0F0F0F000001000E1D17 /* HttpsRequest.h */ = {isa = PBXFileReference; fileEncoding = 4; lastKnownFileType = sourcecode.c.h; path = HttpsRequest.h; sourceTree = \"<group>\"; };\\
${T}${T}0F0F0F0F0F000002000E1D17 /* HttpsRequest.cpp */ = {isa = PBXFileReference; fileEncoding = 4; lastKnownFileType = sourcecode.cpp.cpp; path = HttpsRequest.cpp; sourceTree = \"<group>\"; };\\
${T}${T}0F0F0F0F0F000003000E1D17 /* Https.h */ = {isa = PBXFileReference; fileEncoding = 4; lastKnownFileType = sourcecode.c.h; path = Https.h; sourceTree = \"<group>\"; };\\
${T}${T}0F0F0F0F0F000004000E1D17 /* Https.mm */ = {isa = PBXFileReference; fileEncoding = 4; lastKnownFileType = sourcecode.cpp.objcpp; path = Https.mm; sourceTree = \"<group>\"; };\\
${T}${T}0F0F0F0F0F000005000E1D17 /* wrap_HttpsRequest.h */ = {isa = PBXFileReference; fileEncoding = 4; lastKnownFileType = sourcecode.c.h; path = wrap_HttpsRequest.h; sourceTree = \"<group>\"; };\\
${T}${T}0F0F0F0F0F000006000E1D17 /* wrap_HttpsRequest.cpp */ = {isa = PBXFileReference; fileEncoding = 4; lastKnownFileType = sourcecode.cpp.cpp; path = wrap_HttpsRequest.cpp; sourceTree = \"<group>\"; };\\
${T}${T}0F0F0F0F0F000007000E1D17 /* wrap_Https.h */ = {isa = PBXFileReference; fileEncoding = 4; lastKnownFileType = sourcecode.c.h; path = wrap_Https.h; sourceTree = \"<group>\"; };\\
${T}${T}0F0F0F0F0F000008000E1D17 /* wrap_Https.cpp */ = {isa = PBXFileReference; fileEncoding = 4; lastKnownFileType = sourcecode.cpp.cpp; path = wrap_Https.cpp; sourceTree = \"<group>\"; };
" "$PBXPROJ"

    # 6c. Add PBXGroup for https module (before the timer group)
    sed -i '' "/FA0B7CB71A95902C000E1D17 \/\* timer \*\/ = {/i\\
${T}${T}0F0F0F0F0F000020000E1D17 /* https */ = {\\
${T}${T}${T}isa = PBXGroup;\\
${T}${T}${T}children = (\\
${T}${T}${T}${T}0F0F0F0F0F000001000E1D17 /* HttpsRequest.h */,\\
${T}${T}${T}${T}0F0F0F0F0F000002000E1D17 /* HttpsRequest.cpp */,\\
${T}${T}${T}${T}0F0F0F0F0F000003000E1D17 /* Https.h */,\\
${T}${T}${T}${T}0F0F0F0F0F000004000E1D17 /* Https.mm */,\\
${T}${T}${T}${T}0F0F0F0F0F000005000E1D17 /* wrap_HttpsRequest.h */,\\
${T}${T}${T}${T}0F0F0F0F0F000006000E1D17 /* wrap_HttpsRequest.cpp */,\\
${T}${T}${T}${T}0F0F0F0F0F000007000E1D17 /* wrap_Https.h */,\\
${T}${T}${T}${T}0F0F0F0F0F000008000E1D17 /* wrap_Https.cpp */,\\
${T}${T}${T});\\
${T}${T}${T}path = https;\\
${T}${T}${T}sourceTree = \"<group>\";\\
${T}${T}};
" "$PBXPROJ"

    # 6d. Add https group to modules parent group (before timer entry)
    sed -i '' "/FA0B7CB71A95902C000E1D17 \/\* timer \*\/,/i\\
${T}${T}${T}${T}0F0F0F0F0F000020000E1D17 /* https */,
" "$PBXPROJ"

    # 6e. Add source files to macOS Sources build phase (FA577AAA16C7507900860150)
    sed -i '' "/FA577AAA16C7507900860150 \/\* Sources \*\/ = {/,/files = (/{
        /files = (/a\\
${T}${T}${T}${T}0F0F0F0F0F000012000E1D17 /* HttpsRequest.cpp in Sources */,\\
${T}${T}${T}${T}0F0F0F0F0F000014000E1D17 /* Https.mm in Sources */,\\
${T}${T}${T}${T}0F0F0F0F0F000016000E1D17 /* wrap_HttpsRequest.cpp in Sources */,\\
${T}${T}${T}${T}0F0F0F0F0F000018000E1D17 /* wrap_Https.cpp in Sources */,
    }" "$PBXPROJ"
else
    log_info "project.pbxproj already patched"
fi

log_success "LÖVE source patched successfully"
