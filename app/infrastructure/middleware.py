from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.adapters.opa_adapter import OPAAdapter
from app.core.config import settings

class OPAMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, opa_adapter: OPAAdapter):
        super().__init__(app)
        self.opa_adapter = opa_adapter

    async def dispatch(self, request: Request, call_next):
        # Skip OPA check for health endpoints
        if request.url.path.startswith("/health"):
            return await call_next(request)

        # Extract roles from header
        roles_header = request.headers.get("USER_ROLES", "")
        roles = roles_header.split(",") if roles_header else []

        # Prepare OPA input
        opa_input = {
            "path": request.url.path.split("/"),
            "roles": roles,
            "method": request.method
        }

        # Check permission
        is_allowed = await self.opa_adapter.check_permission(opa_input)
        
        if not is_allowed:
            return Response(
                content="Unauthorized",
                status_code=401
            )

        return await call_next(request)