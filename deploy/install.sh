#!/usr/bin/env bash
# Supported automatic installation: Ubuntu 24.04+ / Debian 12+, systemd.
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Запустите: sudo bash deploy/install.sh' >&2; exit 1; }
project=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
[[ "$project" == /opt/aib-etrn/repo ]] || { echo 'Склонируйте проект в /opt/aib-etrn/repo, как указано в README.' >&2; exit 1; }
cd "$project"
if [[ ${1:-} == --smtp-only ]]; then
  exec /opt/aib-etrn/venv/bin/python deploy/configure.py --smtp-only
fi
[[ $# -eq 0 ]] || { echo 'Допустимый параметр: --smtp-only' >&2; exit 1; }
[[ -f /etc/os-release ]] || { echo 'Требуется Linux с /etc/os-release' >&2; exit 1; }
. /etc/os-release
case " $ID ${ID_LIKE:-} " in
  *ubuntu*|*debian*) ;;
  *) echo 'Автоустановка поддерживает Ubuntu/Debian. Для других Linux смотрите README.' >&2; exit 1 ;;
esac
command -v systemctl >/dev/null
apt-get update
apt-get install -y python3 python3-venv nginx ca-certificates certbot python3-certbot-nginx
python3 -c 'import sys; assert sys.version_info >= (3, 11), "Требуется Python 3.11+"'
if ! id aib-etrn >/dev/null 2>&1; then
  useradd --system --home-dir /var/lib/aib-etrn --shell /usr/sbin/nologin aib-etrn
fi
install -d -o aib-etrn -g aib-etrn -m 700 /var/lib/aib-etrn
install -d -o root -g aib-etrn -m 750 /etc/aib-etrn
python3 -m venv /opt/aib-etrn/venv
/opt/aib-etrn/venv/bin/python -m pip install -r requirements.txt
exec /opt/aib-etrn/venv/bin/python deploy/configure.py
