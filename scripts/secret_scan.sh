#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-.}"
cd "$ROOT_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: secret scan must run inside a git repository"
  exit 2
fi

echo "Running secret scan in: $(pwd)"

if command -v gitleaks >/dev/null 2>&1; then
  echo "Using gitleaks..."
  gitleaks detect --source . --redact --no-banner --exit-code 1
  echo "PASS: no secrets detected by gitleaks"
  exit 0
fi

echo "gitleaks not found, using regex fallback scanner..."

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

git ls-files -z | \
  xargs -0 rg -n -I \
    -e '-----BEGIN (RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY-----' \
    -e 'AKIA[0-9A-Z]{16}' \
    -e 'ghp_[A-Za-z0-9]{36,}' \
    -e 'xox[baprs]-[A-Za-z0-9-]{10,}' \
    -e '(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*["'"'"'][^"'"'"']{8,}["'"'"']' \
  > "$tmp_file" || true

if [[ -s "$tmp_file" ]]; then
  echo "FAIL: potential secrets found"
  cat "$tmp_file"
  exit 1
fi

echo "PASS: no obvious hardcoded secrets detected (fallback scan)"
