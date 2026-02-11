#!/usr/bin/env bash
# smoke-test.sh — verify LÖVE build and Balatro compatibility

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

LOVE_BIN="$BUILD_DIR/love.app/Contents/MacOS/love"
PASSED=0
FAILED=0
SKIPPED=0

run_test() {
    local name="$1"
    shift
    echo -n "  Test: $name ... "
    if "$@"; then
        echo -e "${GREEN}PASSED${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}FAILED${NC}"
        FAILED=$((FAILED + 1))
    fi
}

skip_test() {
    local name="$1"
    local reason="$2"
    echo -e "  Test: $name ... ${YELLOW}SKIPPED${NC} ($reason)"
    SKIPPED=$((SKIPPED + 1))
}

# --- Test 1: Build artifacts exist ---
test_build_artifacts() {
    [ -x "$LOVE_BIN" ]
}

# --- Test 2: LÖVE runs (tiny inline .love) ---
test_love_runs() {
    local tmpdir
    tmpdir="$(mktemp -d)"

    # Create a minimal main.lua
    cat > "$tmpdir/main.lua" <<'LUA'
function love.load()
    print(love._version)
    love.event.quit(0)
end
LUA

    # Package as a .love file (zip)
    local love_file="$tmpdir/test.love"
    (cd "$tmpdir" && zip -q "$love_file" main.lua)

    # Run with a timeout and capture output
    local output_file="$tmpdir/output.txt"
    "$LOVE_BIN" "$love_file" > "$output_file" 2>/dev/null &
    local pid=$!

    # Wait up to 10 seconds
    local i
    for i in $(seq 1 10); do
        if ! kill -0 "$pid" 2>/dev/null; then
            break
        fi
        sleep 1
    done

    # Kill if still running
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null
        wait "$pid" 2>/dev/null || true
    else
        wait "$pid" 2>/dev/null || true
    fi

    # Check for a version string (e.g. "11.5" or "11.x")
    local result=1
    if grep -qE '^[0-9]+\.[0-9]+' "$output_file" 2>/dev/null; then
        result=0
    fi

    rm -rf "$tmpdir"
    return "$result"
}

# --- Test 3: Balatro.love exists ---
test_balatro_exists() {
    [ -f "$BALATRO_LOVE" ]
}

# Helper: launch Balatro with steam_appid.txt in a temp working dir
# Sets BALATRO_PID and BALATRO_WORKDIR for the caller.
launch_balatro() {
    BALATRO_WORKDIR="$(mktemp -d)"
    echo "$BALATRO_APP_ID" > "$BALATRO_WORKDIR/steam_appid.txt"
    (cd "$BALATRO_WORKDIR" && "$LOVE_BIN" "$BALATRO_LOVE" 2>/dev/null &)
    # Find the PID — the subshell forks, so grab by process name
    sleep 1
    BALATRO_PID="$(pgrep -f "love.app/Contents/MacOS/love" | head -1)" || true
    [ -n "$BALATRO_PID" ]
}

cleanup_balatro() {
    if [ -n "${BALATRO_PID:-}" ]; then
        kill "$BALATRO_PID" 2>/dev/null || true
        # Wait for exit
        local i
        for i in 1 2 3 4 5; do
            if ! kill -0 "$BALATRO_PID" 2>/dev/null; then
                break
            fi
            sleep 1
        done
        kill -9 "$BALATRO_PID" 2>/dev/null || true
    fi
    rm -rf "${BALATRO_WORKDIR:-}"
    BALATRO_PID=""
    BALATRO_WORKDIR=""
}

# --- Test 4: Balatro launches ---
test_balatro_launches() {
    launch_balatro || return 1
    sleep 7

    if kill -0 "$BALATRO_PID" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# --- Test 5: Clean shutdown ---
test_clean_shutdown() {
    # Assumes Balatro is still running from test 4
    if [ -z "${BALATRO_PID:-}" ] || ! kill -0 "$BALATRO_PID" 2>/dev/null; then
        return 1
    fi

    kill "$BALATRO_PID" 2>/dev/null

    # Wait up to 5 seconds for exit
    local i
    for i in 1 2 3 4 5; do
        if ! kill -0 "$BALATRO_PID" 2>/dev/null; then
            return 0
        fi
        sleep 1
    done

    return 1
}

# --- Run all tests ---
echo ""
log_info "Running smoke tests..."
echo ""

run_test "Build artifacts exist" test_build_artifacts
run_test "LÖVE runs" test_love_runs
run_test "Balatro.love exists" test_balatro_exists

# Tests 4-5 require Balatro.love
if [ ! -f "$BALATRO_LOVE" ]; then
    skip_test "Balatro launches" "Balatro.love not found"
    skip_test "Clean shutdown" "Balatro.love not found"
else
    run_test "Balatro launches" test_balatro_launches
    run_test "Clean shutdown" test_clean_shutdown
    cleanup_balatro
fi

# --- Summary ---
echo ""
TOTAL=$((PASSED + FAILED + SKIPPED))
if [ "$FAILED" -eq 0 ]; then
    if [ "$SKIPPED" -gt 0 ]; then
        log_success "$PASSED passed, $SKIPPED skipped (of $TOTAL)"
    else
        log_success "All $TOTAL tests passed"
    fi
    exit 0
else
    log_error "$FAILED failed, $PASSED passed (of $TOTAL)"
    exit 1
fi
