import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

const date = value => new Date(value * 1000).toLocaleString('ko-KR');

function App() {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);
  const [view, setView] = useState('posts');
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [page, setPage] = useState(1);
  const [list, setList] = useState({ items: [], total: 0 });
  const [loadingList, setLoadingList] = useState(false);
  const [revision, setRevision] = useState(0);
  const [selected, setSelected] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [record, setRecord] = useState(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');

  function clearPrivate() {
    setUser(null); setPrompt(''); setRecord(null); setTitle(''); setContent('');
    setSelected(null); setList({ items: [], total: 0 });
  }

  async function api(path, method = 'GET', body) {
    let response;
    try {
      response = await fetch('/api' + path, {
        method, credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'X-Storybot-Request': '1' },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
    } catch {
      throw new Error('서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.');
    }
    let data;
    try { data = await response.json(); }
    catch { throw new Error('서버 응답을 확인할 수 없습니다. 다시 시도해주세요.'); }
    if (!response.ok) {
      if (response.status === 401 && path !== '/login') {
        setUser(null); setView('login');
      }
      throw new Error(data.detail?.message || '요청에 실패했습니다. 다시 시도해주세요.');
    }
    return data;
  }

  async function act(work) {
    if (pending.current) return;
    pending.current = true; setBusy(true); setError(''); setNotice('');
    try { await work(); }
    catch (failure) { setError(failure.message); }
    finally { pending.current = false; setBusy(false); }
  }

  function navigate(next) {
    setView(next); setPage(1); setError(''); setNotice('');
    setList({ items: [], total: 0 }); setRevision(value => value + 1);
  }

  useEffect(() => {
    api('/me').then(data => setUser(data.user)).catch(failure => setError(failure.message))
      .finally(() => setReady(true));
  }, []);

  useEffect(() => {
    if (!ready || !['posts', 'history'].includes(view)) return;
    let active = true;
    setLoadingList(true);
    api(`/${view === 'posts' ? 'posts' : 'history'}?page=${page}`)
      .then(data => { if (active) setList(data); })
      .catch(failure => { if (active) setError(failure.message); })
      .finally(() => { if (active) setLoadingList(false); });
    return () => { active = false; };
  }, [ready, view, page, revision]);

  const openPost = id => act(async () => { setSelected(await api(`/posts/${id}`)); setView('detail'); });
  const openRecord = item => { setRecord(item); setPrompt(item.prompt); setTitle(''); setContent(item.content); navigate('compose'); };

  function authSubmit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form));
    act(async () => {
      if (view === 'signup') {
        const data = await api('/signup', 'POST', values);
        form.reset(); navigate('login'); setNotice(data.message);
      } else {
        const nextUser = await api('/login', 'POST', values);
        clearPrivate(); setUser(nextUser); form.reset(); navigate('posts');
      }
    });
  }

  function profileSubmit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form));
    if (!values.new_password) { delete values.new_password; delete values.current_password; }
    act(async () => {
      const data = await api('/me', 'PATCH', values);
      if (data.logged_out) {
        clearPrivate(); navigate('login'); setNotice('비밀번호를 변경했습니다. 다시 로그인해주세요.');
      } else {
        setUser((await api('/me')).user); setNotice('회원정보를 수정했습니다.');
      }
    });
  }

  function generateStory(event) {
    event.preventDefault();
    act(async () => {
      const data = await api('/generate', 'POST', { prompt });
      setRecord(data); setContent(data.content); setTitle('');
      setNotice('생성 기록에 저장했습니다. 제목과 본문을 확인한 뒤 게시해주세요.');
    });
  }

  function savePost(event) {
    event.preventDefault();
    act(async () => {
      const editing = view === 'edit';
      const data = await api(editing ? `/posts/${selected.id}` : '/posts', editing ? 'PATCH' : 'POST',
        { title, content, ...(editing ? {} : { generation_id: record.id }) });
      setSelected(data);
      if (!editing) setRecord(previous => ({ ...previous, post_id: data.id }));
      setView('detail'); setNotice(editing ? '게시물을 수정했습니다.' : '게시했습니다.');
    });
  }

  return (
    <main>
      <header>
        <div><h1>스토리봇</h1><p>이야기를 만들고 함께 읽어보세요.</p></div>
        <nav aria-label="메인 메뉴">
          <button disabled={busy} onClick={() => navigate('posts')}>전체 스토리</button>
          {ready && (user ? <>
            <span>{user.nickname} 님</span>
            <button disabled={busy} onClick={() => navigate('compose')}>스토리 생성</button>
            <button disabled={busy} onClick={() => navigate('history')}>내 생성 기록</button>
            <button disabled={busy} onClick={() => navigate('profile')}>회원정보 수정</button>
            <button disabled={busy} onClick={() => act(async () => {
              await api('/logout', 'POST'); clearPrivate(); navigate('posts');
            })}>로그아웃</button>
          </> : <>
            <button disabled={busy} onClick={() => navigate('signup')}>회원가입</button>
            <button disabled={busy} onClick={() => navigate('login')}>로그인</button>
          </>)}
        </nav>
      </header>
      <div aria-live="polite">{busy && <p>처리 중입니다…</p>}{notice && <p className="notice">{notice}</p>}</div>
      {error && <p role="alert" className="error">{error}</p>}
      {!ready ? <p>로그인 상태를 확인하고 있습니다…</p> : <>
        {['signup', 'login'].includes(view) && <section>
          <h2>{view === 'signup' ? '회원가입' : '로그인'}</h2>
          <form key={view} onSubmit={authSubmit}><fieldset disabled={busy}>
            <label>아이디<input name="username" required minLength={4} maxLength={20} pattern="[A-Za-z0-9_]+" autoComplete="username" /></label>
            <p className="hint">영문·숫자·밑줄 4~20자</p>
            <label>비밀번호<input type="password" name="password" required minLength={8} maxLength={128} autoComplete={view === 'signup' ? 'new-password' : 'current-password'} /></label>
            <p className="hint">8~128자 · 로그인은 7일간 유지됩니다.</p>
            {view === 'signup' && <label>닉네임<input name="nickname" required maxLength={30} /></label>}
            <button className="primary">{view === 'signup' ? '가입하기' : '로그인'}</button>
          </fieldset></form>
        </section>}
        {view === 'profile' && user && <section>
          <h2>회원정보 수정</h2><p>아이디: {user.username}</p>
          <form onSubmit={profileSubmit}><fieldset disabled={busy}>
            <label>닉네임<input name="nickname" required maxLength={30} defaultValue={user.nickname} /></label>
            <label>현재 비밀번호<input type="password" name="current_password" maxLength={128} autoComplete="current-password" /></label>
            <label>새 비밀번호<input type="password" name="new_password" minLength={8} maxLength={128} autoComplete="new-password" /></label>
            <p className="hint">비밀번호를 바꿀 때만 두 비밀번호를 입력하세요. 변경하면 모든 로그인이 해제됩니다.</p>
            <button className="primary">수정하기</button>
          </fieldset></form>
        </section>}
        {['posts', 'history'].includes(view) && <section>
          <h2>{view === 'posts' ? '전체 스토리' : '내 생성 기록'}</h2>
          {view === 'history' && <p className="hint">이 기록은 본인만 볼 수 있습니다. 게시한 스토리는 누구나 볼 수 있습니다.</p>}
          {loadingList ? <p>목록을 불러오고 있습니다…</p> : <>
            {!list.items.length && <p>아직 {view === 'posts' ? '게시된 스토리가' : '생성 기록이'} 없습니다.</p>}
            {list.items.map(item => <article key={item.id}>
              {view === 'posts' ? <>
                <h3><button className="link" disabled={busy} onClick={() => openPost(item.id)}>{item.title}</button></h3>
                <p className="hint">{item.author} · {date(item.created_at)} · 좋아요 {item.like_count}</p>
              </> : <>
                <p className="hint">{date(item.created_at)} · {item.post_id ? '게시됨' : '미게시'}</p>
                <h3>입력 내용</h3><p className="story">{item.prompt}</p>
                <h3>생성 결과</h3><p className="story">{item.content}</p>
                <button disabled={busy} onClick={() => item.post_id ? openPost(item.post_id) : openRecord(item)}>
                  {item.post_id ? '게시물 보기' : '이 이야기 게시하기'}
                </button>
              </>}
            </article>)}
          </>}
          <div className="pagination">
            <button disabled={busy || loadingList || page === 1} onClick={() => setPage(page - 1)}>이전</button>
            <span>{page} / {Math.max(1, Math.ceil(list.total / 10))}</span>
            <button disabled={busy || loadingList || page * 10 >= list.total} onClick={() => setPage(page + 1)}>다음</button>
          </div>
        </section>}
        {view === 'compose' && user && <section>
          <h2>스토리 생성</h2>
          <form onSubmit={generateStory}><fieldset disabled={busy}>
            <label>이야기의 시작 부분<textarea value={prompt} onChange={event => setPrompt(event.target.value)} required placeholder="Once upon a time" /></label>
            <p className="hint">입력 최대 128토큰 · 추가 생성 최대 128토큰</p>
            <button className="primary">이야기 생성</button>
          </fieldset></form>
          {record && <div className="generated">
            {record.post_id ? <p>게시한 이야기입니다. 내 생성 기록에서 게시물을 확인할 수 있습니다.</p> : <>
              <h2>생성 결과 확인 및 게시</h2>
              <PostForm {...{ title, setTitle, content, setContent, busy }} onSubmit={savePost} label="게시하기" />
            </>}
          </div>}
        </section>}
        {view === 'edit' && user && <section><h2>스토리 수정</h2>
          <PostForm {...{ title, setTitle, content, setContent, busy }} onSubmit={savePost} label="수정 저장" />
          <button disabled={busy} onClick={() => setView('detail')}>취소</button>
        </section>}
        {view === 'detail' && selected && <section>
          <h2>{selected.title}</h2><p className="hint">{selected.author} · {date(selected.created_at)}</p>
          <p className="story">{selected.content}</p>
          <div className="actions">
            <button disabled={busy || !user} aria-pressed={Boolean(selected.liked)} onClick={() => act(async () => {
              setSelected(await api(`/posts/${selected.id}/like`, selected.liked ? 'DELETE' : 'PUT'));
            })}>{selected.liked ? '좋아요 취소' : '좋아요'} · {selected.like_count}</button>
            {!user && <span className="hint">좋아요는 로그인 후 사용할 수 있습니다.</span>}
            {user?.id === selected.author_id && <>
              <button disabled={busy} onClick={() => { setTitle(selected.title); setContent(selected.content); setView('edit'); }}>수정</button>
              <button disabled={busy} onClick={() => act(async () => {
                await api(`/posts/${selected.id}`, 'DELETE');
                setRecord(null); setSelected(null); navigate('posts'); setNotice('게시물을 삭제했습니다. 생성 기록은 유지됩니다.');
              })}>삭제</button>
            </>}
          </div>
        </section>}
      </>}
    </main>
  );
}

function PostForm({ title, setTitle, content, setContent, busy, onSubmit, label }) {
  return <form onSubmit={onSubmit}><fieldset disabled={busy}>
    <label>제목<input value={title} onChange={event => setTitle(event.target.value)} required maxLength={100} /></label>
    <label>본문<textarea className="body-input" value={content} onChange={event => setContent(event.target.value)} required maxLength={10000} /></label>
    <p className="hint">제목 최대 100자 · 본문 최대 10,000자</p>
    <button className="primary">{label}</button>
  </fieldset></form>;
}

createRoot(document.getElementById('root')).render(<App />);
