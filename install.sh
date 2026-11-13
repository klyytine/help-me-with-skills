#!/bin/sh
# Installs the help-skill into Claude's skills folder.
#
#   sh install.sh             personal install: <config>/skills/help-skill
#   sh install.sh --project   project install:  ./.claude/skills/help-skill
#
# <config> is $CLAUDE_CONFIG_DIR when set, otherwise $HOME/.claude.
# An existing copy is moved to a skills-backup folder first.
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
source_dir="$script_dir/skills/help-skill"

if [ ! -f "$source_dir/SKILL.md" ]; then
    echo "Cannot find skills/help-skill/SKILL.md next to this script." >&2
    exit 1
fi

if [ "${1:-}" = "--project" ]; then
    base="$(pwd)/.claude"
elif [ -n "${CLAUDE_CONFIG_DIR:-}" ]; then
    base="$CLAUDE_CONFIG_DIR"
else
    base="$HOME/.claude"
fi

skills_dir="$base/skills"
target="$skills_dir/help-skill"

if [ -e "$target" ]; then
    backup_dir="$base/skills-backup"
    mkdir -p "$backup_dir"
    backup="$backup_dir/help-skill-$(date +%Y%m%d-%H%M%S)"
    mv "$target" "$backup"
    echo "Existing copy moved to $backup"
fi

mkdir -p "$skills_dir"
cp -R "$source_dir" "$target"
find "$target" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true

echo "Installed help-skill to $target"

if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
    echo "Warning: Python was not found. The skill needs Python 3.9 or newer for its inventory script." >&2
fi

echo "Start a new Claude session, then try: /help-skill <your task>"
