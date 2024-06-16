import datetime
from sqs import send_to_sqs
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional


router = APIRouter()

class LogEntryStatusResponse(BaseModel):
    status: str

class LogEntryRequest(BaseModel):
    timestamp: Optional[datetime.datetime] = None
    message: str
    level: str


@router.post(
    "/log",
    summary="Create a log entry",
    response_description="Status of the log entry creation",
    status_code=201,
    response_model=LogEntryStatusResponse
)
async def create_log_entry(log: LogEntryRequest):
    try:
        await send_to_sqs(log.model_dump_json())
        return LogEntryStatusResponse(status="queued")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
