# FastAPI with OPA Sidecar - Comprehensive Specification

## 1. Project Overview

This specification outlines the implementation of a FastAPI application with OPA (Open Policy Agent) sidecar for authorization. The application will follow clean code and hexagonal architecture principles, making it maintainable and testable.

## 2. Project Structure

```
fastapi-opa-project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── exceptions.py
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── opa_adapter.py
│   │   └── http_adapter.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── services.py
│   ├── application/
│   │   ├── __init__.py
│   │   ├── use_cases.py
│   │   └── dtos.py
│   └── infrastructure/
│       ├── __init__.py
│       ├── middleware.py
│       └── routes.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── Dockerfile
├── requirements.txt
├── k8s/
│   ├── deployment.yml
│   ├── service.yml
│   └── cm.yml
└── README.md
```

## 3. Core Components

### 3.1 Configuration (app/core/config.py)
```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    OPA_SERVER_URL: str = "http://localhost:8181/v1/data/sample"
    APP_NAME: str = "FastAPI with OPA"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

settings = Settings()
```

### 3.2 OPA Adapter (app/adapters/opa_adapter.py)
```python
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
```

### 3.3 OPA Middleware (app/infrastructure/middleware.py)
```python
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
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
```

### 3.4 Main Application (app/main.py)
```python
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
```

### 3.5 Routes (app/infrastructure/routes.py)
```python
from fastapi import APIRouter, Path
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/v1", tags=["Admin"])

@router.get("/admin/users/{userName}", response_class=PlainTextResponse)
async def get_users(userName: str = Path(..., description="The name of the user")):
    return f"Hello!! {userName} You have reached the Get Users"

@router.post("/admin/users/{userName}", response_class=PlainTextResponse)
async def update_users(userName: str = Path(..., description="The name of the user")):
    return f"Hello!! {userName} You have access to edits"
```

### 3.6 DTOs (app/application/dtos.py)
```python
from pydantic import BaseModel
from typing import Dict, Any

class OPARequest(BaseModel):
    input: Dict[str, Any]

class OPAResponse(BaseModel):
    result: dict
```

## 4. Kubernetes Configuration

### 4.1 Deployment (k8s/deployment.yml)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
spec:
  replicas: 1
  selector:
    matchLabels:
      role: fastapi-app
  template:
    metadata:
      labels:
        role: fastapi-app
    spec:
      containers:
        - name: fastapi-app
          image: fastapi-opa-app:v1
          imagePullPolicy: IfNotPresent
          resources:
            limits:
              memory: 1Gi
          ports:
            - name: http
              containerPort: 8000
          livenessProbe:
            httpGet:
              port: http
              path: /health/liveness
            initialDelaySeconds: 20
            failureThreshold: 20
            periodSeconds: 1
          readinessProbe:
            httpGet:
              port: http
              path: /health/readiness
            initialDelaySeconds: 30
            failureThreshold: 2
            periodSeconds: 1
          env:
            - name: OPA_SERVER_URL
              value: "http://localhost:8181/v1/data/sample"
        - name: opa
          image: openpolicyagent/opa:0.60.0
          ports:
            - name: http
              containerPort: 8181
          args:
            - "run"
            - "--ignore=.*"
            - "--server"
            - "/policies"
          volumeMounts:
            - readOnly: true
              mountPath: /policies
              name: example-policy
          livenessProbe:
            httpGet:
              scheme: HTTP
              port: 8181
            initialDelaySeconds: 5
            periodSeconds: 5
          readinessProbe:
            httpGet:
              path: /health?bundle=true
              scheme: HTTP
              port: 8181
            initialDelaySeconds: 5
            periodSeconds: 5
      volumes:
        - name: example-policy
          configMap:
            name: example-policy
```

### 4.2 Service (k8s/service.yml)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-app
spec:
  type: LoadBalancer
  ports:
    - port: 80
      protocol: TCP
      targetPort: 8000
  selector:
    role: fastapi-app
```

### 4.3 ConfigMap (k8s/cm.yml)
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: example-policy
data:
  admin.rego: |
    package sample

    import future.keywords.if
    import future.keywords.in

    default allow = false

    allow if {
        some i, "admin" in input.path
        some j, "ADMIN_ROLE" in input.roles
        "POST" == input.method
    }

    allow if {
        not "POST" == input.method
    }
```

## 5. Dockerfile
```dockerfile
# Use Python 3.9 as base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 6. Requirements (requirements.txt)
```
fastapi>=0.95.0
httpx>=0.24.0
pydantic>=2.0.0
uvicorn>=0.22.0
```

## 7. Implementation Steps

### Step 1: Create Project Structure
Create all directories and empty files as specified in the project structure.

### Step 2: Implement Core Components
- Implement `app/core/config.py`
- Implement `app/adapters/opa_adapter.py`
- Implement `app/infrastructure/middleware.py`
- Implement `app/main.py`
- Implement `app/infrastructure/routes.py`
- Implement `app/application/dtos.py`

### Step 3: Create Kubernetes Configuration
- Create `k8s/deployment.yml`
- Create `k8s/service.yml`
- Create `k8s/cm.yml`

### Step 4: Create Dockerfile and requirements.txt
- Create `Dockerfile`
- Create `requirements.txt`

### Step 5: Build and Test Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload

# Test endpoints
curl -X GET http://localhost:8000/v1/admin/users/testuser
curl -X POST http://localhost:8000/v1/admin/users/testuser -H "USER_ROLES: ADMIN_ROLE"
```

### Step 6: Deploy to Kubernetes
```bash
# Apply Kubernetes configurations
kubectl apply -f k8s/cm.yml
kubectl apply -f k8s/service.yml
kubectl apply -f k8s/deployment.yml

# Get service external IP
kubectl get services

# Test endpoints using the external IP
curl -X GET http://<EXTERNAL_IP>/v1/admin/users/testuser
curl -X POST http://<EXTERNAL_IP>/v1/admin/users/testuser -H "USER_ROLES: ADMIN_ROLE"
```

## 8. Testing and Validation

### 8.1 Expected Behavior
- GET requests to `/v1/admin/users/{userName}` should always succeed
- POST requests to `/v1/admin/users/{userName}` should succeed only if the `USER_ROLES` header contains "ADMIN_ROLE"
- All other requests should be denied with 401 Unauthorized

### 8.2 Test Cases
1. GET request without roles: Should succeed
2. POST request without roles: Should return 401
3. POST request with ADMIN_ROLE: Should succeed
4. Health endpoints: Should always return 200

## 9. Troubleshooting

### Common Issues:
1. **OPA not responding**: Check if OPA container is running and accessible on port 8181
2. **Permission denied**: Verify the OPA policy is correctly loaded and the roles header is being passed
3. **Connection refused**: Ensure the OPA server URL is correctly configured in the environment variables

### Debugging Tips:
- Check Kubernetes pod logs: `kubectl logs <pod-name> -c opa`
- Verify OPA policy is loaded: `curl http://localhost:8181/v1/policies`
- Test OPA directly: `curl -X POST http://localhost:8181/v1/data/sample -d '{"input": {"path": ["v1", "admin", "users"], "roles": ["ADMIN_ROLE"], "method": "POST"}}'`

This specification provides a complete, self-contained guide for junior developers to implement a FastAPI application with OPA sidecar from scratch, without any dependencies on the existing Spring Boot repository.