#!/usr/bin/env bash
# common.sh — shared paths, config, and logging helpers

set -euo pipefail

# Paths derived from this script's location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPS_DIR="$PROJECT_ROOT/deps"
BUILD_DIR="$PROJECT_ROOT/build"

# Balatro.love location (override with BALATRO_LOVE_PATH env var)
BALATRO_LOVE="${BALATRO_LOVE_PATH:-$HOME/Library/Application Support/Steam/steamapps/common/Balatro/Balatro.app/Contents/Resources/Balatro.love}"

# LÖVE source config
LOVE_REPO="https://github.com/love2d/love.git"
LOVE_BRANCH="11.x"
LOVE_DEPS_REPO="https://github.com/love2d/love-apple-dependencies.git"
LOVE_DEPS_TAG="11.5"

# Balatro Steam App ID (needed when launching outside Steam)
BALATRO_APP_ID="2379780"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[OK]${NC} $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }

die() { log_error "$@"; exit 1; }

# Portable timeout: run_with_timeout <seconds> <command...>
# Returns the command's exit code, or 124 on timeout.
run_with_timeout() {
    local secs="$1"; shift
    "$@" &
    local pid=$!
    (sleep "$secs" && kill "$pid" 2>/dev/null) &
    local watcher=$!
    wait "$pid" 2>/dev/null
    local rc=$?
    kill "$watcher" 2>/dev/null 2>&1
    wait "$watcher" 2>/dev/null 2>&1 || true
    return "$rc"
}
