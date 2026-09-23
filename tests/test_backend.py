import json
import tempfile
import time
import unittest
from pathlib import Path
from uuid import uuid4

from backend.app import create_app
from backend.core import clean, database, heartbeat, stats
from backend.worker import DeliveryError, process_one


class LeadsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cfg = {
            'origin': 'https://etrn.example.org', 'secret': 'unit-test-secret-' * 4,
            'database': str(Path(self.temp.name) / 'leads.sqlite3'),
            'recipient': 'etrn@corp.aib.ru', 'rate_limit': 5,
            'rate_window': 600, 'retention': 7 * 86400,
        }
        self.app = create_app(self.cfg)
        self.client = self.app.test_client()
        heartbeat(self.cfg)
        self.payload = {
            'request_id': str(uuid4()), 'contact_type': 'email',
            'email': 'test@example.org', 'name': 'Тест', 'company': '',
            'problem': 'Тестовый документ не отправляется оператору ЭДО.',
            'consent': 'true', '_honey': '',
        }

    def tearDown(self):
        self.temp.cleanup()

    def post(self, payload=None, origin=None, **kwargs):
        return self.client.post('/api/leads', data=payload or self.payload,
                                headers={'Origin': origin or self.cfg['origin']}, **kwargs)

    def row(self):
        with database(self.cfg) as db:
            return dict(db.execute('SELECT * FROM leads LIMIT 1').fetchone())

    def test_accepts_and_persists_before_success(self):
        response = self.post()
        self.assertEqual(response.status_code, 202)
        self.assertIs(response.json['success'], True)
        self.assertEqual(self.row()['state'], 'queued')
        self.assertEqual(json.loads(self.row()['payload'])['contact'], 'test@example.org')

    def test_request_id_retry_and_content_deduplication(self):
        self.post()
        self.assertEqual(self.post().status_code, 200)
        payload = dict(self.payload, request_id=str(uuid4()))
        self.assertEqual(self.post(payload).status_code, 200)
        self.assertEqual(stats(self.cfg)['counts'], {'queued': 1})
        self.assertEqual(self.post(dict(self.payload, problem='Другая неисправность в подписи документа.')).status_code, 409)

    def test_validation_contact_and_consent(self):
        for update in ({'email': 'invalid'}, {'problem': 'short'}, {'consent': ''},
                       {'_honey': 'robot'}, {'name': 'x' * 81}, {'request_id': 'short'},
                       {'company': 'x' * 121}, {'contact_type': 'file'}, {'problem': 'x' * 1501}):
            with self.subTest(update=update):
                self.assertEqual(self.post(dict(self.payload, **update)).status_code, 400)
        self.assertEqual(stats(self.cfg)['counts'], {})

    def test_phone(self):
        payload = dict(self.payload, contact_type='phone', phone='+7 (961) 777-02-20')
        self.assertEqual(self.post(payload).status_code, 202)
        self.assertEqual(json.loads(self.row()['payload'])['contact'], '79617770220')

    def test_origin_and_body_size(self):
        self.assertEqual(self.post(origin='https://foreign.example').status_code, 403)
        self.assertEqual(self.client.post('/api/leads', data=self.payload).status_code, 403)
        self.assertEqual(self.post(dict(self.payload, problem='x' * 17000)).status_code, 413)

    def test_json_malformed_types(self):
        for payload in ([], None, dict(self.payload, problem=['x']), dict(self.payload, consent=True)):
            result = self.client.post('/api/leads', json=payload, headers={'Origin': self.cfg['origin']})
            self.assertEqual(result.status_code, 400)

    def test_rate_limit_and_expiry(self):
        for i in range(5):
            payload = dict(self.payload, request_id=str(uuid4()), problem=self.payload['problem'] + str(i))
            self.assertEqual(self.post(payload).status_code, 202)
        self.assertEqual(self.post().status_code, 429)
        with database(self.cfg) as db:
            db.execute('UPDATE rate_limits SET at=?', (time.time() - 601,))
        self.assertEqual(self.post().status_code, 202)

    def test_stopped_worker_does_not_accept(self):
        with database(self.cfg) as db:
            db.execute('DELETE FROM runtime')
        self.assertEqual(self.post().status_code, 503)
        self.assertEqual(self.client.get('/healthz').status_code, 503)
        self.assertEqual(stats(self.cfg)['counts'], {})

    def test_delivery_and_payload_erasure(self):
        self.post()
        calls = []
        process_one(self.cfg, lambda cfg, identifier, payload: calls.append(identifier))
        self.assertEqual(calls, [self.payload['request_id']])
        self.assertEqual(self.row()['state'], 'sent')
        self.assertIsNone(self.row()['payload'])
        self.assertFalse(process_one(self.cfg, lambda *_: self.fail('duplicate delivery')))

    def test_retry_then_recovery(self):
        self.post()
        def failing(*_):
            raise DeliveryError('provider_unavailable')
        process_one(self.cfg, failing)
        self.assertEqual(self.row()['attempts'], 1)
        self.assertEqual(self.row()['state'], 'queued')
        with database(self.cfg) as db:
            db.execute('UPDATE leads SET next_attempt=0')
        process_one(self.cfg, lambda *_: None)
        self.assertEqual(self.row()['state'], 'sent')

    def test_smtp_auth_failure_and_retention(self):
        self.post()
        def inactive(*_):
            raise DeliveryError('smtp_authentication_failed')
        process_one(self.cfg, inactive)
        self.assertEqual(self.row()['state'], 'failed')
        self.assertEqual(self.client.get('/healthz').status_code, 503)
        self.assertNotIn('test@example.org', str(self.client.get('/healthz').json))
        with database(self.cfg) as db:
            db.execute('UPDATE leads SET created=?', (time.time() - 8 * 86400,))
        self.assertEqual(clean(self.cfg), 1)
        self.assertEqual(stats(self.cfg)['counts'], {})

if __name__ == '__main__':
    unittest.main()
