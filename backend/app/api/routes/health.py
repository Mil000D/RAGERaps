"""
Health check endpoints for the RAGERaps API.

These endpoints allow monitoring the health and status of the API.
"""
from fastapi import APIRouter, status

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Check API health",
    response_description="Health status of the API",
    responses={
        200: {
            "description": "API is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "healthy"}
                }
            }
        }
    }
)
async def health_check():
    """
    Check if the API is healthy and operational.

    This endpoint can be used for:
    - Health monitoring
    - Load balancer checks
    - Deployment verification

    Returns a simple JSON object with a status field.
    """
    return {"status": "healthy"}
