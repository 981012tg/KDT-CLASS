from fastapi import FastAPI, Depends
from sqlalchemy.ext.declarative import declarative_base 
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

Base = declarative_base()
DATABASE_URL = "postgresql://postgres.zubojmhdeleabnvyxihk:W1s26ocmB8VxFqQ0@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres"
engine = create_engine(DATABASE_URL)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String)

class UserCreate(BaseModel):
    username: str
    email: str

def get_db(): 
    db = Session(engine)
    try: 
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {
        "message": "hi fastapi"
    }


@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(username=user.username, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "id": new_user.id, 
        "username": new_user.username, 
        "email": new_user.email
    }

@app.get("/users/{user_id}")
def read_user(user_id: int, db : Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        return {"error" : "사용자를 찾을 수 없습니다."}
    return {
        "id" : db_user.id,
        "username" : db_user.username,
        "email" : db_user.email
    }

class UserUpdate(BaseModel):
    username : Optional[str] = None
    email : Optional[str] = None

@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        return {"error" : "사용자를 찾을 수 없습니다."}

    if user.username is not None:
        db_user.username = user.username

    if user.email is not None:
        db_user.email = user.email

    db.commit()
    db.refresh(db_user)

    return {
        "id" : db_user.id,
        "username" : db_user.username,
        "email": db_user.email
    }

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        return {"error" : "사용자를 찾을 수 없습니다."}

    db.delete(db_user)
    db.commit()
    return {
        "message": "사용자가 성공적으로 삭제되었습니다"
    }