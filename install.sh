#!/usr/bin/env bash
# AI Updater — install for Claude Code / Codex / Cursor / Reasonix
# Run from the repo root:
#   bash install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "AI Updater — Installer"
echo "======================"
echo ""

# ----- Claude Code -----
if command -v claude &> /dev/null || [ -d "$HOME/.claude" ]; then
    echo "[Claude Code]"
    mkdir -p "$HOME/.claude/skills/ai-updater"
    mkdir -p "$HOME/.claude/commands"
    cp "$SCRIPT_DIR/SKILL.md" "$HOME/.claude/skills/ai-updater/SKILL.md"
    cp "$SCRIPT_DIR/ai_updater.py" "$HOME/.claude/skills/ai-updater/ai_updater.py"
    cp "$SCRIPT_DIR/projects.csv" "$HOME/.claude/skills/ai-updater/projects.csv"
    cp "$SCRIPT_DIR/config.yaml" "$HOME/.claude/skills/ai-updater/config.yaml"
    cp "$SCRIPT_DIR/requirements.txt" "$HOME/.claude/skills/ai-updater/requirements.txt"
    cp "$SCRIPT_DIR/.claude/commands/ai-updater.md" "$HOME/.claude/commands/ai-updater.md"
    echo "  -> ~/.claude/skills/ai-updater/"
    echo "  -> ~/.claude/commands/ai-updater.md"
    echo "  /ai-updater ready"
else
    echo "[Claude Code] skipped (not found)"
fi

echo ""

# ----- Codex -----
if command -v codex &> /dev/null || [ -d "$HOME/.codex" ]; then
    echo "[Codex]"
    mkdir -p "$HOME/.codex/skills/ai-updater"
    mkdir -p "$HOME/.codex/commands"
    cp "$SCRIPT_DIR/SKILL.md" "$HOME/.codex/skills/ai-updater/SKILL.md"
    cp "$SCRIPT_DIR/ai_updater.py" "$HOME/.codex/skills/ai-updater/ai_updater.py"
    cp "$SCRIPT_DIR/projects.csv" "$HOME/.codex/skills/ai-updater/projects.csv"
    cp "$SCRIPT_DIR/config.yaml" "$HOME/.codex/skills/ai-updater/config.yaml"
    cp "$SCRIPT_DIR/requirements.txt" "$HOME/.codex/skills/ai-updater/requirements.txt"
    cp "$SCRIPT_DIR/.codex/commands/ai-updater.md" "$HOME/.codex/commands/ai-updater.md"
    echo "  -> ~/.codex/skills/ai-updater/"
    echo "  -> ~/.codex/commands/ai-updater.md"
    echo "  /ai-updater ready for Codex"
else
    echo "[Codex] skipped (not found)"
fi

echo ""

# ----- Cursor -----
if [ -d "$HOME/.cursor" ] || [ -d "$HOME/Library/Application Support/Cursor" ]; then
    echo "[Cursor]"
    mkdir -p "$HOME/.cursor/commands"
    cp "$SCRIPT_DIR/.cursor/commands/ai-updater.md" "$HOME/.cursor/commands/ai-updater.md"
    echo "  -> ~/.cursor/commands/ai-updater.md"
    echo "  /ai-updater ready for Cursor"
else
    echo "[Cursor] skipped (not found)"
fi

echo ""

# ----- Reasonix -----
if [ -d "$SCRIPT_DIR/.reasonix" ]; then
    echo "[Reasonix]"
    mkdir -p "$SCRIPT_DIR/.reasonix/skills/ai-updater"
    cp "$SCRIPT_DIR/SKILL.md" "$SCRIPT_DIR/.reasonix/skills/ai-updater/SKILL.md"
    echo "  -> .reasonix/skills/ai-updater/SKILL.md"
    echo "  /ai-updater ready for Reasonix"
fi

echo ""
echo "Done. Now install Python dependencies:"
echo "  pip install -r $SCRIPT_DIR/requirements.txt"
echo ""
echo "Then open your AI coding tool and type: /ai-updater"
