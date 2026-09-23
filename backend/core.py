import hashlib
import hmac
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit
from .smtp_delivery import validate_smtp


def config():
    config_path = os.environ.get('AIB_CONFIG')
    stored = json.loads(Path(config_path).read_text(encoding='utf-8')) if config_path else {}
    origin = stored.get('origin', os.environ.get('SITE_ORIGIN', '')).rstrip('/')
    parsed = urlsplit(origin)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.path or parsed.query or parsed.fragment
            or parsed.username or parsed.password or 'YOUR-DOMAIN' in origin.upper()):
        raise ValueError('SITE_ORIGIN must be the real HTTPS origin without a path')
    secret = stored.get('secret', os.environ.get('HASH_SECRET', ''))
    if len(secret) < 32 or 'REPLACE' in secret.upper():
        raise ValueError('Set a random HASH_SECRET of at least 32 characters')
    return {
        'origin': origin,
        'secret': secret,
        'database': stored.get('database', os.environ.get('DATABASE_PATH', '/var/lib/aib-etrn/leads.sqlite3')),
        'recipient': 'etrn@corp.aib.ru',
        'rate_limit': 5,
        'rate_window': 600,
        'retention': 7 * 86400,
        'smtp': validate_smtp(stored.get('smtp', {
            'host': os.environ.get('SMTP_HOST', ''),
            'port': int(os.environ.get('SMTP_PORT', '587')),
            'security': os.environ.get('SMTP_SECURITY', 'starttls'),
            'username': os.environ.get('SMTP_USERNAME', ''),
            'password': os.environ.get('SMTP_PASSWORD', ''),
            'from_email': os.environ.get('SMTP_FROM', 'etrn@corp.aib.ru'),
        })),
    }


@contextmanager
def database(cfg):
    connection = sqlite3.connect(cfg['database'], timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize(cfg):
    Path(cfg['database']).parent.mkdir(parents=True, exist_ok=True)
    with database(cfg) as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA secure_delete=ON')
        db.executescript('''
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, payload TEXT,
                state TEXT NOT NULL DEFAULT 'queued', created REAL NOT NULL,
                updated REAL NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                next_attempt REAL NOT NULL, error TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS due_leads ON leads(state,next_attempt);
            CREATE INDEX IF NOT EXISTS fingerprints ON leads(fingerprint,created);
            CREATE TABLE IF NOT EXISTS rate_limits (ip TEXT NOT NULL, at REAL NOT NULL);
            CREATE INDEX IF NOT EXISTS rates ON rate_limits(ip,at);
            CREATE TABLE IF NOT EXISTS runtime (key TEXT PRIMARY KEY,value REAL NOT NULL);
        ''')


def digest(cfg, text):
    return hmac.new(cfg['secret'].encode(), text.encode(), hashlib.sha256).hexdigest()


def heartbeat(cfg):
    with database(cfg) as db:
        db.execute("INSERT OR REPLACE INTO runtime VALUES ('heartbeat', ?)", (time.time(),))


def stats(cfg):
    now = time.time()
    with database(cfg) as db:
        counts = {row['state']: row['n'] for row in db.execute('SELECT state, count(*) n FROM leads GROUP BY state')}
        beat = db.execute("SELECT value FROM runtime WHERE key='heartbeat'").fetchone()
        oldest = db.execute("SELECT min(created) FROM leads WHERE state IN ('queued','sending')").fetchone()[0]
    return {
        'counts': counts,
        'worker_alive': bool(beat and now - beat[0] < 90),
        'oldest_pending_seconds': int(now - oldest) if oldest else 0,
    }


def clean(cfg):
    now = time.time()
    with database(cfg) as db:
        db.execute('PRAGMA secure_delete=ON')
        db.execute('DELETE FROM rate_limits WHERE at < ?', (now - cfg['rate_window'],))
        expired = db.execute("SELECT count(*) FROM leads WHERE created < ? AND state != 'sent'", (now - cfg['retention'],)).fetchone()[0]
        db.execute('DELETE FROM leads WHERE created < ?', (now - cfg['retention'],))
    # Best-effort truncation of the WAL: backups still have their own retention.
    with database(cfg) as db:
        db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    return expired


def fingerprint(cfg, payload):
    fields = {key: payload[key] for key in ('contact_type', 'contact', 'name', 'company', 'problem')}
    return digest(cfg, json.dumps(fields, ensure_ascii=False, sort_keys=True))
