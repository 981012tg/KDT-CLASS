from fastapi import FastAPI

app = FastAPI()

quotes = {
    1: "시작이 반이다.",
    2: "실패는 성공의 어머니다.",
    3: "실패는 새로운 시작이다.",
    4: "계획 없는 목표는 그냥 바램에 불과하다.",
    5: "가장 어려운 일은 스스로를 깨끗이 닦는 일이다.",
    6: "네 자신을 믿어라.",
    7: "너 자신이 가장 큰 기적이다.",
    8: "성공은 준비된 사람을 만나게 된다.",
    9: "성공의 비결은 실패를 견뎌내는데 있다.",
    10: "행동은 모든 성공의 기초다."
}

@app.get("/quotes/{word}")
def read_quote(word: int):
 return {
      "word": word,
      "quote": quotes.get(word, "해당 번호의 명언이 없습니다.")
 }