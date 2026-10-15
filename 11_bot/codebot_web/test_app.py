import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch

import torch
from fastapi.testclient import TestClient

from codebot.utils import generate
from codebot_web.main import app


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def test_real_model(self):
        self.assertEqual(app.state.model.max_context_len, 256)
        response = self.client.post('/api/generate', json={'code': 'def'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['code'].startswith('def'))

    def test_invalid_input_does_not_generate(self):
        with patch('codebot_web.main.generate') as mocked:
            for body in ({'code': ''}, {'code': ' \t\n'}, {'code': 42}, {},
                         {'code': 'def', 'max_new_tokens': 999}):
                self.assertEqual(self.client.post('/api/generate', json=body).status_code, 422)
            mocked.assert_not_called()

    def test_token_boundaries(self):
        tokenizer = app.state.tokenizer
        for size in (256, 257):
            code = '<|endoftext|>' * size
            self.assertEqual(len(tokenizer.encode(code)), size)
            with patch('codebot_web.main.generate', return_value=code) as mocked:
                response = self.client.post('/api/generate', json={'code': code})
                if size == 256:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(mocked.call_args.kwargs['max_new_tokens'], 256)
                else:
                    self.assertEqual(response.status_code, 422)
                    self.assertEqual(response.json()['detail']['input_tokens'], 257)
                    mocked.assert_not_called()

    def test_whitespace_and_unicode(self):
        code = '  # 한글 주석\n\tdef sample():\n    '
        with patch('codebot_web.main.generate', return_value=code) as mocked:
            response = self.client.post('/api/generate', json={'code': code})
            self.assertEqual(response.json()['code'], code)
            self.assertEqual(mocked.call_args.args[2], code)
        code = '# 한글 주석\n' * 100
        response = self.client.post('/api/generate', json={'code': code})
        self.assertEqual(response.json()['detail']['input_tokens'], len(app.state.tokenizer.encode(code)))

    def test_failure_releases_lock(self):
        with patch('codebot_web.main.generate', side_effect=RuntimeError('test')):
            with self.assertLogs('codebot_web.main', level='ERROR'):
                self.assertEqual(self.client.post('/api/generate', json={'code': 'def'}).status_code, 500)
        with patch('codebot_web.main.generate', return_value='def'):
            self.assertEqual(self.client.post('/api/generate', json={'code': 'def'}).status_code, 200)

    def test_concurrent_request(self):
        entered, release = Event(), Event()

        def slow_generate(*args, **kwargs):
            entered.set()
            release.wait(10)
            return 'def'

        with patch('codebot_web.main.generate', side_effect=slow_generate):
            with ThreadPoolExecutor() as pool:
                future = pool.submit(self.client.post, '/api/generate', json={'code': 'def'})
                try:
                    self.assertTrue(entered.wait(10))
                    self.assertEqual(self.client.post('/api/generate', json={'code': 'def'}).status_code, 503)
                finally:
                    release.set()
                self.assertEqual(future.result().status_code, 200)

    def test_generation_window_and_end_token(self):
        tokenizer = app.state.tokenizer

        class FixedModel(torch.nn.Module):
            max_context_len = 256

            def __init__(self, token):
                super().__init__()
                self.anchor = torch.nn.Parameter(torch.zeros(1))
                self.token = token
                self.lengths = []

            def forward(self, ids):
                self.lengths.append(ids.shape[1])
                logits = torch.full((1, ids.shape[1], tokenizer.vocab_size), -100.0)
                logits[:, :, self.token] = 100.0
                return logits

        prompt = '<|endoftext|>' * 256
        model = FixedModel(ord('x'))
        result = generate(model, tokenizer, prompt, max_new_tokens=256, temperature=0)
        self.assertEqual(result, prompt + 'x' * 256)
        self.assertEqual(model.lengths, [256] * 256)
        model = FixedModel(tokenizer.end_token_id)
        self.assertEqual(generate(model, tokenizer, 'def', max_new_tokens=256), 'def')
        self.assertEqual(len(model.lengths), 1)


if __name__ == '__main__':
    unittest.main()
