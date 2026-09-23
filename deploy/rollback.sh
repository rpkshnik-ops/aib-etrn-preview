#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 && $# -eq 1 ]] || { echo 'sudo bash deploy/rollback.sh /srv/aib-etrn/releases/RELEASE' >&2; exit 1; }
target=$(realpath "$1")
[[ "$target" == /srv/aib-etrn/releases/* && -s "$target/index.html" ]] || { echo 'Invalid release directory' >&2; exit 1; }
[[ -L /srv/aib-etrn/current ]] || { echo 'Current must be a symbolic link' >&2; exit 1; }
link="/srv/aib-etrn/rollback-$(date +%s)-$$"
ln -s "$target" "$link"
mv -Tf "$link" /srv/aib-etrn/current
echo "Restored static release: $target"
