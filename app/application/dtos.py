from pydantic import BaseModel
from typing import Dict, Any

class OPARequest(BaseModel):
    input: Dict[str, Any]

class OPAResponse(BaseModel):
    result: dict