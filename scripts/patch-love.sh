#!/usr/bin/env bash
# patch-love.sh — apply Open Heart engine mods to deps/love/ (idempotent)
# Usage: patch-love.sh <module1> [module2] ...
# Each module must have engine/<name>/module.conf

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

if [ $# -eq 0 ]; then
    die "Usage: patch-love.sh <module1> [module2] ..."
fi

LOVE_SRC="$DEPS_DIR/love/src"
LOVE_MODULES="$LOVE_SRC/modules"
PBXPROJ="$DEPS_DIR/love/platform/xcode/liblove.xcodeproj/project.pbxproj"

# macOS sed doesn't interpret \t in replacement text, so use a literal tab
T="$(printf '\t')"

# --- Validation ---
validate_module() {
    local mod_dir="$1"
    local conf="$mod_dir/module.conf"

    [ -f "$conf" ] || die "module.conf not found at $conf"

    # Source it in a subshell first to validate fields
    (
        source "$conf"
        for field in MODULE_NAME MODULE_ENUM MODULE_DEFINE MODULE_LUAOPEN MODULE_FILES MODULE_SOURCES; do
            eval "val=\${$field:-}"
            [ -n "$val" ] || { echo "Missing required field: $field in $conf" >&2; exit 1; }
        done
        # Verify every file in MODULE_FILES exists on disk
        for f in $MODULE_FILES; do
            [ -f "$mod_dir/$f" ] || { echo "File listed in MODULE_FILES not found: $mod_dir/$f" >&2; exit 1; }
        done
        # Verify MODULE_SOURCES is a subset of MODULE_FILES
        for s in $MODULE_SOURCES; do
            echo " $MODULE_FILES " | grep -q " $s " || { echo "MODULE_SOURCES file '$s' not in MODULE_FILES in $conf" >&2; exit 1; }
        done
    ) || die "Validation failed for $conf"
}

# --- Patch functions ---

patch_copy_sources() {
    local mod_name="$1" mod_dir="$2"
    local dest="$LOVE_MODULES/$mod_name"
    log_info "[$mod_name] Copying source files..."
    mkdir -p "$dest"
    rsync -a --exclude='module.conf' "$mod_dir/" "$dest/"
}

patch_module_h() {
    local mod_name="$1" mod_enum="$2"
    local module_h="$LOVE_SRC/common/Module.h"
    if ! grep -q "$mod_enum" "$module_h"; then
        log_info "[$mod_name] Patching Module.h..."
        sed -i '' "s/${T}${T}M_MAX_ENUM/${T}${T}${mod_enum},\\
${T}${T}M_MAX_ENUM/" "$module_h"
    else
        log_info "[$mod_name] Module.h already patched"
    fi
}

patch_config_h() {
    local mod_name="$1" mod_define="$2"
    local config_h="$LOVE_SRC/common/config.h"
    if ! grep -q "$mod_define" "$config_h"; then
        log_info "[$mod_name] Patching config.h..."
        sed -i '' "/#${T}define LOVE_ENABLE_WINDOW/a\\
\\
#${T}define ${mod_define}
" "$config_h"
    else
        log_info "[$mod_name] config.h already patched"
    fi
}

patch_love_cpp() {
    local mod_name="$1" mod_define="$2" mod_luaopen="$3"
    local love_cpp="$LOVE_MODULES/love/love.cpp"
    if ! grep -q "$mod_luaopen" "$love_cpp"; then
        log_info "[$mod_name] Patching love.cpp..."
        # Insert extern declaration before luaopen_love_nogame
        sed -i '' "/extern int luaopen_love_nogame/i\\
#if defined(${mod_define})\\
${T}extern int ${mod_luaopen}(lua_State*);\\
#endif
" "$love_cpp"
        # Insert module table entry before { "love.nogame"
        sed -i '' "/{ \"love.nogame\"/i\\
#if defined(${mod_define})\\
${T}{ \"love.${mod_name}\", ${mod_luaopen} },\\
#endif
" "$love_cpp"
    else
        log_info "[$mod_name] love.cpp already patched"
    fi
}

patch_boot_lua() {
    local mod_name="$1"
    local boot_lua="$LOVE_MODULES/love/boot.lua"
    if ! grep -q "\"${mod_name}\"" "$boot_lua"; then
        log_info "[$mod_name] Patching boot.lua..."
        # Add to module load list (after "physics")
        sed -i '' "/\"physics\",/a\\
${T}${T}\"${mod_name}\",
" "$boot_lua"
        # Add to default config (after video = true)
        sed -i '' "/video = true,/a\\
${T}${T}${T}${mod_name} = true,
" "$boot_lua"
    else
        log_info "[$mod_name] boot.lua already patched"
    fi
}

patch_pbxproj() {
    local mod_name="$1" mod_files="$2" mod_sources="$3"

    # Check if already patched using the group ID for this module
    local group_id
    group_id="$(xcode_id "$mod_name" "group" "$mod_name")"
    if grep -q "$group_id" "$PBXPROJ"; then
        log_info "[$mod_name] project.pbxproj already patched"
        return
    fi

    log_info "[$mod_name] Patching project.pbxproj..."

    # --- PBXBuildFile entries (only for source files) ---
    local buildfile_lines=""
    for src in $mod_sources; do
        local bf_id
        bf_id="$(xcode_id "$mod_name" "buildfile" "$src")"
        local fr_id
        fr_id="$(xcode_id "$mod_name" "fileref" "$src")"
        buildfile_lines="${buildfile_lines}\\
${T}${T}${bf_id} /* ${src} in Sources */ = {isa = PBXBuildFile; fileRef = ${fr_id} /* ${src} */; };"
    done
    sed -i '' "/\/\* Begin PBXBuildFile section \*\//a\\
${buildfile_lines}
" "$PBXPROJ"

    # --- PBXFileReference entries (all files) ---
    local fileref_lines=""
    for f in $mod_files; do
        local fr_id
        fr_id="$(xcode_id "$mod_name" "fileref" "$f")"
        local ftype
        ftype="$(xcode_filetype "$f")"
        fileref_lines="${fileref_lines}\\
${T}${T}${fr_id} /* ${f} */ = {isa = PBXFileReference; fileEncoding = 4; lastKnownFileType = ${ftype}; path = ${f}; sourceTree = \"<group>\"; };"
    done
    sed -i '' "/\/\* Begin PBXFileReference section \*\//a\\
${fileref_lines}
" "$PBXPROJ"

    # --- PBXGroup for this module (before the timer group) ---
    local children_lines=""
    for f in $mod_files; do
        local fr_id
        fr_id="$(xcode_id "$mod_name" "fileref" "$f")"
        children_lines="${children_lines}\\
${T}${T}${T}${T}${fr_id} /* ${f} */,"
    done
    sed -i '' "/FA0B7CB71A95902C000E1D17 \/\* timer \*\/ = {/i\\
${T}${T}${group_id} /* ${mod_name} */ = {\\
${T}${T}${T}isa = PBXGroup;\\
${T}${T}${T}children = (${children_lines}\\
${T}${T}${T});\\
${T}${T}${T}path = ${mod_name};\\
${T}${T}${T}sourceTree = \"<group>\";\\
${T}${T}};
" "$PBXPROJ"

    # --- Add group to modules parent group (before timer entry) ---
    sed -i '' "/FA0B7CB71A95902C000E1D17 \/\* timer \*\/,/i\\
${T}${T}${T}${T}${group_id} /* ${mod_name} */,
" "$PBXPROJ"

    # --- Add source files to macOS Sources build phase (FA577AAA16C7507900860150) ---
    local sources_lines=""
    for src in $mod_sources; do
        local bf_id
        bf_id="$(xcode_id "$mod_name" "buildfile" "$src")"
        sources_lines="${sources_lines}\\
${T}${T}${T}${T}${bf_id} /* ${src} in Sources */,"
    done
    sed -i '' "/FA577AAA16C7507900860150 \/\* Sources \*\/ = {/,/files = (/{
        /files = (/a\\
${sources_lines}
    }" "$PBXPROJ"
}

patch_mod_loader() {
    local boot_lua="$LOVE_MODULES/love/boot.lua"
    if grep -q "\[Open Heart\]" "$boot_lua"; then
        log_info "[mod-loader] boot.lua mod loader already patched"
        return
    fi
    log_info "[mod-loader] Injecting mod loader into boot.lua..."

    local snippet
    snippet="$(mktemp)"
    cat > "$snippet" << 'MODLOADER'
-- [Open Heart] Mod loader — scan save directory for mods
local _oh_lfs = love.filesystem
if _oh_lfs.getInfo("Mods") then
    for _, _oh_dir in ipairs(_oh_lfs.getDirectoryItems("Mods")) do
        local _oh_entry = "Mods/" .. _oh_dir .. "/" .. _oh_dir .. ".lua"
        if _oh_lfs.getInfo(_oh_entry) then
            local _oh_ok, _oh_err = pcall(function() require("Mods." .. _oh_dir .. "." .. _oh_dir) end)
            if not _oh_ok then print("[Open Heart] Failed to load mod " .. _oh_dir .. ": " .. tostring(_oh_err)) end
        end
    end
end
MODLOADER
    sed -i '' '/require("main")/r '"$snippet" "$boot_lua"
    rm -f "$snippet"
}

# --- Main loop ---
log_info "Patching LÖVE source with engine mods: $*"

for mod_name in "$@"; do
    mod_dir="$PROJECT_ROOT/engine/$mod_name"
    [ -d "$mod_dir" ] || die "Engine module directory not found: $mod_dir"

    validate_module "$mod_dir"

    # Source the manifest
    source "$mod_dir/module.conf"

    patch_copy_sources "$mod_name" "$mod_dir"
    patch_module_h "$mod_name" "$MODULE_ENUM"
    patch_config_h "$mod_name" "$MODULE_DEFINE"
    patch_love_cpp "$mod_name" "$MODULE_DEFINE" "$MODULE_LUAOPEN"
    patch_boot_lua "$mod_name"
    patch_pbxproj "$mod_name" "$MODULE_FILES" "$MODULE_SOURCES"
done

# Inject mod loader (runs once, idempotent)
patch_mod_loader

log_success "LÖVE source patched successfully"
