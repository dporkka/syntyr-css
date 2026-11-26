#!/bin/sh
# Optional maintainer-only check. Never print or upload matching secret values.
set -eu
root=$(git rev-parse --show-toplevel)
if [ "$(git -C "$root" rev-parse --is-shallow-repository)" != false ]; then
    echo 'INCOMPLETE credential scan: fetch full history before scanning' >&2
    exit 2
fi
# Use default built-in rules, not an ambient override or inline allow comment.
unset GITLEAKS_CONFIG GITLEAKS_CONFIG_TOML
export GIT_NO_REPLACE_OBJECTS=1
if [ -e "$root/.gitleaks.toml" ]; then
    echo 'Unexpected scanner configuration; review before scanning' >&2
    exit 2
fi
# Emit merge patches against the first parent while walking all parents.
"${GITLEAKS:-gitleaks}" git --log-opts="--diff-merges=first-parent HEAD" --gitleaks-ignore-path "$root/.gitleaksignore" \
    --ignore-gitleaks-allow --redact=100 --no-banner --log-level=warn "$root"
echo 'PASS: no unreviewed Gitleaks matches in complete checked-out HEAD ancestry'
