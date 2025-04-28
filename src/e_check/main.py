from fastapi import FastAPI

from e_check.api import router

app = FastAPI()
app.include_router(router)
