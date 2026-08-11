from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Union

app = FastAPI()

# class Item(BaseModel):
#     name : str
#     price : float
#     is_offer : bool = None # 이 None의 뜻은, '굳이 안적어도 된다, 필수가 아니다' 라는 뜻

# @app.post("/items/")
# def create_item(item: Item):
#     return {
#         "item": item
#     }

#필드제약 조건
# class Item(BaseModel):
#     name : str = Field(..., title = "Item Name", min_length=2, max_length=50)
#     description : str = Field(None, description = "The description of the item", max_length = 300)
#     price : float = Field(..., gt = 0, description="0보다 커야한다") #gt는 greater than의 약자

# @app.post("/items/")
# def create_item(items: Item):
#     return{
#         "item" : items
#     }

class Item(BaseModel):
    name : str
    tag : List[str]
    variant : Union[int, str]

@app.post("/items/")
def create_item(item: Item):
    return {
        "item" : item
    }