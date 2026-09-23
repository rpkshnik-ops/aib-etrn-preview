"""Local-only queue inspection. Never prints applicant contact or problem fields."""
import argparse
import json
import time

from .core import config, database, initialize, stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('status', 'retry-failed', 'backup', 'smtp-test'))
    parser.add_argument('--output', help='New SQLite backup path; keep outside the web root')
    args = parser.parse_args()
    cfg = config()
    initialize(cfg)
    if args.action == 'smtp-test':
        from .smtp_delivery import DeliveryError, deliver
        from uuid import uuid4
        try:
            deliver(cfg, str(uuid4()), {
                'contact_type': 'email', 'contact': cfg['recipient'], 'name': 'Техническая проверка',
                'company': 'Компания АиБ', 'problem': 'Проверка настройки SMTP. Ответ не требуется.',
                'page_url': cfg['origin'] + '/',
            })
        except DeliveryError as error:
            print('SMTP test failed: ' + str(error))
            return 1
        print('SMTP accepted the test message. Confirm receipt in the mailbox.')
        return 0
    if args.action == 'status':
        state = stats(cfg)
        print(json.dumps(state, indent=2))
        with database(cfg) as db:
            for row in db.execute("SELECT id,state,attempts,error FROM leads WHERE state='failed' ORDER BY created LIMIT 20"):
                print(json.dumps(dict(row)))
        return 0 if state['worker_alive'] and not state['counts'].get('failed', 0) and state['oldest_pending_seconds'] < 600 else 1
    if args.action == 'retry-failed':
        with database(cfg) as db:
            count = db.execute("UPDATE leads SET state='queued',attempts=0,next_attempt=?,error='' WHERE state='failed'", (time.time(),)).rowcount
        print(f'Requeued: {count}')
    else:
        import sqlite3
        from pathlib import Path
        if not args.output:
            parser.error('--output is required')
        target = Path(args.output)
        if target.exists():
            parser.error('Backup target already exists')
        with database(cfg) as db, sqlite3.connect(target) as backup:
            db.backup(backup)
        target.chmod(0o600)
        print('Backup created')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
