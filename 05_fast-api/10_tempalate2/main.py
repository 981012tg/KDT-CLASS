from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles



app = FastAPI()

# html 렌더링 디렉토리 설정
templates = Jinja2Templates(directory="templates")
# 정적파일 디렉토리 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root(request: Request):
    print(request)
    return templates.TemplateResponse(request, "index.html")

@app.get("/signup")
def read_signup(request: Request):
    return templates.TemplateResponse(request, "signup.html")

@app.get("/introduction")
def read_signup(request: Request):
    return templates.TemplateResponse(request, "introduction.html")