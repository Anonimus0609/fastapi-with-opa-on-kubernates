from fastapi import APIRouter, Path
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/v1", tags=["Admin"])

@router.get("/admin/users/{userName}", response_class=PlainTextResponse)
async def get_users(userName: str = Path(..., description="The name of the user")):
    return f"Hello!! {userName} You have reached the Get Users"

@router.post("/admin/users/{userName}", response_class=PlainTextResponse)
async def update_users(userName: str = Path(..., description="The name of the user")):
    return f"Hello!! {userName} You have access to edits"