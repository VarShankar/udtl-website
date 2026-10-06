#!/usr/bin/env bash
# Run once from Git Bash in this folder:   bash publish_to_github.sh
# Creates a fresh git repo and pushes it to github.com/VarShankar/udtl-website
set -euo pipefail
cd "$(dirname "$0")"
REPO=udtl-website
rm -rf .git                     # clear the half-made repo left by the Claude session
git init -q -b main
git add -A
git commit -q -m "Personal site and Utah Digital Twin Lab site"
if command -v gh >/dev/null 2>&1; then
  gh repo create "VarShankar/$REPO" --public --source . --push
else
  echo "Create an EMPTY public repo named $REPO at https://github.com/new (no README), then press Enter."
  read -r
  git remote add origin "https://github.com/VarShankar/$REPO.git"
  git push -u origin main
fi
echo
echo "Pushed. Next: https://github.com/VarShankar/$REPO/settings/pages"
echo "  - Source: GitHub Actions"
echo "  - Custom domain: varunshankar.com"
