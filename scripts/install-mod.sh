#!/usr/bin/env bash
# install-mod.sh — copy mod Lua files to Balatro's Mods directory
# Usage: install-mod.sh [all|<mod_id>]

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

MOD_ARG="${1:-all}"
# Our custom LÖVE binary runs unfused (love Balatro.love), so the save
# directory is under LOVE/<identity>/, not the fused app's path.
BALATRO_MODS_DIR="$HOME/Library/Application Support/LOVE/Balatro/Mods"
INSTALLED=0

install_mod() {
    local mod_id="$1"
    local mod_dir="$PROJECT_ROOT/mods/$mod_id"
    local mod_conf="$mod_dir/mod.conf"

    [ -f "$mod_conf" ] || die "mod.conf not found at $mod_conf"

    source "$mod_conf"

    [ -n "${MOD_NAME:-}" ] || die "MOD_NAME not set in $mod_conf"

    local lua_dir="$mod_dir/lua"
    [ -d "$lua_dir" ] || die "Lua directory not found at $lua_dir"

    local dest="$BALATRO_MODS_DIR/$MOD_NAME"
    log_info "Installing mod '$MOD_NAME' to $dest..."
    mkdir -p "$dest"
    rsync -a "$lua_dir/" "$dest/"
    log_success "Installed mod '$MOD_NAME'"
    INSTALLED=$((INSTALLED + 1))
}

# --- Main ---
if [ "$MOD_ARG" = "all" ]; then
    if [ ! -d "$PROJECT_ROOT/mods" ]; then
        die "No mods/ directory found"
    fi
    for mod_dir in "$PROJECT_ROOT"/mods/*/; do
        [ -d "$mod_dir" ] || continue
        install_mod "$(basename "$mod_dir")"
    done
else
    install_mod "$MOD_ARG"
fi

if [ "$INSTALLED" -eq 0 ]; then
    die "No mods found to install"
fi

log_success "Installed $INSTALLED mod(s)"
