from fastapi import FastAPI
from app.core.config import settings
from app.infrastructure.middleware import OPAMiddleware
from app.adapters.opa_adapter import OPAAdapter

app = FastAPI(title=settings.APP_NAME)

# Initialize OPA adapter
opa_adapter = OPAAdapter(settings.OPA_SERVER_URL)

# Add OPA middleware
app.add_middleware(OPAMiddleware, opa_adapter=opa_adapter)

# Include routes
from app.infrastructure.routes import router
app.include_router(router)

@app.get("/health/liveness")
async def liveness():
    return {"status": "alive"}

@app.get("/health/readiness")
async def readiness():
    return {"status": "ready"}