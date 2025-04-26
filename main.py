from typing import Optional
import uuid

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.openapi.utils import status_code_ranges
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, Field, create_engine, Session, select


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    role: str
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    email: str
    password: str
    age: Optional[int] = None


class APIKeys(SQLModel, table=True):
    api_key: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="user.id")
    title: str = Field(nullable=False)


# SQL Model Code to initialize SQLite and create User table. User class used for serialization in CRUD
DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


app = FastAPI()

app.mount("/", StaticFiles(directory="static",html = True), name="static")


# Home Page
@app.get("/test")
async def root():
    return {"message": "Hello World"}


# Create User
@app.post("/users/", response_model=User)
async def create_user(user: User, session: Session = Depends(get_session)):
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# List All User
@app.get("/users/", response_model=list[User])
async def list_all_users(skip: int = 0, limit: int = 10, session: Session = Depends(get_session)):
    users = session.exec(select(User).offset(skip).limit(limit)).all()
    return users


# List User
@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


# Update User
@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user_data: User, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    for field, value in user_data.model_dump().items():
        setattr(user, field, value)

    session.commit()
    session.refresh(user)
    return user

# Delete User
@app.delete("/users/{user_id}", response_model=User)
async def delete_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    session.delete(user)
    session.commit()
    return user


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
