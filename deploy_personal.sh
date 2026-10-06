#!/usr/bin/env bash
# Build the personal site and publish it to users.cs.utah.edu/~shankar
# Requires: GlobalProtect VPN connected, ssh access as shankar@shell.cs.utah.edu
set -euo pipefail
cd "$(dirname "$0")"
# Rebuild if Python + jinja2 are available; otherwise use the prebuilt dist/personal
(python build.py personal || python3 build.py personal) 2>/dev/null || echo "Using prebuilt dist/personal"
HOST="${HOST:-shankar@shell.cs.utah.edu}"
STAMP=$(date +%F-%H%M)
echo "Backing up current public_html -> public_html_backup_$STAMP"
ssh "$HOST" "cp -a public_html public_html_backup_$STAMP 2>/dev/null || true"
rsync -avz --chmod=Da+rx,Fa+r dist/personal/ "$HOST:public_html/"
echo "Done: https://users.cs.utah.edu/~shankar/"
