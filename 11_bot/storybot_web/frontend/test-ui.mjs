import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { JSDOM, VirtualConsole } from 'jsdom';

const base = 'http://127.0.0.1:18001';
const html = await readFile(new URL('./dist/index.html', import.meta.url), 'utf8');
const asset = html.match(/src="(\/assets\/[^\"]+\.js)"/)[1];
const bundle = await readFile(new URL('./dist' + asset, import.meta.url), 'utf8');
const failures = [];
const windows = [];
const unique = Date.now().toString(36);
const password = 'ui-password-123';

function mount(cookieJar) {
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', error => failures.push(error.message));
  const dom = new JSDOM(html, { url: base, runScripts: 'outside-only', pretendToBeVisual: true, cookieJar, virtualConsole });
  dom.window.fetch = async (path, options = {}) => {
    const headers = new Headers(options.headers);
    const cookies = dom.cookieJar.getCookieStringSync(base);
    if (cookies) headers.set('Cookie', cookies);
    const response = await fetch(new URL(path, base), { ...options, headers });
    for (const cookie of response.headers.getSetCookie()) dom.cookieJar.setCookieSync(cookie, base);
    return response;
  };
  dom.window.eval(bundle);
  windows.push(dom);
  return dom;
}

async function until(predicate, message) {
  const start = Date.now();
  while (!predicate()) {
    if (Date.now() - start > 15000) throw new Error(message);
    await new Promise(resolve => setTimeout(resolve, 20));
  }
}

const text = dom => dom.window.document.body.textContent;
const buttons = dom => [...dom.window.document.querySelectorAll('button')];
const button = (dom, label) => buttons(dom).find(item => item.textContent === label);
async function click(dom, label) {
  await until(() => button(dom, label) && !button(dom, label).disabled, `버튼 대기: ${label}`);
  button(dom, label).click();
  await new Promise(resolve => setTimeout(resolve, 30));
}
function input(dom, selector, value) {
  const field = dom.window.document.querySelector(selector);
  assert.ok(field, selector);
  const prototype = field.tagName === 'TEXTAREA' ? dom.window.HTMLTextAreaElement.prototype : dom.window.HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(prototype, 'value').set.call(field, value);
  field.dispatchEvent(new dom.window.Event('input', { bubbles: true }));
  field.dispatchEvent(new dom.window.Event('change', { bubbles: true }));
}
async function signupAndLogin(dom, username) {
  await click(dom, '회원가입');
  input(dom, '[name=username]', username);
  input(dom, '[name=password]', password);
  input(dom, '[name=nickname]', username);
  await click(dom, '가입하기');
  await until(() => text(dom).includes('회원가입이 완료되었습니다'), '가입 완료');
  input(dom, '[name=username]', username);
  input(dom, '[name=password]', password);
  dom.window.document.querySelector('form').requestSubmit();
  await until(() => text(dom).includes(username + ' 님'), '로그인 완료');
}

try {
  const a = mount();
  const b = mount();
  const guest = mount();
  await signupAndLogin(a, 'a_' + unique);
  await signupAndLogin(b, 'b_' + unique);
  await click(a, '스토리 생성');
  input(a, 'textarea', 'Once upon a time');
  await click(a, '이야기 생성');
  await until(() => text(a).includes('생성 결과 확인 및 게시'), '실제 생성 결과');
  assert.ok(a.window.document.querySelector('.body-input').value.startsWith('Once upon a time'));
  input(a, 'input', 'UI 테스트 이야기');
  await click(a, '게시하기');
  await until(() => text(a).includes('게시했습니다.'), '게시 완료');
  assert.ok(button(a, '수정'));
  assert.ok(button(a, '삭제'));
  await click(b, '전체 스토리');
  await click(b, 'UI 테스트 이야기');
  assert.equal(button(b, '수정'), undefined);
  assert.equal(button(b, '삭제'), undefined);
  await click(b, '좋아요 · 0');
  await until(() => Boolean(button(b, '좋아요 취소 · 1')), '좋아요 증가');
  await click(b, '좋아요 취소 · 1');
  await until(() => Boolean(button(b, '좋아요 · 0')), '좋아요 취소');
  await click(guest, '전체 스토리');
  await click(guest, 'UI 테스트 이야기');
  assert.ok(button(guest, '좋아요 · 0').disabled);
  assert.equal(button(guest, '수정'), undefined);
  await click(b, '내 생성 기록');
  await until(() => text(b).includes('아직 생성 기록이 없습니다.'), '다른 회원의 기록 미노출');
  await click(a, '수정');
  input(a, 'input', '수정한 제목');
  input(a, 'textarea', '<script>window.storyExecuted=true</script>\n수정한 이야기');
  await click(a, '수정 저장');
  await until(() => text(a).includes('게시물을 수정했습니다.'), '수정 완료');
  assert.equal(a.window.storyExecuted, undefined);
  assert.ok(text(a).includes('<script>window.storyExecuted=true</script>'));
  const reopened = mount(a.cookieJar);
  await until(() => text(reopened).includes('a_' + unique + ' 님'), '로그인 유지');
  await click(a, '삭제');
  await until(() => text(a).includes('게시물을 삭제했습니다.'), '삭제 완료');
  await click(a, '내 생성 기록');
  await click(a, '이 이야기 게시하기');
  assert.ok(a.window.document.querySelector('.body-input').value.startsWith('Once upon a time'));
  input(a, 'textarea', '<|endoftext|>'.repeat(129));
  await click(a, '이야기 생성');
  await until(() => text(a).includes('129토큰'), '입력 초과 안내');
  assert.equal(a.window.document.querySelector('textarea').value, '<|endoftext|>'.repeat(129));
  await click(a, '회원정보 수정');
  input(a, '[name=nickname]', '변경한닉네임');
  input(a, '[name=current_password]', password);
  input(a, '[name=new_password]', 'changed-password-123');
  await click(a, '수정하기');
  await until(() => text(a).includes('다시 로그인해주세요.'), '비밀번호 변경 후 로그아웃');
  assert.equal(button(a, '로그아웃'), undefined);
  assert.deepEqual(failures, []);
  console.log('PASS: React DOM + 실제 FastAPI/모델 연동 (가입, 로그인, 생성, 게시, 타인/비회원 조회, 권한별 버튼, 좋아요/취소, 수정/삭제, 기록 보존, 로그인 유지, 입력 초과, 비밀번호 변경)');
} finally {
  for (const dom of windows) dom.window.close();
}
