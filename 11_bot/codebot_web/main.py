import logging
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, StrictStr

from codebot.model import GPT
from codebot.tokenizer import BPETokenizer
from codebot.utils import generate, get_device


ROOT = Path(__file__).resolve().parent.parent
INPUT_LIMIT = 256
GENERATION_LIMIT = 256
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    app.state.tokenizer = BPETokenizer.load_from(ROOT / "codebot/merge_rules.pkl")
    app.state.model = GPT.load_from(
        ROOT / "codebot/model_pretrain.pt", device=get_device()
    )
    if app.state.model.max_context_len != INPUT_LIMIT:
        raise RuntimeError("모델 문맥 길이가 확정된 256토큰과 다릅니다.")
    app.state.generation_lock = Lock()
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: StrictStr


@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": {"message": "code 항목에 코드 문자열만 입력해주세요."}},
    )


@app.post("/api/generate")
def generate_code(body: GenerateRequest):
    if not body.code.strip():
        raise HTTPException(422, detail={"message": "코드를 입력해주세요."})

    input_tokens = len(app.state.tokenizer.encode(body.code))
    if input_tokens > INPUT_LIMIT:
        raise HTTPException(
            422,
            detail={
                "message": f"입력이 {input_tokens}토큰입니다. 최대 256토큰까지 입력할 수 있습니다.",
                "input_tokens": input_tokens,
                "max_input_tokens": INPUT_LIMIT,
            },
        )

    if not app.state.generation_lock.acquire(blocking=False):
        raise HTTPException(
            503, detail={"message": "다른 코드를 생성 중입니다. 잠시 후 다시 시도해주세요."}
        )
    try:
        result = generate(
            app.state.model,
            app.state.tokenizer,
            body.code,
            max_new_tokens=GENERATION_LIMIT,
            temperature=1.0,
        )
        return {"code": result}
    except Exception:
        logger.exception("코드 생성 실패")
        raise HTTPException(
            500, detail={"message": "코드 생성에 실패했습니다. 다시 시도해주세요."}
        ) from None
    finally:
        app.state.generation_lock.release()


FRONTEND = ROOT / "codebot_web/frontend/dist"
if FRONTEND.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
