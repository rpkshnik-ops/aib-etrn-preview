import json
import re
import sqlite3
import time

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from .core import config, database, digest, fingerprint, initialize, stats


def validated(data):
    def field(key, limit, required=False):
        value = data.get(key, '')
        if not isinstance(value, str) or len(value) > limit or '\x00' in value:
            raise ValueError('Некорректное поле: ' + key)
        value = value.strip()
        if required and not value:
            raise ValueError('Заполните поле: ' + key)
        return value
    if field('_honey', 200):
        raise ValueError('Не удалось принять заявку')
    identifier = field('request_id', 80, True)
    if not re.fullmatch(r'[a-zA-Z0-9-]{16,80}', identifier):
        raise ValueError('Некорректный идентификатор заявки')
    kind = field('contact_type', 10, True)
    if kind not in ('phone', 'email'):
        raise ValueError('Выберите способ связи')
    contact = field(kind, 254, True)
    if kind == 'email':
        contact = contact.lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', contact):
            raise ValueError('Укажите корректный email')
    else:
        if not re.fullmatch(r'[+\d() .-]+', contact):
            raise ValueError('Укажите корректный телефон')
        contact = re.sub(r'\D', '', contact)
        if not 10 <= len(contact) <= 15:
            raise ValueError('Укажите корректный телефон')
    problem = field('problem', 1500, True)
    if len(problem) < 20:
        raise ValueError('Опишите проблему хотя бы в 20 символах')
    if field('consent', 10) != 'true':
        raise ValueError('Подтвердите согласие')
    return identifier, {
        'contact_type': kind, 'contact': contact, 'problem': problem,
        'name': field('name', 80), 'company': field('company', 120),
        'consent': True,
    }


def create_app(overrides=None):
    cfg = overrides or config()
    initialize(cfg)
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=16384, MAX_FORM_PARTS=30, MAX_FORM_MEMORY_SIZE=16384)

    @app.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(success=False, message='Запрос не может быть обработан'), error.code

    @app.errorhandler(sqlite3.Error)
    @app.errorhandler(OSError)
    def storage_error(error):
        app.logger.error('storage_error type=%s', type(error).__name__)
        return jsonify(success=False, message='Обработчик временно недоступен'), 503

    @app.get('/healthz')
    def health():
        state = stats(cfg)
        healthy = state['worker_alive'] and state['oldest_pending_seconds'] < 600 and not state['counts'].get('failed', 0)
        # Counts and identifiers are available only to the server-side CLI.
        return jsonify(status='ok' if healthy else 'degraded'), 200 if healthy else 503

    @app.post('/api/leads')
    def lead():
        if request.headers.get('Origin') != cfg['origin']:
            return jsonify(success=False, message='Недопустимый источник'), 403
        data = request.get_json(silent=True) if request.is_json else request.form
        if not hasattr(data, 'get') or request.files:
            return jsonify(success=False, message='Некорректный запрос'), 400
        try:
            identifier, payload = validated(data)
        except ValueError as error:
            return jsonify(success=False, message=str(error)), 400
        now = time.time()
        signature = fingerprint(cfg, payload)
        ip = digest(cfg, request.headers.get('X-Real-IP') or request.remote_addr or 'unknown')
        with database(cfg) as db:
            db.execute('BEGIN IMMEDIATE')
            existing = db.execute('SELECT fingerprint FROM leads WHERE id=?', (identifier,)).fetchone()
            if existing:
                if existing['fingerprint'] != signature:
                    return jsonify(success=False, message='Идентификатор уже использован'), 409
                return jsonify(success=True, request_id=identifier), 200
            duplicate = db.execute('SELECT id FROM leads WHERE fingerprint=? AND created>?', (signature, now - 600)).fetchone()
            if duplicate:
                return jsonify(success=True, request_id=duplicate['id']), 200
            beat = db.execute("SELECT value FROM runtime WHERE key='heartbeat'").fetchone()
            if not beat or now - beat[0] >= 90:
                return jsonify(success=False, message='Обработчик временно недоступен'), 503
            count = db.execute('SELECT count(*) FROM rate_limits WHERE ip=? AND at>?', (ip, now - cfg['rate_window'])).fetchone()[0]
            if count >= cfg['rate_limit']:
                return jsonify(success=False, message='Подождите перед повторной отправкой'), 429, {'Retry-After': '600'}
            pending = db.execute("SELECT count(*) FROM leads WHERE state!='sent'").fetchone()[0]
            if pending >= 1000:
                return jsonify(success=False, message='Обработчик временно недоступен'), 503
            payload.update(accepted_at=now, page_url=cfg['origin'] + '/')
            db.execute('INSERT INTO leads (id,fingerprint,payload,created,updated,next_attempt) VALUES (?,?,?,?,?,?)',
                       (identifier, signature, json.dumps(payload, ensure_ascii=False), now, now, now))
            db.execute('INSERT INTO rate_limits VALUES (?,?)', (ip, now))
        app.logger.info('lead_queued id=%s', identifier)
        return jsonify(success=True, request_id=identifier), 202

    return app
