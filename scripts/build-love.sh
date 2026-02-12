#!/usr/bin/env bash
# build-love.sh — clone deps, copy frameworks, build LÖVE from source

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

log_info "Building LÖVE from source..."

# 1. Verify tools
command -v git >/dev/null || die "git not found"
command -v xcodebuild >/dev/null || die "xcodebuild not found"

# 2. Clone love source
if [ ! -d "$DEPS_DIR/love/.git" ]; then
    log_info "Cloning love2d/love (branch $LOVE_BRANCH)..."
    git clone --branch "$LOVE_BRANCH" --single-branch "$LOVE_REPO" "$DEPS_DIR/love"
else
    log_info "love source already present, skipping clone"
fi

# 3. Clone apple dependencies
if [ ! -d "$DEPS_DIR/love-apple-dependencies/.git" ]; then
    log_info "Cloning love-apple-dependencies (tag $LOVE_DEPS_TAG)..."
    git clone "$LOVE_DEPS_REPO" "$DEPS_DIR/love-apple-dependencies"
    git -C "$DEPS_DIR/love-apple-dependencies" checkout "$LOVE_DEPS_TAG"
else
    log_info "love-apple-dependencies already present, skipping clone"
fi

# 4. Copy macOS frameworks into the Xcode project
FRAMEWORKS_SRC="$DEPS_DIR/love-apple-dependencies/macOS/Frameworks"
FRAMEWORKS_DST="$DEPS_DIR/love/platform/xcode/macosx/Frameworks"

if [ ! -d "$FRAMEWORKS_SRC" ]; then
    die "Frameworks not found at $FRAMEWORKS_SRC"
fi

log_info "Copying macOS frameworks..."
mkdir -p "$FRAMEWORKS_DST"
rsync -a "$FRAMEWORKS_SRC/" "$FRAMEWORKS_DST/"

# 5. Apply engine patches (idempotent)
bash "$SCRIPT_DIR/patch-love.sh"

# 6. Build with xcodebuild
XCODE_PROJECT="$DEPS_DIR/love/platform/xcode/love.xcodeproj"
XCODE_BUILD_DIR="$BUILD_DIR/xcode-build"

if [ ! -d "$XCODE_PROJECT" ]; then
    die "Xcode project not found at $XCODE_PROJECT"
fi

log_info "Running xcodebuild (this may take a few minutes)..."
xcodebuild \
    -project "$XCODE_PROJECT" \
    -target love-macosx \
    -configuration Release \
    -arch arm64 \
    SYMROOT="$XCODE_BUILD_DIR" \
    2>&1 | tail -20

# 7. Copy love.app to build/
BUILT_APP="$XCODE_BUILD_DIR/Release/love.app"
if [ ! -d "$BUILT_APP" ]; then
    die "Build failed — love.app not found at $BUILT_APP"
fi

log_info "Copying love.app to build/..."
rsync -a "$BUILT_APP" "$BUILD_DIR/"

# 8. Verify binary
LOVE_BIN="$BUILD_DIR/love.app/Contents/MacOS/love"
if [ -x "$LOVE_BIN" ]; then
    log_success "Build complete: $LOVE_BIN"
else
    die "Binary not executable: $LOVE_BIN"
fi
