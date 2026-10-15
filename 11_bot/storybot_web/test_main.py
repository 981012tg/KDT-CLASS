import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from unittest.mock import patch

import torch
from fastapi.testclient import TestClient

from storybot.utils import generate
from storybot_web.main import COOKIE, ROOT, connect, create_app

HEADERS = {'X-Storybot-Request': '1'}
PASSWORD = 'test-password-123'


class StoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handle, filename = tempfile.mkstemp(suffix='.sqlite3', dir=ROOT)
        os.close(handle)
        cls.database_path = Path(filename)
        cls.app = create_app(cls.database_path)
        cls.server = TestClient(cls.app)
        cls.server.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.server.__exit__(None, None, None)
        cls.database_path.unlink()

    def setUp(self):
        db = connect(self.database_path)
        try:
            for table in ('likes', 'posts', 'generations', 'sessions', 'users'):
                db.execute(f'DELETE FROM {table}')
            db.commit()
        finally:
            db.close()
        self.a = TestClient(self.app, headers=HEADERS)
        self.b = TestClient(self.app, headers=HEADERS)
        self.guest = TestClient(self.app, headers=HEADERS)
        self.addCleanup(self.a.close)
        self.addCleanup(self.b.close)
        self.addCleanup(self.guest.close)
        for client, name in ((self.a, 'member_a'), (self.b, 'member_b')):
            self.assertEqual(client.post('/api/signup', json={
                'username': name, 'password': PASSWORD, 'nickname': name,
            }).status_code, 201)
            self.assertEqual(client.post('/api/login', json={
                'username': name, 'password': PASSWORD,
            }).status_code, 200)

    def generate_record(self):
        with patch('storybot_web.main.generate', return_value='Once upon a time\nA happy ending.'):
            response = self.a.post('/api/generate', json={'prompt': 'Once upon a time'})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def publish(self, record):
        response = self.a.post('/api/posts', json={
            'generation_id': record['id'], 'title': '우리 이야기', 'content': record['content'],
        })
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_auth_validation_and_password_storage(self):
        self.assertEqual(self.guest.post('/api/signup', json={
            'username': 'member_a', 'password': PASSWORD, 'nickname': '중복',
        }).status_code, 409)
        self.assertEqual(self.guest.post('/api/login', json={
            'username': 'member_a', 'password': 'wrong-password',
        }).status_code, 401)
        for values in (
            {'username': 'bad!', 'password': PASSWORD, 'nickname': '이름'},
            {'username': 'valid_id', 'password': 'short', 'nickname': '이름'},
            {'username': 'valid_id', 'password': PASSWORD, 'nickname': '   '},
        ):
            self.assertEqual(self.guest.post('/api/signup', json=values).status_code, 422)
        db = connect(self.database_path)
        try:
            self.assertNotEqual(db.execute('SELECT password_hash FROM users LIMIT 1').fetchone()[0], PASSWORD)
            self.assertNotEqual(db.execute('SELECT token_hash FROM sessions LIMIT 1').fetchone()[0], self.a.cookies.get(COOKIE))
        finally:
            db.close()
        self.assertEqual(set(self.a.get('/api/me').json()['user']), {'id', 'username', 'nickname'})
        self.assertEqual(self.guest.get('/api/me').json(), {'user': None})

    def test_session_persistence_expiration_logout(self):
        login = self.a.post('/api/login', json={'username': 'member_a', 'password': PASSWORD})
        cookie = login.headers['set-cookie'].lower()
        for expected in ('httponly', 'samesite=strict', 'max-age=604800'):
            self.assertIn(expected, cookie)
        with TestClient(self.app, headers=HEADERS, cookies=self.a.cookies) as reopened:
            self.assertIsNotNone(reopened.get('/api/me').json()['user'])
        old = self.a.cookies.get(COOKIE)
        self.assertEqual(self.a.post('/api/logout').status_code, 200)
        self.a.cookies.set(COOKIE, old)
        self.assertEqual(self.a.get('/api/history').status_code, 401)
        db = connect(self.database_path)
        try:
            db.execute('UPDATE sessions SET expires_at=0')
            db.commit()
        finally:
            db.close()
        self.assertEqual(self.b.get('/api/history').status_code, 401)

    def test_profile_change_invalidates_all_sessions(self):
        self.assertEqual(self.a.patch('/api/me', json={'nickname': '바뀐 이름'}).status_code, 200)
        self.assertEqual(self.a.get('/api/me').json()['user']['nickname'], '바뀐 이름')
        self.assertEqual(self.b.get('/api/me').json()['user']['nickname'], 'member_b')
        self.assertEqual(self.a.patch('/api/me', json={'nickname': '침입', 'user_id': 2}).status_code, 422)
        self.assertEqual(self.a.patch('/api/me', json={
            'new_password': 'new-password-123', 'current_password': 'wrong-password',
        }).status_code, 403)
        other = TestClient(self.app, headers=HEADERS)
        self.addCleanup(other.close)
        other.post('/api/login', json={'username': 'member_a', 'password': PASSWORD})
        self.assertEqual(self.a.patch('/api/me', json={
            'new_password': 'new-password-123', 'current_password': PASSWORD,
        }).status_code, 200)
        self.assertEqual(other.get('/api/history').status_code, 401)
        self.assertEqual(self.a.get('/api/history').status_code, 401)
        self.assertEqual(self.a.post('/api/login', json={'username': 'member_a', 'password': PASSWORD}).status_code, 401)
        self.assertEqual(self.a.post('/api/login', json={'username': 'member_a', 'password': 'new-password-123'}).status_code, 200)

    def test_real_generation_publish_and_public_read(self):
        response = self.a.post('/api/generate', json={'prompt': 'Once upon a time'})
        self.assertEqual(response.status_code, 201, response.text)
        record = response.json()
        self.assertTrue(record['content'].startswith('Once upon a time'))
        self.assertGreater(len(record['content']), len('Once upon a time'))
        post = self.publish(record)
        for client in (self.b, self.guest):
            self.assertEqual(client.get('/api/posts').json()['total'], 1)
            self.assertEqual(client.get(f"/api/posts/{post['id']}").json()['content'], record['content'])

    def test_history_privacy_and_post_permissions(self):
        record = self.generate_record()
        self.assertEqual(self.b.get('/api/history').json()['items'], [])
        self.assertEqual(self.b.get(f"/api/history/{record['id']}").status_code, 404)
        self.assertEqual(self.guest.get('/api/history').status_code, 401)
        post = self.publish(record)
        path = f"/api/posts/{post['id']}"
        for client, status in ((self.b, 403), (self.guest, 401)):
            self.assertEqual(client.patch(path, json={'title': '변경', 'content': '변경'}).status_code, status)
            self.assertEqual(client.delete(path).status_code, status)
        self.assertEqual(self.b.post('/api/posts', json={
            'generation_id': record['id'], 'title': '도용', 'content': '도용',
        }).status_code, 403)
        self.assertEqual(self.a.patch(path, json={'title': '수정', 'content': '수정한 본문'}).status_code, 200)
        self.assertEqual(self.a.get(f"/api/history/{record['id']}").json()['content'], record['content'])
        self.assertEqual(self.a.post('/api/posts', json={
            'generation_id': record['id'], 'title': '중복', 'content': '중복',
        }).status_code, 409)
        self.b.put(path + '/like')
        self.assertEqual(self.a.delete(path).status_code, 200)
        self.assertEqual(self.guest.get(path).status_code, 404)
        self.assertIsNone(self.a.get(f"/api/history/{record['id']}").json()['post_id'])
        self.assertEqual(self.publish(record)['like_count'], 0)

    def test_like_idempotence_and_ownership(self):
        post = self.publish(self.generate_record())
        path = f"/api/posts/{post['id']}/like"
        self.assertEqual(self.guest.put(path).status_code, 401)
        self.assertEqual(self.a.put(path).json()['like_count'], 1)
        self.assertEqual(self.b.put(path).json()['like_count'], 2)
        self.assertEqual(self.b.put(path).json()['like_count'], 2)
        self.assertEqual(self.b.delete(path).json()['like_count'], 1)
        self.assertEqual(self.b.delete(path).json()['like_count'], 1)
        self.assertTrue(self.a.get(f"/api/posts/{post['id']}").json()['liked'])
        self.assertFalse(self.b.get(f"/api/posts/{post['id']}").json()['liked'])

    def test_token_limits_and_failure_no_history(self):
        self.assertEqual(self.guest.post('/api/generate', json={'prompt': 'Once'}).status_code, 401)
        for body in ({'prompt': ''}, {'prompt': ' \n\t'}, {'prompt': 123}, {'prompt': 'hello', 'max_new_tokens': 999}):
            self.assertEqual(self.a.post('/api/generate', json=body).status_code, 422)
        for size in (128, 129):
            prompt = '<|endoftext|>' * size
            self.assertEqual(len(self.app.state.tokenizer.encode(prompt)), size)
            with patch('storybot_web.main.generate', return_value='story') as mocked:
                response = self.a.post('/api/generate', json={'prompt': prompt})
                self.assertEqual(response.status_code, 201 if size == 128 else 422)
                if size == 128:
                    self.assertEqual(mocked.call_args.kwargs['max_new_tokens'], 128)
                else:
                    mocked.assert_not_called()
                    self.assertEqual(response.json()['detail']['input_tokens'], size)
        prompt = '  한글\nOnce upon a time\n'
        with patch('storybot_web.main.generate', return_value=prompt) as mocked:
            self.assertEqual(self.a.post('/api/generate', json={'prompt': prompt}).status_code, 201)
            self.assertEqual(mocked.call_args.args[2], prompt)
        before = self.a.get('/api/history').json()['total']
        with patch('storybot_web.main.generate', side_effect=RuntimeError('test')):
            with self.assertLogs('storybot_web.main', level='ERROR'):
                self.assertEqual(self.a.post('/api/generate', json={'prompt': 'Once'}).status_code, 500)
        with patch('storybot_web.main.generate', return_value=''):
            self.assertEqual(self.a.post('/api/generate', json={'prompt': 'Once'}).status_code, 500)
        self.assertEqual(self.a.get('/api/history').json()['total'], before)
        self.assertFalse(self.app.state.generation_lock.locked())

    def test_concurrent_generation(self):
        entered, release = Event(), Event()
        def slow(*args, **kwargs):
            entered.set()
            release.wait(10)
            return 'A story'
        with patch('storybot_web.main.generate', side_effect=slow):
            with ThreadPoolExecutor() as pool:
                first = pool.submit(self.a.post, '/api/generate', json={'prompt': 'Once'})
                try:
                    self.assertTrue(entered.wait(10))
                    self.assertEqual(self.b.post('/api/generate', json={'prompt': 'Once'}).status_code, 503)
                finally:
                    release.set()
                self.assertEqual(first.result().status_code, 201)

    def test_pagination_and_restart_persistence(self):
        for _ in range(11):
            self.publish(self.generate_record())
        self.a.put('/api/posts/1/like')
        for route, client in (('/api/posts', self.guest), ('/api/history', self.a)):
            first = client.get(route).json()
            second = client.get(route + '?page=2').json()
            self.assertEqual(len(first['items']), 10)
            self.assertEqual(len(second['items']), 1)
            self.assertGreater(first['items'][0]['id'], second['items'][0]['id'])
            self.assertEqual(client.get(route + '?page=0').status_code, 422)
        with TestClient(create_app(self.database_path), headers=HEADERS, cookies=self.a.cookies) as restarted:
            self.assertIsNotNone(restarted.get('/api/me').json()['user'])
            self.assertEqual(restarted.get('/api/posts').json()['total'], 11)
            self.assertEqual(restarted.get('/api/history').json()['total'], 11)
            self.assertEqual(restarted.get('/api/posts/1').json()['like_count'], 1)

    def test_generation_loop_and_end(self):
        tokenizer = self.app.state.tokenizer
        class FixedModel(torch.nn.Module):
            max_context_len = 256
            def __init__(self, token):
                super().__init__()
                self.anchor = torch.nn.Parameter(torch.zeros(1))
                self.token = token
                self.calls = 0
                self.cleared = False
            def clear_cache(self):
                self.cleared = True
            def forward(self, ids, use_cache=False):
                self.calls += 1
                logits = torch.full((1, ids.shape[1], tokenizer.vocab_size), -100.)
                logits[:, :, self.token] = 100.
                return logits
        model = FixedModel(ord('x'))
        self.assertEqual(generate(model, tokenizer, 'Once', max_new_tokens=128, temperature=0), 'Once' + 'x' * 128)
        self.assertEqual(model.calls, 128)
        self.assertTrue(model.cleared)
        model = FixedModel(tokenizer.end_token_id)
        self.assertEqual(generate(model, tokenizer, 'Once', max_new_tokens=128), 'Once')
        self.assertEqual(model.calls, 1)

    def test_request_protection_and_text_limits(self):
        with TestClient(self.app) as plain:
            self.assertEqual(plain.post('/api/logout').status_code, 403)
        record = self.generate_record()
        for title, content in ((' ', 'story'), ('title', ' '), ('x' * 101, 'story'), ('title', 'x' * 10001)):
            self.assertEqual(self.a.post('/api/posts', json={
                'generation_id': record['id'], 'title': title, 'content': content,
            }).status_code, 422)


if __name__ == '__main__':
    unittest.main()
