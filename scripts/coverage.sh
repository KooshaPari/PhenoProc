#!/usr/bin/env bash
# scripts/coverage.sh — Run cargo-llvm-cov with auto-detected LLVM tools.
#
# On systems where `cargo llvm-cov` cannot find the `llvm-tools-preview`
# rustup component by its old canonical name, set LLVM_COV and
# LLVM_PROFDATA explicitly to the binaries shipped under rustup's
# toolchain lib directory.
#
# Usage:
#   ./scripts/coverage.sh                       # default: --fail-under-lines 85
#   ./scripts/coverage.sh --fail-under-lines 90 # custom threshold
#   ./scripts/coverage.sh --workspace --html    # any extra cargo-llvm-cov args
set -euo pipefail

# Detect rustup-managed LLVM tools.
RUSTUP_TOOLCHAIN="${RUSTUP_TOOLCHAIN:-}"
if [[ -z "$RUSTUP_TOOLCHAIN" ]] && command -v rustup >/dev/null 2>&1; then
    RUSTUP_TOOLCHAIN="$(rustup show active-toolchain 2>/dev/null | awk '{print $1}')"
fi

if [[ -n "$RUSTUP_TOOLCHAIN" ]]; then
    TOOLCHAIN_BIN_DIR="$HOME/.rustup/toolchains/${RUSTUP_TOOLCHAIN}/lib/rustlib/$(rustup show active-toolchain 2>/dev/null | awk '{print $2}' | tr -d '-' || echo '')/bin"
    # The path layout above is target-specific and brittle; fall back to a
    # direct lookup which is the actual convention rustup uses.
    BIN_DIR="$(find "$HOME/.rustup/toolchains/${RUSTUP_TOOLCHAIN}/lib/rustlib" -maxdepth 3 -type d -name bin 2>/dev/null | head -1 || true)"
    if [[ -n "${BIN_DIR:-}" ]]; then
        : "${LLVM_COV:=$BIN_DIR/llvm-cov}"
        : "${LLVM_PROFDATA:=$BIN_DIR/llvm-profdata}"
        export LLVM_COV LLVM_PROFDATA
    fi
fi

# Default args: workspace, line-coverage, SSOT threshold = 85.
ARGS=("$@")
if [[ $# -eq 0 ]]; then
    ARGS=(--workspace --fail-under-lines 85)
fi

exec cargo llvm-cov "${ARGS[@]}"
