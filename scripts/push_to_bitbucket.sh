#!/usr/bin/env bash
# Helper: configure `bitbucket` remote and push `main` branch
# Usage: run this locally where your SSH agent / credentials are available

set -euo pipefail

REPO_URL_SSH="git@bitbucket.org:micahread/patent-miner.git"
REPO_URL_HTTPS="https://micahread-admin@bitbucket.org/micahread/patent-miner.git"

cd "$(dirname "$0")/.."

if git remote get-url bitbucket >/dev/null 2>&1; then
  echo "Remote 'bitbucket' already exists: $(git remote get-url bitbucket)"
else
  echo "Adding remote 'bitbucket' (SSH) -> $REPO_URL_SSH"
  git remote add bitbucket "$REPO_URL_SSH"
fi

echo "Fetching remote refs (will not modify local branches)"
git fetch bitbucket || true

echo "Attempting to push 'main' -> bitbucket"
if git push -u bitbucket main; then
  echo "Push succeeded (SSH)."
  exit 0
else
  echo "SSH push failed; trying HTTPS with credential prompt"
  git remote set-url bitbucket "$REPO_URL_HTTPS"
  git push -u "$REPO_URL_HTTPS" main
fi

echo "Done. If push still fails, run the following locally and paste output to me for debugging:"
echo "  git remote -v"
echo "  git ls-remote https://micahread-admin@bitbucket.org/micahread/patent-miner.git"
echo "  ssh -T git@bitbucket.org"
