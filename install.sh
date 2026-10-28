#!/usr/bin/env bash
# ==============================================================================
# Claude Code + OpenRouter Free Tier: One-Click Resilient Installer
# Author: Vikrant Rana (https://github.com/vikrant-project)
# ==============================================================================

set -e

# Terminal Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
PURPLE='\033[0;35m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo -e "${PURPLE}"
cat << "EOF"
   ___ _                 _        ___                   ___             _            
  / __| |__ _ _  _  __| |___   / _ \ _ __  ___ _ _   | _ \___ _  _ |_ ___ _ _   
 | (__| / _` | || |/ _` / -_) | (_) | '_ \/ -_) ' \  |   / _ \ || |  _/ -_) '_|  
  \___|_\__,_|\_,_|\__,_\___|  \___/| .__/\___|_||_| |_|_\___/\_,_|\__\___|_|    
                                     |_|                                         
EOF
echo -e "${CYAN}=== Claude Code + OpenRouter Free Tier (16+ Auto-Failover Models) ===${NC}\n"

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[Error] python3 is required. Please install python3 & python3-venv.${NC}"
    exit 1
fi

CLAUDE_DIR="$HOME/.claude"
BIN_DIR="$HOME/.local/bin"
mkdir -p "$CLAUDE_DIR" "$BIN_DIR"

# 2. Get API Key
API_KEY="${OPENROUTER_API_KEY}"
if [ -z "$API_KEY" ]; then
    for arg in "$@"; do
        case $arg in
            --key=*)
            API_KEY="${arg#*=}"
            shift
            ;;
        esac
    done
fi

if [ -z "$API_KEY" ]; then
    echo -e "${YELLOW}Please enter your OpenRouter API Key (press Enter to use default or set later):${NC}"
    read -r -p "OpenRouter Key (sk-or-v1-...): " input_key
    if [ -n "$input_key" ]; then
        API_KEY="$input_key"
    fi
fi

if [ -z "$API_KEY" ]; then
    echo -e "${YELLOW}[Notice] No API key entered. You can set it later using: claude-openrouter --set-key <YOUR_KEY>${NC}"
    API_KEY="sk-or-v1-YOUR_KEY_HERE"
fi

# 3. Setup Virtual Environment & Dependencies
VENV_DIR="$CLAUDE_DIR/emergent-proxy"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${CYAN}[1/5] Creating Python virtual environment in $VENV_DIR...${NC}"
    python3 -m venv "$VENV_DIR"
fi

echo -e "${CYAN}[2/5] Installing core dependencies (litellm, fastapi, uvicorn, sse-starlette)...${NC}"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet litellm fastapi uvicorn httpx sse-starlette pydantic

# 4. Generate local secret token if not exists
TOKEN_FILE="$CLAUDE_DIR/openrouter_token"
if [ ! -f "$TOKEN_FILE" ]; then
    python3 -c "import secrets; print(secrets.token_urlsafe(32))" > "$TOKEN_FILE"
    chmod 600 "$TOKEN_FILE"
fi
LOCAL_TOKEN=$(cat "$TOKEN_FILE" | tr -d '\r\n')

# 5. Write OpenRouter Configuration
echo -e "${CYAN}[3/5] Configuring OpenRouter 16-Model Auto-Failover pool...${NC}"
cat << EOF > "$CLAUDE_DIR/openrouter-config.json"
{
  "upstream": "https://openrouter.ai/api/v1",
  "openrouter_api_key": "$API_KEY",
  "local_key": "$LOCAL_TOKEN",
  "port": 4141,
  "cooldown_seconds": 60,
  "models": [
    "openrouter/free",
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3.5-lightning:free",
    "poolside/laguna-s-2.1:free",
    "poolside/laguna-xs-2.1:free",
    "dots-studio/dots-3-note-preview:free",
    "nvidia/nemotron-3.5-super-vl:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "xingchen-agi/xing4.0-29b-a4b:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "recursive/flint-v1.0:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "liquid/lfm-2.5-2.6b:free",
    "thinkingmachines/inkling:free",
    "thinkingmachines/inkling-small:free"
  ]
}
EOF
chmod 600 "$CLAUDE_DIR/openrouter-config.json"
cp -f "$CLAUDE_DIR/openrouter-config.json" "$CLAUDE_DIR/emergent-config.json" 2>/dev/null || true

# 6. Copy Bridge & Helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/src/bridge.py" ]; then
    cp -r "$SCRIPT_DIR/src" "$CLAUDE_DIR/"
fi

# Deploy standalone bridge executable
cat << 'EOF' > "$CLAUDE_DIR/openrouter_bridge.py"
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude"))
from src.bridge import run
if __name__ == "__main__":
    run()
EOF
chmod 700 "$CLAUDE_DIR/openrouter_bridge.py"
cp -f "$CLAUDE_DIR/openrouter_bridge.py" "$CLAUDE_DIR/emergent_bridge.py" 2>/dev/null || true

# 7. Configure Claude Code settings.json
echo -e "${CYAN}[4/5] Updating Claude Code settings ($CLAUDE_DIR/settings.json)...${NC}"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
python3 -c "
import json
from pathlib import Path
p = Path('$SETTINGS_FILE')
data = {}
if p.exists():
    try: data = json.loads(p.read_text())
    except: pass
if 'env' not in data: data['env'] = {}
data['env']['ANTHROPIC_BASE_URL'] = 'http://127.0.0.1:4141'
data['env']['ANTHROPIC_AUTH_TOKEN'] = '$LOCAL_TOKEN'
data['env']['ANTHROPIC_MODEL'] = 'claude-sonnet-4-6'
data['env']['ANTHROPIC_DEFAULT_SONNET_MODEL'] = 'claude-sonnet-4-6'
data['env']['ANTHROPIC_DEFAULT_OPUS_MODEL'] = 'claude-sonnet-4-6'
data['env']['ANTHROPIC_DEFAULT_HAIKU_MODEL'] = 'claude-sonnet-4-6'
data['env']['CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC'] = '1'
data['env']['DISABLE_PROMPT_CACHING'] = '1'
data['env']['API_TIMEOUT_MS'] = '660000'
p.write_text(json.dumps(data, indent=2))
"

# 8. Deploy CLI Launchers
echo -e "${CYAN}[5/5] Deploying CLI launchers into $BIN_DIR...${NC}"
if [ -f "$SCRIPT_DIR/bin/claude-openrouter" ]; then
    cp "$SCRIPT_DIR/bin/claude-openrouter" "$BIN_DIR/claude-openrouter"
    chmod +x "$BIN_DIR/claude-openrouter"
    
    # If claude isn't backed up, backup and link wrapper
    if [ ! -f "$BIN_DIR/claude-original" ] && [ -f "$BIN_DIR/claude" ]; then
        if [ ! -L "$BIN_DIR/claude" ] || [ "$(readlink "$BIN_DIR/claude")" != "$BIN_DIR/claude-openrouter" ]; then
            cp "$BIN_DIR/claude" "$BIN_DIR/claude-original" 2>/dev/null || true
        fi
    fi
    cp -f "$BIN_DIR/claude-openrouter" "$BIN_DIR/claude"
    chmod +x "$BIN_DIR/claude"
    cp -f "$BIN_DIR/claude-openrouter" "$BIN_DIR/claude-emergent" 2>/dev/null || true
fi

# Ensure PATH
if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    echo "export PATH="\$HOME/.local/bin:\$PATH"" >> "$HOME/.bashrc"
    export PATH="$BIN_DIR:$PATH"
fi

echo -e "\n${GREEN}================================================================================"
echo -e "                 ✨ SETUP COMPLETED SUCCESSFULLY! ✨                            "
echo -e "================================================================================${NC}"
echo -e "${BOLD}Your Claude Code CLI is now powered by OpenRouter Free Tier with 16+ Models!${NC}\n"
echo -e "To start coding right now:"
echo -e "  ${CYAN}claude${NC}                 (Standard interactive Claude Code session)"
echo -e "  ${CYAN}claude-openrouter --status${NC} (View real-time model pool & failover health)"
echo -e "\n${PURPLE}Happy endless coding with zero rate-limit interruptions! 🚀${NC}\n"
