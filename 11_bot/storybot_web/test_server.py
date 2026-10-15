"""React 연동 검증용 서버. 실제 서비스 DB 대신 임시 SQLite 파일을 사용한다."""
import os
import tempfile
from pathlib import Path

import uvicorn

from storybot_web.main import ROOT, create_app


if __name__ == '__main__':
    handle, filename = tempfile.mkstemp(prefix='ui-test-', suffix='.sqlite3', dir=ROOT)
    os.close(handle)
    try:
        uvicorn.run(create_app(Path(filename)), host='127.0.0.1', port=18001)
    finally:
        Path(filename).unlink(missing_ok=True)
