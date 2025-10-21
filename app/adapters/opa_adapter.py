import httpx
from typing import Dict, Any

class OPAAdapter:
    def __init__(self, opa_url: str):
        self.opa_url = opa_url
        self.client = httpx.AsyncClient()

    async def check_permission(self, input_data: Dict[str, Any]) -> bool:
        try:
            response = await self.client.post(
                self.opa_url,
                json={"input": input_data}
            )
            response.raise_for_status()
            result = response.json()
            return result.get("result", {}).get("allow", False)
        except Exception as e:
            raise Exception(f"OPA policy check failed: {str(e)}")