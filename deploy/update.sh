#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Запустите через sudo' >&2; exit 1; }
cd /opt/aib-etrn/repo
[[ -f site.local.json ]] || { echo 'Сначала выполните установку' >&2; exit 1; }
/opt/aib-etrn/venv/bin/python -m pip install -r requirements.txt
/opt/aib-etrn/venv/bin/python build.py --config site.local.json
nginx -t
bash deploy/publish.sh dist
install -m 644 deploy/aib-etrn-api.service /etc/systemd/system/aib-etrn-api.service
install -m 644 deploy/aib-etrn-worker.service /etc/systemd/system/aib-etrn-worker.service
systemctl daemon-reload
systemctl restart aib-etrn-api aib-etrn-worker
systemctl reload nginx
echo 'Обновлено. Проверьте /healthz и форму; параметры SMTP не изменялись.'
