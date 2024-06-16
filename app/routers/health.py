from fastapi import APIRouter, status
from pydantic import BaseModel


class HealthCheck(BaseModel):
    status: str


router = APIRouter()


@router.get(
    "/health",
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
async def fargate_healthcheck():
    return HealthCheck(status="ok")
