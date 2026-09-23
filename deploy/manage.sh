#!/usr/bin/env bash
# Load systemd's server environment without putting it in shell history.
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Run with sudo' >&2; exit 1; }
cd /opt/aib-etrn/repo
exec systemd-run --quiet --wait --pipe --collect \
  --uid=aib-etrn --gid=aib-etrn \
  --property=WorkingDirectory=/opt/aib-etrn/repo \
  --property=EnvironmentFile=/etc/aib-etrn.env \
  --property=UMask=0077 \
  /opt/aib-etrn/venv/bin/python -m backend.manage "$@"
