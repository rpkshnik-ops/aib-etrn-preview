"""Interactive Linux installer. Credentials never appear in command arguments or output."""
import argparse
import getpass
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import time
import warnings
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.smtp_delivery import DeliveryError, deliver, validate_smtp
from src.deployment import settings

CONFIG_PATH = Path('/etc/aib-etrn/config.json')


def ask(label, default=''):
    suffix = f' [{default}]' if default else ''
    return input(label + suffix + ': ').strip() or default


def yes(label, default=False):
    while True:
        answer = ask(label + ' (да/нет)', 'да' if default else 'нет').lower()
        if answer in ('да', 'д', 'yes', 'y'):
            return True
        if answer in ('нет', 'н', 'no', 'n'):
            return False
        print('Введите да или нет.')


def domain_name(value):
    value = value.encode('idna').decode('ascii').lower()
    if (len(value) > 253 or 'your-domain' in value or
            not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}', value)):
        raise ValueError('Введите домен без https:// и без пути, например etrn.company.ru')
    return value


def collect_smtp(previous=None):
    old = previous or {}
    while True:
        try:
            host = ask('Адрес SMTP-сервера', old.get('host', ''))
            security = ask('TLS: starttls (обычно 587) или ssl (обычно 465)', old.get('security', 'starttls')).lower()
            if security not in ('starttls', 'ssl'):
                raise ValueError('Укажите starttls или ssl')
            default_port = old.get('port', 587) if security == old.get('security') else (465 if security == 'ssl' else 587)
            port = int(ask('Порт SMTP', str(default_port)))
            username = ask('Логин SMTP (введите - для реле без авторизации)', old.get('username') or 'etrn@corp.aib.ru')
            username = '' if username == '-' else username
            password = ''
            if username:
                keep = username == old.get('username') and bool(old.get('password'))
                prompt = 'Пароль SMTP (Enter — сохранить прежний): ' if keep else 'Пароль SMTP (ввод скрыт): '
                with warnings.catch_warnings():
                    warnings.simplefilter('error', getpass.GetPassWarning)
                    password = getpass.getpass(prompt)
                if not password and keep:
                    password = old['password']
            sender = ask('Email отправителя (разрешённый SMTP-сервером)', old.get('from_email', 'etrn@corp.aib.ru'))
            return validate_smtp({'host': host, 'port': port, 'security': security,
                                  'username': username, 'password': password, 'from_email': sender})
        except (ValueError, UnicodeError):
            print('Некорректные параметры. Проверьте адрес, порт, режим TLS, логин и email; повторите ввод.')


def collect_metrica(previous=''):
    action = 'сохранить прежний ID' if previous else 'пропустить'
    while True:
        value = ask(f'ID счётчика Яндекс Метрики (необязательно; Enter — {action}; - — отключить)', previous)
        if value == '-':
            return ''
        try:
            return settings({'metrica_id': value})['metrica_id']
        except ValueError:
            print('Введите только цифровой ID счётчика (5–12 цифр), без HTML-кода и ссылок, либо пропустите настройку.')


def report_metrica(site):
    if not site['metrica_id']:
        print('Яндекс Метрика отключена: сторонний скрипт аналитики не загружается.')
    elif site['mode'] != 'production':
        print('ID Метрики сохранён. В preview/staging аналитика отключена; счётчик подключится после перехода в production.')
    else:
        print('ID Метрики сохранён для production-сборки: ' + site['metrica_id'])


def configure_analytics(site_path):
    site = settings(json.loads(site_path.read_text(encoding='utf-8')))
    site['metrica_id'] = collect_metrica(site['metrica_id'])
    site_path.write_text(json.dumps(site, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    run(sys.executable, 'build.py', '--config', site_path)
    run('bash', 'deploy/publish.sh', ROOT / 'dist')
    report_metrica(site)
    print('Настройки аналитики обновлены. SMTP и очередь заявок не изменялись.')


def write_private_json(path, values, gid=None):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix='.aib-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            if os.name == 'posix':
                os.fchmod(stream.fileno(), 0o640)
                if gid is not None:
                    os.fchown(stream.fileno(), 0, gid)
            json.dump(values, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def run(*args):
    subprocess.run([str(arg) for arg in args], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description='Настройка Linux-сервера, SMTP и необязательной аналитики')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--smtp-only', action='store_true', help='Изменить только SMTP и перезапустить обработчики')
    mode.add_argument('--analytics-only', action='store_true', help='Изменить только Яндекс Метрику и пересобрать сайт')
    args = parser.parse_args()
    if sys.platform != 'linux' or os.geteuid() != 0:
        parser.error('Запустите установщик на Linux через sudo')
    if ROOT != Path('/opt/aib-etrn/repo'):
        parser.error('Проект должен находиться в /opt/aib-etrn/repo')
    if not sys.stdin.isatty():
        parser.error('Нужен интерактивный терминал для настройки (пароль SMTP вводится скрыто)')
    site_path = ROOT / 'site.local.json'
    if args.analytics_only:
        if not site_path.exists() or not CONFIG_PATH.exists():
            parser.error('Сначала выполните полную установку')
        configure_analytics(site_path)
        return 0
    import grp
    import shutil
    old = json.loads(CONFIG_PATH.read_text(encoding='utf-8')) if CONFIG_PATH.exists() else {}
    if args.smtp_only and not old:
        parser.error('Сначала выполните полную установку')
    gid = grp.getgrnam('aib-etrn').gr_gid
    print('Настройка лендинга «Компания АиБ». Получатель заявок: etrn@corp.aib.ru')
    if old:
        domain = old['origin'].split('://', 1)[1]
        print('Существующий домен: ' + domain)
    else:
        while True:
            try:
                domain = domain_name(ask('Домен сайта'))
                break
            except (ValueError, UnicodeError) as error:
                print(str(error))
    smtp = collect_smtp(old.get('smtp'))
    cfg = dict(old, origin='https://' + domain,
               secret=old.get('secret') or secrets.token_hex(32),
               database=old.get('database', '/var/lib/aib-etrn/leads.sqlite3'),
               recipient='etrn@corp.aib.ru', smtp=smtp)
    if yes('Отправить техническое проверочное письмо на etrn@corp.aib.ru', True):
        try:
            deliver(cfg, str(uuid4()), {'contact_type': 'email', 'contact': cfg['recipient'],
                    'name': 'Техническая проверка', 'company': 'Компания АиБ',
                    'problem': 'Проверка установки SMTP. Ответ на письмо не требуется.',
                    'page_url': cfg['origin'] + '/'})
            print('SMTP-сервер принял письмо. Проверьте поступление в почтовом ящике.')
        except DeliveryError as error:
            print('Проверка SMTP не пройдена: ' + str(error))
            print('Прежние настройки сохранены. Исправьте параметры и запустите установщик ещё раз.')
            return 1
    write_private_json(CONFIG_PATH, cfg, gid)
    env_path = Path('/etc/aib-etrn.env')
    env_path.write_text('AIB_CONFIG=/etc/aib-etrn/config.json\nPYTHONUNBUFFERED=1\n', encoding='utf-8')
    os.chown(env_path, 0, gid)
    env_path.chmod(0o640)
    if args.smtp_only:
        run('systemctl', 'restart', 'aib-etrn-api', 'aib-etrn-worker')
        print('SMTP обновлён. Неотправленные заявки: sudo bash deploy/manage.sh retry-failed')
        return 0
    site = json.loads(site_path.read_text(encoding='utf-8')) if site_path.exists() else {
        'mode': 'staging', 'site_url': cfg['origin'], 'privacy_url': '', 'consent_url': '',
        'offer_url': cfg['origin'] + '/assets/documents/offer.pdf',
        'delivery_confirmed': False, 'metrica_id': '',
    }
    site['privacy_url'] = ask('Ссылка HTTPS на политику обработки данных (можно заполнить позже)', site.get('privacy_url', ''))
    site['consent_url'] = ask('Ссылка HTTPS на текст согласия (можно заполнить позже)', site.get('consent_url', ''))
    site['metrica_id'] = collect_metrica(site.get('metrica_id', ''))
    site = settings(site)
    site_path.write_text(json.dumps(site, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report_metrica(site)
    run(sys.executable, 'build.py', '--config', site_path)
    run('bash', 'deploy/publish.sh', ROOT / 'dist')
    for service in ('aib-etrn-api.service', 'aib-etrn-worker.service'):
        shutil.copyfile(ROOT / 'deploy' / service, Path('/etc/systemd/system') / service)
    run('systemctl', 'daemon-reload')
    run('systemctl', 'enable', 'aib-etrn-api', 'aib-etrn-worker')
    run('systemctl', 'restart', 'aib-etrn-api', 'aib-etrn-worker')
    nginx = Path('/etc/nginx/sites-available/aib-etrn')
    if not nginx.exists():
        run(sys.executable, 'deploy/render_nginx.py', '--domain', domain, '--output', nginx)
    enabled = Path('/etc/nginx/sites-enabled/aib-etrn')
    if not enabled.exists():
        enabled.symlink_to(nginx)
    run('nginx', '-t')
    run('systemctl', 'enable', '--now', 'nginx')
    run('systemctl', 'reload', 'nginx')
    if yes('DNS домена уже направлен на сервер. Выпустить HTTPS через Let’s Encrypt и принять условия сервиса', True):
        run('certbot', '--nginx', '--non-interactive', '--agree-tos', '--redirect',
            '--email', cfg['recipient'], '-d', domain)
    else:
        print('После настройки DNS выполните: sudo certbot --nginx --redirect -d ' + domain)
        print('Для рабочей отправки формы откройте сайт через HTTPS.')
    print('Установлено: ' + cfg['origin'])
    print('Проверьте /healthz и реальную заявку. Включение индексации описано в README.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, EOFError):
        raise SystemExit('Установка прервана пользователем.')
    except subprocess.CalledProcessError:
        raise SystemExit('Системная команда завершилась ошибкой; устраните причину выше и повторите установку.')
