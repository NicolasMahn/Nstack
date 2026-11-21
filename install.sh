#!/bin/sh
# Links this repo into the places Claude Code and Codex look, so both read the
# same files. Safe to run again: existing links are refreshed, and a real file
# in the way is kept as <name>.bak-<date> rather than overwritten.
set -eu

repo=$(cd "$(dirname "$0")" && pwd)

link() {
  target=$1 path=$2
  mkdir -p "$(dirname "$path")"
  if [ -e "$path" ] && [ ! -L "$path" ]; then
    mv "$path" "$path.bak-$(date +%F)"
    echo "kept old $path as $path.bak-$(date +%F)"
  fi
  ln -sfn "$target" "$path"
}

link "$repo/AGENTS.md" "$HOME/.claude/CLAUDE.md"
link "$repo/AGENTS.md" "$HOME/.codex/AGENTS.md"

for skill in "$repo"/skills/*/; do
  name=$(basename "$skill")
  link "$repo/skills/$name" "$HOME/.claude/skills/$name"
  # Codex and Cursor both read ~/.agents/skills.
  link "$repo/skills/$name" "$HOME/.agents/skills/$name"
done

# A skill deleted from this repo leaves a dead link behind. Remove only links
# that point into this repo, so skills installed from elsewhere stay untouched.
for path in "$HOME"/.claude/skills/* "$HOME"/.agents/skills/*; do
  if [ -L "$path" ] && [ ! -e "$path" ]; then
    case $(readlink "$path") in
      "$repo"/skills/*) rm "$path"; echo "removed dead link $path" ;;
    esac
  fi
done

# The repo is public. Its pre-commit hook keeps private values out of commits.
git -C "$repo" config core.hooksPath hooks

for tool in "$repo"/bin/*; do
  link "$tool" "$HOME/.local/bin/$(basename "$tool")"
done
