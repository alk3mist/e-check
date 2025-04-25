from pydantic import BaseModel


class UserInDB(BaseModel):
    password: str
    username: str
    full_name: str | None = None


fake_users_db: dict[str, dict[str, UserInDB]] = {
    "johndoe": UserInDB.parse_obj(
        {
            "username": "johndoe",
            "full_name": "John Doe",
            "password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        }
    ),
}


class UsernameIsAlreadyTakenError(Exception): ...


def get_by_username(username: str) -> UserInDB | None:
    if username in fake_users_db:
        return fake_users_db[username]
    else:
        return None


def create_user(username: str, full_name: str, password: str) -> UserInDB:
    existing_user = get_by_username(username)
    if existing_user:
        raise UsernameIsAlreadyTakenError(username)
    fake_users_db[username] = UserInDB(
        username=username,
        full_name=full_name,
        password=password,
    )
    return fake_users_db[username]
