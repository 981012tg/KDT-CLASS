# 코드봇 웹서비스

FastAPI와 React로 만든 코드 이어쓰기 최소 기능 서비스입니다. 로그인 없이 입력 최대 256토큰, 추가 생성 최대 256토큰으로 동작하며 전체 코드를 표시합니다. 기존 `codebot` 소스와 모델은 변경하지 않습니다.

## 현재 작업 환경에서 실행

프론트엔드 빌드는 완료되어 있습니다. 프로젝트 루트에서 실행합니다. 이미 서버가 실행 중이면 추가 실행하지 않고 아래 주소에 접속합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\codebot_web\start.ps1
```

브라우저에서 http://127.0.0.1:8000 에 접속합니다. 종료는 실행 터미널에서 Ctrl+C를 누릅니다. 이 명령은 로컬에서만 서비스합니다.

현재 환경의 필수 웹 패키지는 `.packages`, Node.js는 `.tools`에 준비되어 있습니다. 화면을 수정한 후에는 다음 명령으로 다시 빌드하고 서버를 재시작합니다.

```powershell
cd codebot_web/frontend
$env:PATH = "$PWD/../.tools/node-v22.14.0-win-x64;$env:PATH"
& ../.tools/node-v22.14.0-win-x64/node.exe ../.tools/node-v22.14.0-win-x64/node_modules/npm/bin/npm-cli.js run build
cd ../..
```

## 새 환경 준비

Python 3.12와 Node.js 22 이상을 준비하고 프로젝트 루트에서 실행합니다.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r codebot_web/requirements.txt
cd codebot_web/frontend
npm install
npm run build
cd ../..
.\.venv\Scripts\python.exe -m uvicorn codebot_web.main:app --host 127.0.0.1 --port 8000
```

개발 중에는 백엔드 실행 후 프론트엔드 폴더에서 `npm run dev`를 실행합니다. Vite가 `/api` 요청을 로컬 백엔드로 전달합니다. 프론트엔드를 다시 빌드하면 백엔드를 재시작합니다.

## API

`POST /api/generate`

요청: `{"code":"def"}`

성공 응답: `{"code":"입력과 생성 내용을 합친 전체 코드"}`

오류 응답은 `{"detail":{"message":"안내 문구"}}` 형식입니다. 입력 초과 시 `detail`에 `input_tokens`, `max_input_tokens`도 포함됩니다.

- 422: 빈 입력, 잘못된 요청, 입력 토큰 초과
- 500: 생성 실패
- 503: 다른 요청을 생성 중; 잠시 후 재시도

생성은 한 번에 한 요청을 처리합니다. 서버는 단일 worker로 실행합니다. 별도 생성 시간 제한은 없으며 종료 토큰 또는 최대 256회 생성에서 끝납니다.

## 검증

프로젝트 루트에서 실행합니다. 실제 모델 생성 1건을 포함합니다.

```powershell
$env:PYTHONPATH = "$PWD/codebot_web/.packages;$PWD"
.\.venv\Scripts\python.exe -m unittest codebot_web.test_app -v
```

화면은 입력 보존, 중복 제출 방지, 오류 안내, 전체 코드 텍스트 표시를 확인합니다. 코드 실행·저장·로그인·모델 설정 기능은 없습니다.

### 수행한 검증

- 백엔드 테스트 7개 통과: 실제 모델 생성, 잘못된 입력, 256·257토큰 경계, 공백·한글, 실패 후 복구, 동시 요청, 문맥 이동 및 종료 토큰.
- React 프로덕션 빌드 성공.
- 실행 서버의 HTML·JS·CSS HTTP 응답 및 실제 모델 생성 API 정상 확인.
- 연결 가능한 브라우저가 없어 화면 클릭과 시각적 검증은 미수행.
