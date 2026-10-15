import React, { useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

function App() {
  const [code, setCode] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const pending = useRef(false);

  async function submit(event) {
    event.preventDefault();
    if (pending.current) return;
    setError('');
    if (!code.trim()) {
      setError('코드를 입력해주세요.');
      return;
    }
    pending.current = true;
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail?.message || '코드 생성에 실패했습니다. 다시 시도해주세요.');
      }
      setResult(data.code);
    } catch (failure) {
      setError(failure instanceof TypeError || failure instanceof SyntaxError
        ? '서버에 연결할 수 없습니다. 서버 실행 상태를 확인하고 다시 시도해주세요.'
        : failure.message);
    } finally {
      pending.current = false;
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>코드봇</h1>
      <p>코드를 입력하면 이어지는 코드를 만들어드립니다.</p>
      <form onSubmit={submit}>
        <label htmlFor="code">입력 코드</label>
        <p id="limits" className="hint">입력 최대 256토큰 · 추가 생성 최대 256토큰</p>
        <textarea id="code" value={code} onChange={event => setCode(event.target.value)}
          aria-describedby="limits" spellCheck={false} autoCapitalize="off"
          autoCorrect="off" disabled={loading} placeholder="def" />
        <button type="submit" disabled={loading}>코드 생성</button>
      </form>
      <p role="status">{loading ? '코드를 생성하고 있습니다…' : ''}</p>
      {error && <p role="alert" className="error">{error}</p>}
      <section aria-labelledby="result-title" aria-busy={loading}>
        <h2 id="result-title">전체 코드</h2>
        {result === null
          ? <p className="hint">생성 결과가 여기에 표시됩니다.</p>
          : <pre><code>{result}</code></pre>}
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
