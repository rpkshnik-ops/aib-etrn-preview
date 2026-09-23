import json
import logging
import time

from .core import clean, config, database, heartbeat, initialize
from .smtp_delivery import DeliveryError, deliver

LOG = logging.getLogger('aib.delivery')


def process_one(cfg, sender=deliver):
    now = time.time()
    heartbeat(cfg)
    with database(cfg) as db:
        db.execute('BEGIN IMMEDIATE')
        # A process may have stopped after claiming a message.
        db.execute("UPDATE leads SET state='queued' WHERE state='sending' AND updated<?", (now - 120,))
        row = db.execute("SELECT * FROM leads WHERE state='queued' AND next_attempt<=? ORDER BY created LIMIT 1", (now,)).fetchone()
        if not row:
            return False
        db.execute("UPDATE leads SET state='sending', updated=?, attempts=attempts+1 WHERE id=?", (now, row['id']))
    try:
        sender(cfg, row['id'], json.loads(row['payload']))
    except DeliveryError as error:
        attempts = row['attempts'] + 1
        state = 'failed' if attempts >= 8 or str(error) in ('smtp_authentication_failed', 'smtp_certificate_invalid', 'smtp_recipient_refused', 'smtp_tls_or_auth_not_supported') else 'queued'
        delay = min(3600, 30 * (2 ** min(attempts - 1, 7)))
        with database(cfg) as db:
            db.execute('UPDATE leads SET state=?,error=?,updated=?,next_attempt=? WHERE id=?',
                       (state, str(error), time.time(), time.time() + delay, row['id']))
        LOG.warning('delivery_failed id=%s reason=%s attempts=%s', row['id'], str(error), attempts)
    else:
        with database(cfg) as db:
            db.execute('PRAGMA secure_delete=ON')
            db.execute("UPDATE leads SET state='sent',payload=NULL,error='',updated=? WHERE id=?", (time.time(), row['id']))
        LOG.info('smtp_accepted id=%s', row['id'])
    return True


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    cfg = config()
    initialize(cfg)
    last_cleanup = 0
    while True:
        try:
            if time.time() - last_cleanup > 3600:
                expired = clean(cfg)
                if expired:
                    LOG.error('undelivered_expired count=%s', expired)
                last_cleanup = time.time()
            worked = process_one(cfg)
        except Exception as error:
            # Do not log upstream messages, contact details or request bodies.
            LOG.error('worker_error type=%s', type(error).__name__)
            worked = False
        if not worked:
            time.sleep(5)


if __name__ == '__main__':
    main()
