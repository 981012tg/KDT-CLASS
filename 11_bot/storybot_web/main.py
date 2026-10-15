import hashlib
import hmac
import logging
import secrets
import sqlite3
import time
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictStr

from storybot.model import GPT
from storybot.tokenizer import BPETokenizer
from storybot.utils import generate, get_device

ROOT = Path(__file__).resolve().parent
COOKIE = "storybot_session"
SESSION_SECONDS = 7 * 24 * 60 * 60
logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL, nickname TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
    expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS generations (
    id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
    prompt TEXT NOT NULL, content TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
    generation_id INTEGER NOT NULL UNIQUE REFERENCES generations(id),
    title TEXT NOT NULL, content TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS likes (
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id), PRIMARY KEY(post_id, user_id)
);
"""


def connect(path):
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def database(request: Request):
    connection = connect(request.app.state.database_path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def fail(status, message, **details):
    raise HTTPException(status, detail={"message": message, **details})


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    value = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
    return salt + ":" + value.hex()


def valid_password(password, stored):
    return hmac.compare_digest(password_hash(password, stored.split(":")[0]), stored)


def current_user(request: Request, db=Depends(database, scope="function")):
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    user = db.execute(
        "SELECT u.id, u.username, u.nickname FROM users u JOIN sessions s ON u.id=s.user_id "
        "WHERE s.token_hash=? AND s.expires_at>?", (token_hash(token), time.time())
    ).fetchone()
    return dict(user) if user else None


def member(user=Depends(current_user)):
    if user is None:
        fail(401, "로그인이 필요합니다.")
    return user


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Credentials(Input):
    username: StrictStr = Field(min_length=4, max_length=20, pattern=r"^[A-Za-z0-9_]+$")
    password: StrictStr = Field(min_length=8, max_length=128)


class Signup(Credentials):
    nickname: StrictStr = Field(min_length=1, max_length=30)


class Profile(Input):
    nickname: StrictStr | None = Field(default=None, min_length=1, max_length=30)
    new_password: StrictStr | None = Field(default=None, min_length=8, max_length=128)
    current_password: StrictStr | None = Field(default=None, max_length=128)


class Prompt(Input):
    prompt: StrictStr


class PostText(Input):
    title: StrictStr = Field(min_length=1, max_length=100)
    content: StrictStr = Field(min_length=1, max_length=10000)


class NewPost(PostText):
    generation_id: int = Field(strict=True, gt=0)


def require_text(value, label):
    if not value.strip():
        fail(422, f"{label}을(를) 입력해주세요.")


POST_SELECT = """
SELECT p.id, p.user_id AS author_id, u.nickname AS author, p.title, p.content, p.created_at,
    (SELECT COUNT(*) FROM likes l WHERE l.post_id=p.id) AS like_count,
    EXISTS(SELECT 1 FROM likes l WHERE l.post_id=p.id AND l.user_id=?) AS liked
FROM posts p JOIN users u ON u.id=p.user_id
"""


def get_post(db, post_id, user=None):
    row = db.execute(POST_SELECT + " WHERE p.id=?", (user['id'] if user else -1, post_id)).fetchone()
    if row is None:
        fail(404, "게시물을 찾을 수 없습니다.")
    return dict(row)


def own_post(db, post_id, user):
    post = get_post(db, post_id, user)
    if post['author_id'] != user['id']:
        fail(403, "작성자만 수정·삭제할 수 있습니다.")
    return post


def create_app(database_path=ROOT / "storybot.sqlite3"):
    @asynccontextmanager
    async def lifespan(application):
        db = connect(database_path)
        try:
            db.executescript(SCHEMA)
            db.commit()
        finally:
            db.close()
        application.state.tokenizer = BPETokenizer.load_from(ROOT.parent / "storybot/merge_rules.pkl")
        application.state.model = GPT.load_from(ROOT.parent / "storybot/model_pretrain.pt", device=get_device())
        if application.state.model.max_context_len != 256:
            raise RuntimeError("모델 문맥 길이가 확정된 256토큰과 다릅니다.")
        application.state.generation_lock = Lock()
        yield

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.database_path = database_path

    @app.middleware("http")
    async def protect_requests(request: Request, call_next):
        if request.url.path.startswith('/api/') and request.method not in ('GET', 'HEAD', 'OPTIONS'):
            if request.headers.get('X-Storybot-Request') != '1':
                return JSONResponse(status_code=403, content={"detail": {"message": "허용되지 않은 요청입니다."}})
        response = await call_next(request)
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, exc):
        return JSONResponse(status_code=422, content={"detail": {"message": "입력 항목과 길이를 확인해주세요."}})

    @app.exception_handler(sqlite3.Error)
    async def storage_error(request, exc):
        logger.error("데이터 저장소 오류: %s", type(exc).__name__)
        return JSONResponse(status_code=500, content={"detail": {"message": "데이터 처리에 실패했습니다. 다시 시도해주세요."}})

    @app.post('/api/signup', status_code=201)
    def signup(body: Signup, db=Depends(database, scope="function")):
        require_text(body.nickname, '닉네임')
        try:
            db.execute('INSERT INTO users(username,password_hash,nickname) VALUES(?,?,?)',
                       (body.username, password_hash(body.password), body.nickname.strip()))
        except sqlite3.IntegrityError:
            fail(409, '이미 사용 중인 아이디입니다.')
        return {"message": "회원가입이 완료되었습니다. 로그인해주세요."}

    @app.post('/api/login')
    def login(body: Credentials, response: Response, request: Request, db=Depends(database, scope="function")):
        row = db.execute('SELECT * FROM users WHERE username=?', (body.username,)).fetchone()
        if row is None or not valid_password(body.password, row['password_hash']):
            fail(401, '아이디 또는 비밀번호가 올바르지 않습니다.')
        old = request.cookies.get(COOKIE)
        if old:
            db.execute('DELETE FROM sessions WHERE token_hash=?', (token_hash(old),))
        token = secrets.token_urlsafe(32)
        db.execute('INSERT INTO sessions VALUES(?,?,?)', (token_hash(token), row['id'], time.time() + SESSION_SECONDS))
        response.set_cookie(COOKIE, token, max_age=SESSION_SECONDS, httponly=True, samesite='strict',
                            secure=request.url.scheme == 'https')
        return {"id": row['id'], "username": row['username'], "nickname": row['nickname']}

    @app.post('/api/logout')
    def logout(request: Request, response: Response, db=Depends(database, scope="function")):
        token = request.cookies.get(COOKIE)
        if token:
            db.execute('DELETE FROM sessions WHERE token_hash=?', (token_hash(token),))
        response.delete_cookie(COOKIE, httponly=True, samesite='strict')
        return {"message": "로그아웃했습니다."}

    @app.get('/api/me')
    def me(user=Depends(current_user)):
        return {"user": user}

    @app.patch('/api/me')
    def update_me(body: Profile, response: Response, user=Depends(member), db=Depends(database, scope="function")):
        if body.nickname is None and body.new_password is None:
            fail(422, '변경할 정보를 입력해주세요.')
        if body.nickname is not None:
            require_text(body.nickname, '닉네임')
        if body.new_password is not None:
            stored = db.execute('SELECT password_hash FROM users WHERE id=?', (user['id'],)).fetchone()[0]
            if body.current_password is None or not valid_password(body.current_password, stored):
                fail(403, '현재 비밀번호를 확인해주세요.')
            db.execute('UPDATE users SET password_hash=? WHERE id=?', (password_hash(body.new_password), user['id']))
            db.execute('DELETE FROM sessions WHERE user_id=?', (user['id'],))
            response.delete_cookie(COOKIE, httponly=True, samesite='strict')
        if body.nickname is not None:
            db.execute('UPDATE users SET nickname=? WHERE id=?', (body.nickname.strip(), user['id']))
        return {"logged_out": body.new_password is not None}

    @app.post('/api/generate', status_code=201)
    def generate_story(body: Prompt, request: Request, user=Depends(member), db=Depends(database, scope="function")):
        require_text(body.prompt, '이야기의 시작 부분')
        count = len(app.state.tokenizer.encode(body.prompt))
        if count > 128:
            fail(422, f'입력이 {count}토큰입니다. 최대 128토큰까지 입력할 수 있습니다.', input_tokens=count, max_input_tokens=128)
        if not app.state.generation_lock.acquire(blocking=False):
            fail(503, '다른 이야기를 생성 중입니다. 잠시 후 다시 시도해주세요.')
        try:
            result = generate(app.state.model, app.state.tokenizer, body.prompt, max_new_tokens=128, temperature=1.0)
        except Exception:
            logger.exception('스토리 생성 실패')
            fail(500, '스토리 생성에 실패했습니다. 다시 시도해주세요.')
        finally:
            app.state.generation_lock.release()
        if not result.strip():
            fail(500, '생성된 이야기가 없습니다. 시작 부분을 바꿔 다시 시도해주세요.')
        if current_user(request, db) is None:
            fail(401, '로그인이 만료되었습니다. 다시 로그인해주세요.')
        created = time.time()
        cursor = db.execute('INSERT INTO generations(user_id,prompt,content,created_at) VALUES(?,?,?,?)',
                            (user['id'], body.prompt, result, created))
        return {"id": cursor.lastrowid, "prompt": body.prompt, "content": result, "created_at": created, "post_id": None}

    @app.get('/api/history')
    def history(page: int = Query(1, ge=1), user=Depends(member), db=Depends(database, scope="function")):
        rows = db.execute('SELECT g.id,g.prompt,g.content,g.created_at,p.id AS post_id FROM generations g '
                          'LEFT JOIN posts p ON p.generation_id=g.id WHERE g.user_id=? '
                          'ORDER BY g.created_at DESC,g.id DESC LIMIT 10 OFFSET ?', (user['id'], (page - 1) * 10)).fetchall()
        total = db.execute('SELECT COUNT(*) FROM generations WHERE user_id=?', (user['id'],)).fetchone()[0]
        return {"items": [dict(row) for row in rows], "page": page, "total": total}

    @app.get('/api/history/{record_id}')
    def history_item(record_id: int, user=Depends(member), db=Depends(database, scope="function")):
        row = db.execute('SELECT g.id,g.prompt,g.content,g.created_at,p.id AS post_id FROM generations g '
                         'LEFT JOIN posts p ON p.generation_id=g.id WHERE g.id=? AND g.user_id=?',
                         (record_id, user['id'])).fetchone()
        if row is None:
            fail(404, '생성 기록을 찾을 수 없습니다.')
        return dict(row)

    @app.get('/api/posts')
    def posts(page: int = Query(1, ge=1), user=Depends(current_user), db=Depends(database, scope="function")):
        rows = db.execute(POST_SELECT + ' ORDER BY p.created_at DESC,p.id DESC LIMIT 10 OFFSET ?',
                          (user['id'] if user else -1, (page - 1) * 10)).fetchall()
        total = db.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
        return {"items": [dict(row) for row in rows], "page": page, "total": total}

    @app.get('/api/posts/{post_id}')
    def post(post_id: int, user=Depends(current_user), db=Depends(database, scope="function")):
        return get_post(db, post_id, user)

    @app.post('/api/posts', status_code=201)
    def publish(body: NewPost, user=Depends(member), db=Depends(database, scope="function")):
        require_text(body.title, '제목')
        require_text(body.content, '본문')
        row = db.execute('SELECT user_id FROM generations WHERE id=?', (body.generation_id,)).fetchone()
        if row is None:
            fail(404, '생성 기록을 찾을 수 없습니다.')
        if row['user_id'] != user['id']:
            fail(403, '본인의 생성 기록만 게시할 수 있습니다.')
        try:
            cursor = db.execute('INSERT INTO posts(user_id,generation_id,title,content,created_at) VALUES(?,?,?,?,?)',
                                (user['id'], body.generation_id, body.title.strip(), body.content, time.time()))
        except sqlite3.IntegrityError:
            fail(409, '이미 게시한 생성 기록입니다.')
        return get_post(db, cursor.lastrowid, user)

    @app.patch('/api/posts/{post_id}')
    def edit(post_id: int, body: PostText, user=Depends(member), db=Depends(database, scope="function")):
        own_post(db, post_id, user)
        require_text(body.title, '제목')
        require_text(body.content, '본문')
        db.execute('UPDATE posts SET title=?,content=? WHERE id=?', (body.title.strip(), body.content, post_id))
        return get_post(db, post_id, user)

    @app.delete('/api/posts/{post_id}')
    def delete(post_id: int, user=Depends(member), db=Depends(database, scope="function")):
        own_post(db, post_id, user)
        db.execute('DELETE FROM posts WHERE id=?', (post_id,))
        return {"message": "게시물을 삭제했습니다."}

    @app.put('/api/posts/{post_id}/like')
    def like(post_id: int, user=Depends(member), db=Depends(database, scope="function")):
        get_post(db, post_id, user)
        db.execute('INSERT OR IGNORE INTO likes(post_id,user_id) VALUES(?,?)', (post_id, user['id']))
        return get_post(db, post_id, user)

    @app.delete('/api/posts/{post_id}/like')
    def unlike(post_id: int, user=Depends(member), db=Depends(database, scope="function")):
        get_post(db, post_id, user)
        db.execute('DELETE FROM likes WHERE post_id=? AND user_id=?', (post_id, user['id']))
        return get_post(db, post_id, user)

    frontend = ROOT / 'frontend/dist'
    if frontend.is_dir():
        app.mount('/', StaticFiles(directory=frontend, html=True), name='frontend')
    return app


app = create_app()
