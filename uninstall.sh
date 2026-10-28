#!/usr/bin/env bash
# Claude OpenRouter Uninstaller
set -e
echo "Uninstalling Claude OpenRouter Bridge..."
BIN_DIR="$HOME/.local/bin"
CLAUDE_DIR="$HOME/.claude"

if [ -f "$BIN_DIR/claude-original" ]; then
    mv -f "$BIN_DIR/claude-original" "$BIN_DIR/claude"
    echo "Restored original claude binary."
fi
rm -f "$BIN_DIR/claude-openrouter"
rm -f "$CLAUDE_DIR/openrouter-config.json" "$CLAUDE_DIR/openrouter_bridge.py"
echo "Uninstallation complete."
