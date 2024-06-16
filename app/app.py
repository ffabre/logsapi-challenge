from fastapi import FastAPI
from routers import logs
from routers import health
from sqs import get_sqs_client

app = FastAPI()
app.include_router(logs.router)
app.include_router(health.router)

@app.on_event("startup")
async def init_sqs_on_startup():
    await get_sqs_client()