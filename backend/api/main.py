from fastapi import FastAPI
from v1.routes import router

app = FastAPI()

app.include_router(router, prefix="/v1")
