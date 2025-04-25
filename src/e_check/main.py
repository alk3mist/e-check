import uvicorn
from fastapi import FastAPI

from e_check.api import router

app = FastAPI()
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        # host=settings.APP_HOST,
        # port=settings.APP_PORT,
        reload=True,
        log_config=None,  # we have our own logging initialization
    )  # pragma: no cover
