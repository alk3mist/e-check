from typing import Any

from pydantic import BaseModel

fake_users_db: dict[str, dict[str, Any]] = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}


class UserInDB(BaseModel):
    hashed_password: str
    username: str
    full_name: str | None = None


def get_by_username(username: str):
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return UserInDB(**user_dict)
