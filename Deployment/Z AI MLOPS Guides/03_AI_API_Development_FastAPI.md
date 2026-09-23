# AI API Development with FastAPI — The Complete Guide

> "A model without an API is a research paper. A model with a great API is a product."

---

## Table of Contents

1. [Why FastAPI for AI APIs](#1-why-fastapi-for-ai-apis)
2. [FastAPI Fundamentals](#2-fastapi-fundamentals)
3. [Pydantic Schemas — The Foundation](#3-pydantic-schemas--the-foundation)
4. [Path Operations & Routing](#4-path-operations--routing)
5. [Dependency Injection](#5-dependency-injection)
6. [Async/Await in FastAPI](#6-asyncawait-in-fastapi)
7. [Loading ML Models at Startup](#7-loading-ml-models-at-startup)
8. [Request/Response Patterns for ML](#8-requestresponse-patterns-for-ml)
9. [Validation & Error Handling](#9-validation--error-handling)
10. [Authentication & Authorization](#10-authentication--authorization)
11. [Rate Limiting](#11-rate-limiting)
12. [Caching & Performance](#12-caching--performance)
13. [Background Tasks & Queues](#13-background-tasks--queues)
14. [Streaming & Server-Sent Events](#14-streaming--server-sent-events)
15. [WebSocket Endpoints](#15-websocket-endpoints)
16. [Testing FastAPI](#16-testing-fastapi)
17. [Observability — Logging, Metrics, Tracing](#17-observability--logging-metrics-tracing)
18. [Production Deployment Patterns](#18-production-deployment-patterns)
19. [LLM-Specific Patterns](#19-llm-specific-patterns)
20. [Putting It All Together — Full Example](#20-putting-it-all-together--full-example)
21. [Summary & Next Steps](#21-summary--next-steps)

---

## 1. Why FastAPI for AI APIs

FastAPI has become the **default** for AI/ML API development. Here's why:

### Pros
- **Async-first** — handles thousands of concurrent requests, critical for LLM streaming.
- **Type hints** → automatic validation, serialization, OpenAPI docs.
- **Pydantic** — type-safe schemas, perfect for ML inputs/outputs.
- **Fast** — on par with Node.js/Go, faster than Flask/Django.
- **Easy** — Flask-like simplicity, modern Python.
- **Auto docs** — Swagger UI at `/docs`, ReDoc at `/redoc`. Free client for testing.
- **Starlette under the hood** — battle-tested ASGI framework.

### When NOT to use FastAPI
- You need Django-level admin/batteries → use Django REST Framework.
- You need RPC semantics → use gRPC directly.
- You're serving models with strict latency needs (< 5ms) → use Triton / TensorRT.

### FastAPI vs Alternatives

| Framework | Speed | DX | ML Fit | Notes |
|-----------|-------|-----|--------|-------|
| FastAPI | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Best all-around |
| Flask | ⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Sync only, no auto docs |
| Django REST | ⚡ | ⭐⭐⭐ | ⭐⭐ | Heavy, batteries-included |
| Sanic | ⚡⚡⚡⚡ | ⭐⭐⭐ | ⭐⭐⭐ | Less popular |
| Litestar | ⚡⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Rising alternative |
| BentoML | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Built specifically for ML |

**Recommendation:** Use FastAPI as your primary. Use BentoML when you want built-in model serving + registry integration.

---

## 2. FastAPI Fundamentals

### Hello World

```python
# main.py
from fastapi import FastAPI

app = FastAPI(
    title="My AI API",
    description="Serving ML models to the world.",
    version="1.0.0",
)

@app.get("/")
def root():
    return {"message": "Hello, AI!"}

@app.get("/health")
def health():
    return {"status": "ok"}
```

Run it:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open:
- `http://localhost:8000/` → `{"message": "Hello, AI!"}`
- `http://localhost:8000/docs` → interactive Swagger UI
- `http://localhost:8000/redoc` → ReDoc documentation

### The Lifecycle of a Request

```
1. Client sends HTTP request
2. ASGI server (uvicorn) receives it
3. Starlette routes it to the right path operation
4. FastAPI runs dependency injection (Depends)
5. FastAPI validates input against Pydantic schema
6. Your function runs (async or sync)
7. FastAPI validates output against response_model
8. FastAPI serializes result to JSON
9. ASGI server sends response back
```

Every step has hooks where you can intercept, validate, log, etc.

### ASGI vs WSGI

- **WSGI** (Flask, Django old): synchronous, one request per worker.
- **ASGI** (FastAPI, modern Django): asynchronous, many concurrent requests per worker.

For ML, ASGI is critical — you can have a model inference in flight while serving other requests.

---

## 3. Pydantic Schemas — The Foundation

Pydantic is **the most important thing to master** in FastAPI. Bad schemas = bad API.

### Basic Schemas

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from enum import Enum
from datetime import datetime

class CustomerFeatures(BaseModel):
    """Input features for churn prediction."""
    customer_id: str = Field(..., description="Unique customer identifier")
    age: int = Field(..., ge=18, le=120, description="Customer age in years")
    monthly_spend: float = Field(..., ge=0, description="Average monthly spend in USD")
    tenure_months: int = Field(..., ge=0, description="Months since signup")
    support_tickets: int = Field(0, ge=0, description="Support tickets in last 90 days")
    plan_type: Literal["free", "basic", "pro", "enterprise"]

    @field_validator("monthly_spend")
    @classmethod
    def spend_must_be_reasonable(cls, v):
        if v > 1_000_000:
            raise ValueError("monthly_spend unrealistically high")
        return v

class ChurnPrediction(BaseModel):
    """Output of churn prediction."""
    customer_id: str
    churn_probability: float = Field(..., ge=0, le=1)
    will_churn: bool
    risk_factors: list[str]
    model_version: str
    predicted_at: datetime
```

### Nested Models

```python
class Address(BaseModel):
    street: str
    city: str
    country: str

class Customer(BaseModel):
    id: str
    name: str
    address: Address
    billing_address: Optional[Address] = None  # optional nested

# This automatically accepts/validates nested JSON:
# {
#   "id": "c123",
#   "name": "Alice",
#   "address": {"street": "1 Main", "city": "NYC", "country": "US"}
# }
```

### Custom Types with Enums

```python
class ModelName(str, Enum):
    XGBOOST = "xgboost"
    RANDOM_FOREST = "random_forest"
    LOGISTIC = "logistic"

class PredictionRequest(BaseModel):
    model: ModelName = ModelName.XGBOOST
    features: dict[str, float]
```

### Generic Responses

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    error: Optional[str] = None
    timestamp: datetime

# Usage:
class UserOut(BaseModel):
    id: str
    name: str

@app.get("/users/{id}", response_model=APIResponse[UserOut])
def get_user(id: str):
    return APIResponse(data=UserOut(id=id, name="Alice"))
```

### Pydantic v2 Tips

Pydantic v2 is 5-50x faster than v1. Some key differences:

```python
# v1 style (deprecated)
class M(BaseModel):
    x: int
    
    @validator("x")
    def check_x(cls, v):
        return v

    class Config:
        orm_mode = True

# v2 style (current)
class M(BaseModel):
    x: int
    
    @field_validator("x")
    @classmethod
    def check_x(cls, v):
        return v

    model_config = {"from_attributes": True}  # was orm_mode
```

---

## 4. Path Operations & Routing

### All the Decorators

```python
from fastapi import FastAPI, HTTPException, Query, Path, Body, Header

app = FastAPI()

@app.get("/items/{item_id}")
def get_item(item_id: int = Path(..., ge=1)):  # path param validation
    return {"id": item_id}

@app.get("/search")
def search(
    q: str = Query(..., min_length=3, max_length=100),  # query param
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return {"q": q, "limit": limit, "offset": offset}

@app.post("/items")
def create_item(item: Item = Body(...)):  # request body
    return item

@app.patch("/items/{id}")
def patch_item(id: int, updates: dict = Body(...)):
    return {"id": id, "updates": updates}

@app.delete("/items/{id}")
def delete_item(id: int):
    return {"deleted": id}
```

### APIRouter — Organizing Endpoints

For non-trivial apps, use `APIRouter` to split routes into modules.

```python
# routers/predictions.py
from fastapi import APIRouter, Depends
from typing import List

router = APIRouter(prefix="/predictions", tags=["predictions"])

@router.post("/churn")
def predict_churn(features: CustomerFeatures):
    ...

@router.post("/churn/batch")
def predict_churn_batch(features: List[CustomerFeatures]):
    ...

@router.get("/history/{customer_id}")
def get_history(customer_id: str):
    ...
```

```python
# routers/health.py
from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    return {"status": "ok"}
```

```python
# main.py
from fastapi import FastAPI
from routers import predictions, health

app = FastAPI()
app.include_router(health.router)
app.include_router(predictions.router)
```

### Tags & OpenAPI Metadata

```python
@app.post(
    "/predict",
    tags=["Inference"],
    summary="Predict churn probability",
    description="Returns the probability that the customer will churn in next 30 days.",
    response_model=ChurnPrediction,
    responses={
        200: {"description": "Successful prediction"},
        422: {"description": "Validation error"},
        429: {"description": "Rate limit exceeded"},
    },
)
def predict(features: CustomerFeatures):
    ...
```

---

## 5. Dependency Injection

FastAPI's `Depends()` is magic. Use it heavily.

### Basic Dependency

```python
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/{id}")
def get_user(id: int, db: Session = Depends(get_db)):
    return db.query(User).filter(User.id == id).first()
```

### Model Loader as Dependency

```python
def get_model():
    """Load model once, share across requests."""
    if not hasattr(get_model, "_model"):
        get_model._model = load_model("models/model.pkl")
    return get_model._model

@app.post("/predict")
def predict(features: CustomerFeatures, model = Depends(get_model)):
    return model.predict_proba([list(features.dict().values())])[0]
```

### Auth as Dependency

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

VALID_KEYS = {"abc123", "xyz789"}

def validate_api_key(api_key: str = Security(api_key_header)):
    if api_key not in VALID_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.post("/predict", dependencies=[Depends(validate_api_key)])
def predict(features: CustomerFeatures):
    ...
```

### Dependencies with Yield (Setup/Teardown)

```python
def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

### Class-based Dependencies

```python
class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.cache = {}

    def __call__(self, api_key: str = Security(api_key_header)):
        now = time.time()
        window = 60
        if api_key not in self.cache:
            self.cache[api_key] = []
        # Drop old timestamps
        self.cache[api_key] = [t for t in self.cache[api_key] if now - t < window]
        if len(self.cache[api_key]) >= self.rpm:
            raise HTTPException(429, "Rate limit exceeded")
        self.cache[api_key].append(now)
        return True

limiter = RateLimiter(requests_per_minute=100)

@app.post("/predict", dependencies=[Depends(limiter)])
def predict(...): ...
```

### Global Dependencies

```python
app = FastAPI(dependencies=[Depends(validate_api_key)])
# All endpoints now require API key
```

---

## 6. Async/Await in FastAPI

### When to Use `async def` vs `def`

| Function does | Use |
|---|---|
| Pure CPU work (math, dict ops) | `def` |
| Sync I/O (sync DB, sync file) | `def` (FastAPI runs in threadpool) |
| Async I/O (async DB, HTTPX async) | `async def` |
| CPU-heavy (model inference) | `def` OR `async def` + `run_in_executor` |

### Blocking the Event Loop — The #1 Mistake

```python
# BAD — blocks event loop, all other requests wait
@app.post("/predict")
async def predict(features: CustomerFeatures):
    result = heavy_model.predict(features)  # synchronous, 2 seconds
    return result

# GOOD — runs in threadpool, event loop free
@app.post("/predict")
def predict(features: CustomerFeatures):  # NOTE: def, not async def
    result = heavy_model.predict(features)
    return result

# ALSO GOOD — explicit threadpool
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

@app.post("/predict")
async def predict(features: CustomerFeatures):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, heavy_model.predict, features)
    return result
```

### Async Database Example (SQLAlchemy 2.0 async)

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

engine = create_async_engine("postgresql+asyncpg://user:pass@host/db")
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/users/{id}")
async def get_user(id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, id)
    if not user:
        raise HTTPException(404, "User not found")
    return user
```

### Async HTTP Client

```python
import httpx

@app.get("/enriched_user/{id}")
async def get_enriched_user(id: int):
    async with httpx.AsyncClient() as client:
        # Call two APIs in parallel
        user_resp, billing_resp = await asyncio.gather(
            client.get(f"https://users.example.com/{id}"),
            client.get(f"https://billing.example.com/{id}"),
        )
    return {
        "user": user_resp.json(),
        "billing": billing_resp.json(),
    }
```

---

## 7. Loading ML Models at Startup

**The #1 performance mistake:** loading the model inside the request handler.

```python
# TERRIBLE — loads model on EVERY request
@app.post("/predict")
def predict(features: CustomerFeatures):
    model = joblib.load("model.pkl")  # 500ms wasted per request
    return model.predict([features])

# GOOD — load once at startup
from contextlib import asynccontextmanager

ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load models at startup
    ml_models["churn"] = joblib.load("models/churn_v2.pkl")
    ml_models["recommendation"] = joblib.load("models/reco_v1.pkl")
    print(f"Loaded {len(ml_models)} models")
    yield
    # Cleanup at shutdown
    ml_models.clear()

app = FastAPI(lifespan=lifespan)

@app.post("/predict")
def predict(features: CustomerFeatures):
    model = ml_models["churn"]
    return {"prediction": model.predict_proba([list(features.dict().values())])[0].tolist()}
```

### Multiple Models, Multiple Versions

```python
ml_models = {}  # name -> {version -> model}

@asynccontextmanager
async def lifespan(app: FastAPI):
    ml_models["churn"] = {
        "v1": joblib.load("models/churn_v1.pkl"),
        "v2": joblib.load("models/churn_v2.pkl"),
    }
    yield
    ml_models.clear()

@app.post("/predict/{version}")
def predict(features: CustomerFeatures, version: str = "v2"):
    if version not in ml_models["churn"]:
        raise HTTPException(404, f"Version {version} not found")
    model = ml_models["churn"][version]
    return {"prediction": model.predict([list(features.dict().values())])[0].tolist()}
```

### Loading from MLflow Registry

```python
import mlflow.sklearn

@asynccontextmanager
async def lifespan(app: FastAPI):
    mlflow.set_tracking_uri("http://mlflow:5000")
    ml_models["churn"] = mlflow.sklearn.load_model(
        "models:/churn-prediction/Production"
    )
    yield
```

### Hot-Reloading Models

For zero-downtime model updates:

```python
import threading
import time

class ModelRegistry:
    def __init__(self):
        self.models = {}
        self.lock = threading.Lock()
        self._start_background_refresher()

    def get(self, name):
        with self.lock:
            return self.models.get(name)

    def refresh(self):
        # Pull latest Production model from MLflow
        new_model = mlflow.sklearn.load_model("models:/churn-prediction/Production")
        with self.lock:
            self.models["churn"] = new_model
        print("Refreshed churn model")

    def _start_background_refresher(self):
        def worker():
            while True:
                time.sleep(3600)  # every hour
                try:
                    self.refresh()
                except Exception as e:
                    print(f"Refresh failed: {e}")
        t = threading.Thread(target=worker, daemon=True)
        t.start()

registry = ModelRegistry()

@asynccontextmanager
async def lifespan(app: FastAPI):
    registry.refresh()
    yield

@app.post("/predict")
def predict(features: CustomerFeatures):
    model = registry.get("churn")
    if model is None:
        raise HTTPException(503, "Model not loaded")
    return model.predict([list(features.dict().values())])[0].tolist()
```

---

## 8. Request/Response Patterns for ML

### Pattern 1: Single Prediction

```python
class PredictRequest(BaseModel):
    features: CustomerFeatures

class PredictResponse(BaseModel):
    prediction: float
    confidence: float
    model_version: str

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    model = ml_models["churn"]
    proba = model.predict_proba([list(req.features.dict().values())])[0][1]
    return PredictResponse(
        prediction=proba,
        confidence=abs(proba - 0.5) * 2,
        model_version="v2.3",
    )
```

### Pattern 2: Batch Prediction

```python
class BatchPredictRequest(BaseModel):
    items: List[CustomerFeatures] = Field(..., max_length=1000)  # cap batch size

class BatchPredictResponse(BaseModel):
    predictions: List[PredictResponse]
    count: int
    processing_time_ms: float

@app.post("/predict/batch", response_model=BatchPredictResponse)
def predict_batch(req: BatchPredictRequest):
    start = time.perf_counter()
    model = ml_models["churn"]
    X = [list(item.dict().values()) for item in req.items]
    probas = model.predict_proba(X)[:, 1]
    
    preds = [
        PredictResponse(prediction=p, confidence=abs(p - 0.5) * 2, model_version="v2.3")
        for p in probas
    ]
    elapsed = (time.perf_counter() - start) * 1000
    return BatchPredictResponse(predictions=preds, count=len(preds), processing_time_ms=elapsed)
```

### Pattern 3: File Upload (Image/Audio)

```python
from fastapi import UploadFile, File
import io
from PIL import Image

@app.post("/predict/image")
async def predict_image(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(400, "Only JPEG/PNG allowed")
    
    contents = await file.read()
    if len(contents) > 10_000_000:  # 10MB limit
        raise HTTPException(413, "File too large")
    
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    # Preprocess + predict
    tensor = preprocess(image)
    prediction = image_model(tensor.unsqueeze(0))
    return {"class": prediction}
```

### Pattern 4: Async Job (Long-running Inference)

```python
import uuid
from fastapi import BackgroundTasks

# In-memory job store (use Redis in production)
jobs: dict[str, dict] = {}

@app.post("/predict/async")
async def predict_async(req: BatchPredictRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "pending", "result": None}
    
    # Schedule actual work
    background_tasks.add_task(run_batch_inference, job_id, req)
    
    return {"job_id": job_id, "status": "pending", "poll_url": f"/jobs/{job_id}"}

def run_batch_inference(job_id: str, req: BatchPredictRequest):
    try:
        jobs[job_id]["status"] = "processing"
        # ... heavy inference ...
        jobs[job_id]["result"] = {"predictions": [...]}
        jobs[job_id]["status"] = "completed"
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    return jobs[job_id]
```

### Pattern 5: Streaming Predictions (LLM Token Stream)

```python
from fastapi.responses import StreamingResponse
import asyncio

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def event_generator():
        async for token in llm_stream(req.prompt):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

## 9. Validation & Error Handling

### Custom Exception Handlers

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

class ModelNotLoadedError(Exception):
    pass

class PredictionTimeoutError(Exception):
    pass

@app.exception_handler(ModelNotLoadedError)
async def model_not_loaded_handler(request: Request, exc: ModelNotLoadedError):
    return JSONResponse(
        status_code=503,
        content={"error": "MODEL_NOT_LOADED", "message": str(exc)},
    )

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "details": exc.errors(),
            "body": exc.body,
        },
    )

@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception):
    # Log full traceback for internal debugging
    logger.exception("Unhandled error")
    # Return sanitized message to user
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
    )
```

### Status Codes — Use Them Right

| Code | When |
|------|------|
| 200 OK | Successful GET/POST |
| 201 Created | Resource created |
| 204 No Content | Successful DELETE |
| 400 Bad Request | Malformed request |
| 401 Unauthorized | Missing/invalid auth |
| 403 Forbidden | Authenticated but no permission |
| 404 Not Found | Resource doesn't exist |
| 422 Unprocessable Entity | Validation failed |
| 429 Too Many Requests | Rate limited |
| 500 Internal Server Error | Bug in your code |
| 502 Bad Gateway | Upstream service failed |
| 503 Service Unavailable | Model not loaded / overloaded |
| 504 Gateway Timeout | Inference timed out |

### Standardized Error Response

```python
class ErrorResponse(BaseModel):
    error: str  # machine-readable code
    message: str  # human-readable
    details: Optional[dict] = None
    request_id: str

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

---

## 10. Authentication & Authorization

### API Key Auth (Simplest)

```python
from fastapi import Security
from fastapi.security import APIKeyHeader, APIKeyQuery

api_key_header = APIKeyHeader(name="X-API-Key")
api_key_query = APIKeyQuery(name="api_key")

# In production, store hashed in DB
API_KEYS = {
    "client_a_123": {"name": "Client A", "rate_limit": 100, "tier": "free"},
    "client_b_456": {"name": "Client B", "rate_limit": 1000, "tier": "pro"},
}

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key not in API_KEYS:
        raise HTTPException(403, "Invalid API key")
    return API_KEYS[api_key]

@app.post("/predict")
async def predict(req: PredictRequest, client = Depends(get_api_key)):
    return {"prediction": ..., "client": client["name"]}
```

### JWT Auth

```python
from datetime import datetime, timedelta
import jwt
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

SECRET = "your-secret-key"
ALGORITHM = "HS256"
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2 = OAuth2PasswordBearer(tokenUrl="token")

def create_token(data: dict, expires_minutes: int = 60):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=expires_minutes)
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

async def current_user(token: str = Depends(oauth2)):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

@app.post("/token")
async def login(username: str, password: str):
    # verify against DB...
    user = verify_user(username, password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    token = create_token({"sub": user.id, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/me")
async def me(user = Depends(current_user)):
    return user
```

### Role-Based Access Control

```python
def require_role(role: str):
    async def checker(user = Depends(current_user)):
        if user.get("role") != role:
            raise HTTPException(403, f"Requires role: {role}")
        return user
    return checker

@app.delete("/models/{name}")
async def delete_model(name: str, user = Depends(require_role("admin"))):
    ...
```

### OAuth2 with External Provider (Google example)

```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name="google",
    client_id="...",
    client_secret="...",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@app.get("/login/google")
async def login_google(request: Request):
    redirect_uri = request.url_for("auth_google")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/google")
async def auth_google(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user = token.get("userinfo")
    # Create session / JWT
    ...
```

---

## 11. Rate Limiting

### In-Memory Rate Limiter (Simple)

```python
import time
from collections import defaultdict
from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")
request_log: dict[str, list[float]] = defaultdict(list)

def rate_limit(requests_per_minute: int):
    def dep(api_key: str = Security(api_key_header)):
        now = time.time()
        window = 60
        # Drop old
        request_log[api_key] = [t for t in request_log[api_key] if now - t < window]
        if len(request_log[api_key]) >= requests_per_minute:
            raise HTTPException(
                429,
                detail=f"Rate limit exceeded: {requests_per_minute}/min",
                headers={"Retry-After": str(int(window - (now - request_log[api_key][0])))},
            )
        request_log[api_key].append(now)
        return api_key
    return dep

@app.post("/predict", dependencies=[Depends(rate_limit(60))])
def predict(...): ...
```

### Redis-Based Rate Limiter (Distributed, Production-Grade)

```python
import redis.asyncio as redis
from fastapi import Request

redis_client = redis.from_url("redis://redis:6379")

async def redis_rate_limit(request: Request, api_key: str):
    key = f"rate:{api_key}:{int(time.time() // 60)}"
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, 60)
    count, _ = await pipe.execute()
    
    if count > 100:
        raise HTTPException(429, "Rate limit exceeded", headers={"Retry-After": "60"})
    return True

@app.post("/predict")
async def predict(req: PredictRequest, request: Request, api_key: str = Security(api_key_header)):
    await redis_rate_limit(request, api_key)
    ...
```

### Sliding Window with Lua Script (Most Accurate)

```lua
-- rate_limit.lua
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

-- Clear old entries
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

-- Count current
local count = redis.call('ZCARD', key)
if count >= limit then
    return 0
end

-- Add current request
redis.call('ZADD', key, now, now .. math.random())
redis.call('EXPIRE', key, window)
return 1
```

```python
import aioredis

with open("rate_limit.lua") as f:
    rate_limit_script = f.read()

async def sliding_window_rate_limit(api_key: str, limit: int = 100, window: int = 60):
    redis = await aioredis.from_url("redis://redis:6379")
    key = f"rate:{api_key}"
    now = int(time.time() * 1000)
    allowed = await redis.eval(rate_limit_script, 1, key, limit, window, now)
    if not allowed:
        raise HTTPException(429, "Rate limit exceeded")
```

### Using `slowapi` Library (Easier)

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/predict")
@limiter.limit("60/minute")
def predict(request: Request, req: PredictRequest):
    ...
```

---

## 12. Caching & Performance

### Response Caching

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
import redis.asyncio as redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = redis.from_url("redis://redis:6379")
    FastAPICache.init(RedisBackend(redis_client), prefix="api-cache")
    yield

@app.post("/predict")
@cache(expire=300)  # cache for 5 min
async def predict(req: PredictRequest):
    # Expensive operation
    return {"prediction": ...}
```

### Feature Caching (Predict-Specific)

```python
import functools

@functools.lru_cache(maxsize=10_000)
def cached_feature_lookup(customer_id: str):
    # Expensive DB call
    return db.get_customer_features(customer_id)

@app.post("/predict")
def predict(req: PredictRequest):
    features = cached_feature_lookup(req.customer_id)
    ...
```

### Model Output Caching

For deterministic models, cache (input_hash → output):

```python
import hashlib
import json

async def cached_predict(features: CustomerFeatures, redis):
    input_hash = hashlib.sha256(
        json.dumps(features.dict(), sort_keys=True).encode()
    ).hexdigest()
    
    cached = await redis.get(f"pred:{input_hash}")
    if cached:
        return json.loads(cached)
    
    result = expensive_predict(features)
    await redis.setex(f"pred:{input_hash}", 3600, json.dumps(result))
    return result
```

### Response Compression

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Connection Pooling

```python
import httpx

# Create once at startup, share across requests
http_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        timeout=httpx.Timeout(30.0),
    )
    yield
    await http_client.aclose()
```

---

## 13. Background Tasks & Queues

### FastAPI BackgroundTasks (Lightweight)

```python
from fastapi import BackgroundTasks

@app.post("/predict/notify")
async def predict_and_notify(req: PredictRequest, bg: BackgroundTasks):
    result = predict(req)
    # Send notification after response sent
    bg.add_task(send_slack_notification, req.customer_id, result)
    return result

async def send_slack_notification(customer_id, result):
    # Non-blocking — runs after response sent
    await httpx.post("https://slack.com/...", json={...})
```

### Celery for Heavy Async Jobs

```python
# worker.py
from celery import Celery
import time

celery = Celery("worker", broker="redis://redis:6379", backend="redis://redis:6379")

@celery.task
def heavy_inference(job_id, features):
    # ... long running ...
    return {"prediction": 0.87}
```

```python
# main.py
from worker import celery

@app.post("/predict/async")
async def predict_async(req: PredictRequest):
    task = heavy_inference.delay(req.customer_id, req.features)
    return {"task_id": task.id, "status_url": f"/tasks/{task.id}"}

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    result = celery.AsyncResult(task_id)
    return {
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
```

### When to Use What

| Scenario | Tool |
|---|---|
| Quick post-response work (email, log) | FastAPI BackgroundTasks |
| Long-running inference | Celery + Redis/RabbitMQ |
| Streaming work | Kafka + Faust |
| Cron jobs | APScheduler, Celery Beat |
| Distributed compute | Ray, Dask |

---

## 14. Streaming & Server-Sent Events

Critical for LLM APIs. Users want to see tokens as they're generated, not wait 10 seconds for a full response.

### SSE Endpoint

```python
from fastapi.responses import StreamingResponse
import asyncio
import json

async def generate_tokens(prompt: str):
    """Simulate token-by-token LLM generation."""
    tokens = prompt.split() + ["END"]
    for token in tokens:
        await asyncio.sleep(0.1)  # simulate latency
        yield token

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def event_stream():
        try:
            async for token in generate_tokens(req.prompt):
                # SSE format: "data: <payload>\n\n"
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )
```

### Client Side (JavaScript)

```javascript
const response = await fetch("/chat/stream", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({prompt: "Hello world"}),
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const {done, value} = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split("\n");
    for (const line of lines) {
        if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") return;
            const event = JSON.parse(data);
            console.log(event.token);
        }
    }
}
```

### Streaming with Real LLM (OpenAI-compatible)

```python
import httpx

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def event_stream():
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": req.prompt}],
                    "stream": True,
                },
                headers={"Authorization": f"Bearer {OPENAI_KEY}"},
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield line + "\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

---

## 15. WebSocket Endpoints

For bidirectional real-time (chat apps, multiplayer, live dashboards).

```python
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            message = await ws.receive_text()
            # Echo back with a "prediction"
            response = await process_message(message)
            await ws.send_json({"input": message, "response": response})
    except WebSocketDisconnect:
        print("Client disconnected")

async def process_message(message: str):
    # Simulate inference
    await asyncio.sleep(0.1)
    return f"Processed: {message.upper()}"
```

### WebSocket with Multiple Clients (Broadcast)

```python
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: str):
        for ws in self.active:
            await ws.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/live")
async def ws_live(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            await manager.broadcast(f"Broadcast: {data}")
    except WebSocketDisconnect:
        manager.disconnect(ws)
```

---

## 16. Testing FastAPI

### Using TestClient

```python
from fastapi.testclient import TestClient
import pytest

client = TestClient(app)

def test_predict():
    response = client.post(
        "/predict",
        json={
            "customer_id": "c123",
            "age": 35,
            "monthly_spend": 100.0,
            "tenure_months": 12,
            "support_tickets": 2,
            "plan_type": "pro",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert 0 <= data["prediction"] <= 1

def test_predict_invalid_input():
    response = client.post(
        "/predict",
        json={
            "customer_id": "c123",
            "age": 200,  # invalid
            "monthly_spend": 100.0,
            "tenure_months": 12,
            "support_tickets": 2,
            "plan_type": "pro",
        },
    )
    assert response.status_code == 422

def test_missing_api_key():
    response = client.post("/predict", json={...})
    assert response.status_code == 403

def test_with_api_key():
    response = client.post(
        "/predict",
        json={...},
        headers={"X-API-Key": "abc123"},
    )
    assert response.status_code == 200
```

### Fixtures for DB, Models, etc.

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def mock_model():
    class MockModel:
        def predict_proba(self, X):
            return [[0.3, 0.7]] * len(X)
    return MockModel()

@pytest.fixture
def app_with_mock_model(mock_model):
    ml_models["churn"] = mock_model
    yield
    ml_models.pop("churn", None)
```

### Async Tests

```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_async_predict():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/predict", json={...})
    assert response.status_code == 200
```

### Load Testing with Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(0.5, 2)
    
    def on_start(self):
        self.client.headers = {"X-API-Key": "abc123"}
    
    @task(3)
    def predict(self):
        self.client.post("/predict", json={
            "customer_id": "c123",
            "age": 35,
            "monthly_spend": 100.0,
            "tenure_months": 12,
            "support_tickets": 2,
            "plan_type": "pro",
        })
    
    @task(1)
    def health(self):
        self.client.get("/health")
```

```bash
locust -f locustfile.py --host=http://localhost:8000
# Open http://localhost:8089 to control the test
```

---

## 17. Observability — Logging, Metrics, Tracing

### Structured Logging

```python
import structlog
import logging

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
logger = structlog.get_logger()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.time()
    
    response = await call_next(request)
    
    duration_ms = (time.time() - start) * 1000
    logger.info(
        "request",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration_ms,
    )
    response.headers["X-Request-ID"] = request_id
    return response

@app.post("/predict")
def predict(req: PredictRequest):
    logger.info("prediction_request", customer_id=req.customer_id, plan_type=req.plan_type)
    try:
        result = run_model(req)
        logger.info("prediction_success", customer_id=req.customer_id, proba=result.proba)
        return result
    except Exception as e:
        logger.exception("prediction_failed", customer_id=req.customer_id, error=str(e))
        raise
```

### Prometheus Metrics

```python
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram

# Auto-instrument: request count, latency, status codes
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Custom metrics
PREDICTION_COUNT = Counter(
    "predictions_total", "Total predictions made", ["model", "plan_type"]
)
PREDICTION_LATENCY = Histogram(
    "prediction_latency_seconds", "Time spent predicting", ["model"]
)
PREDICTION_VALUE = Histogram(
    "prediction_value", "Distribution of predicted probabilities",
    buckets=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

@app.post("/predict")
def predict(req: PredictRequest):
    start = time.time()
    with PREDICTION_LATENCY.labels(model="churn-v2").time():
        result = run_model(req)
    PREDICTION_COUNT.labels(model="churn-v2", plan_type=req.plan_type).inc()
    PREDICTION_VALUE.observe(result.proba)
    return result
```

### Distributed Tracing with OpenTelemetry

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://jaeger:4317"))
)

FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()

tracer = trace.get_tracer(__name__)

@app.post("/predict")
def predict(req: PredictRequest):
    with tracer.start_as_current_span("predict") as span:
        span.set_attribute("customer.id", req.customer_id)
        with tracer.start_as_current_span("feature_lookup"):
            features = lookup_features(req.customer_id)
        with tracer.start_as_current_span("model_inference"):
            result = model.predict([features])
        span.set_attribute("prediction.value", float(result[0]))
        return {"prediction": result[0]}
```

### Health & Readiness Probes

```python
@app.get("/health/live")
def liveness():
    """Is the process alive?"""
    return {"status": "alive"}

@app.get("/health/ready")
def readiness():
    """Is the service ready to serve traffic?"""
    if "churn" not in ml_models:
        raise HTTPException(503, "Model not loaded")
    return {"status": "ready", "models": list(ml_models.keys())}
```

Kubernetes uses these for liveness/readiness probes.

---

## 18. Production Deployment Patterns

### With Gunicorn + Uvicorn Workers

```bash
gunicorn main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --graceful-timeout 30 \
    --access-logfile - \
    --error-logfile -
```

- `-w 4`: 4 worker processes (rule of thumb: 2-4 × CPU cores)
- `-k uvicorn.workers.UvicornWorker`: ASGI worker
- `--timeout`: kill request after 120s
- `--graceful-timeout`: give 30s for in-flight requests on shutdown

### Behind Nginx

```nginx
upstream fastapi_backend {
    server api1:8000;
    server api2:8000;
}

server {
    listen 80;
    server_name api.example.com;
    
    location / {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # For SSE/WebSocket
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_buffering off;  # critical for SSE
        proxy_read_timeout 300s;
    }
}
```

### With Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system deps (for some ML libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Pre-download model at build time
RUN python -c "from model_utils import download_model; download_model()"

# Run as non-root
RUN useradd -m -u 1000 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120"]
```

### With Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: churn-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: churn-api
  template:
    metadata:
      labels:
        app: churn-api
    spec:
      containers:
      - name: api
        image: myuser/churn-api:v2.3
        ports:
        - containerPort: 8000
        env:
        - name: MLFLOW_TRACKING_URI
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: mlflow-uri
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1000m
            memory: 2Gi
        livenessProbe:
          httpGet: { path: /health/live, port: 8000 }
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet: { path: /health/ready, port: 8000 }
          initialDelaySeconds: 30
          periodSeconds: 10
        startupProbe:
          httpGet: { path: /health/live, port: 8000 }
          failureThreshold: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: churn-api
spec:
  type: ClusterIP
  selector:
    app: churn-api
  ports:
  - port: 80
    targetPort: 8000
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: churn-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: churn-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## 19. LLM-Specific Patterns

### OpenAI-Compatible API

If you're building an LLM service, your clients expect an OpenAI-compatible API. Here's the contract:

```python
from pydantic import BaseModel
from typing import Literal, Optional

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float = 1.0
    max_tokens: Optional[int] = None
    stream: bool = False
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[list[str]] = None

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict]
    usage: dict

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completion(req: ChatCompletionRequest):
    if req.stream:
        return StreamingResponse(
            stream_completion(req),
            media_type="text/event-stream",
        )
    # Non-streaming
    response = await call_your_model(req)
    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        created=int(time.time()),
        model=req.model,
        choices=[{
            "index": 0,
            "message": {"role": "assistant", "content": response.text},
            "finish_reason": "stop",
        }],
        usage={
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "total_tokens": response.prompt_tokens + response.completion_tokens,
        }
    )
```

### Token Counting

```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-4") -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

class TokenBudget:
    """Track token usage per user/request."""
    def __init__(self, max_tokens: int):
        self.max = max_tokens
        self.used = 0
    
    def consume(self, n: int):
        if self.used + n > self.max:
            raise HTTPException(429, "Token budget exceeded")
        self.used += n
```

### Concurrency Limits for GPU Models

```python
import asyncio

class GPUResourceManager:
    def __init__(self, max_concurrent: int = 4):
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def __aenter__(self):
        await self.semaphore.acquire()
        return self
    
    async def __aexit__(self, *args):
        self.semaphore.release()

gpu_manager = GPUResourceManager(max_concurrent=4)

@app.post("/predict/llm")
async def predict_llm(req: ChatRequest):
    async with gpu_manager:
        return await run_llm_inference(req)
```

### Embeddings API Pattern

```python
class EmbeddingRequest(BaseModel):
    input: str | list[str]
    model: str = "text-embedding-3-small"

class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: list[dict]  # {"object": "embedding", "embedding": [...], "index": 0}
    model: str
    usage: dict

@app.post("/v1/embeddings", response_model=EmbeddingResponse)
async def create_embedding(req: EmbeddingRequest):
    texts = [req.input] if isinstance(req.input, str) else req.input
    embeddings = []
    for i, text in enumerate(texts):
        vec = await embed(text)
        embeddings.append({"object": "embedding", "embedding": vec, "index": i})
    
    total_tokens = sum(count_tokens(t) for t in texts)
    return EmbeddingResponse(
        data=embeddings,
        model=req.model,
        usage={"prompt_tokens": total_tokens, "total_tokens": total_tokens},
    )
```

---

## 20. Putting It All Together — Full Example

Here's a **complete, production-ready** FastAPI app serving a churn prediction model. Save this as `main.py` and you have a deployable service.

```python
# main.py
import asyncio
import hashlib
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from typing import Optional

import joblib
import redis.asyncio as redis
import structlog
from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram
from pydantic import BaseModel, Field, field_validator

# ---------- Logging ----------
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
logger = structlog.get_logger()

# ---------- Models ----------
class PlanType(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class CustomerFeatures(BaseModel):
    customer_id: str = Field(..., min_length=1, max_length=64)
    age: int = Field(..., ge=18, le=120)
    monthly_spend: float = Field(..., ge=0, le=1_000_000)
    tenure_months: int = Field(..., ge=0, le=1200)
    support_tickets: int = Field(0, ge=0, le=1000)
    plan_type: PlanType = PlanType.PRO

class PredictionResponse(BaseModel):
    customer_id: str
    churn_probability: float = Field(..., ge=0, le=1)
    will_churn: bool
    risk_level: str
    risk_factors: list[str]
    model_version: str
    predicted_at: datetime

class BatchPredictionRequest(BaseModel):
    items: list[CustomerFeatures] = Field(..., min_length=1, max_length=500)

class BatchPredictionResponse(BaseModel):
    predictions: list[PredictionResponse]
    count: int
    processing_time_ms: float

class ErrorResponse(BaseModel):
    error: str
    message: str
    request_id: Optional[str] = None

# ---------- App State ----------
ml_models: dict[str, object] = {}
redis_client: Optional[redis.Redis] = None

# ---------- Metrics ----------
PREDICTION_COUNT = Counter(
    "predictions_total", "Total predictions made", ["model", "plan_type"]
)
PREDICTION_LATENCY = Histogram(
    "prediction_latency_seconds", "Time spent predicting"
)
PREDICTION_VALUE = Histogram(
    "prediction_value", "Distribution of predicted probabilities",
    buckets=[i/10 for i in range(11)]
)

# ---------- API Key Auth ----------
api_key_header = APIKeyHeader(name="X-API-Key")
API_KEYS = {
    "demo-key-123": {"name": "Demo Client", "tier": "free"},
}

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key not in API_KEYS:
        raise HTTPException(401, "Invalid API key")
    return API_KEYS[api_key]

# ---------- Rate Limiting ----------
async def rate_limit(api_key: str = Security(api_key_header)):
    """60 requests per minute per API key."""
    if redis_client is None:
        return  # skip if no redis
    key = f"rate:{api_key}:{int(time.time() // 60)}"
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, 60)
    count, _ = await pipe.execute()
    if count > 60:
        raise HTTPException(
            429,
            "Rate limit exceeded (60/min)",
            headers={"Retry-After": "60"},
        )

# ---------- Lifespan ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    # Load models
    try:
        ml_models["churn"] = joblib.load("models/churn_v2.pkl")
        logger.info("model_loaded", model="churn", version="v2")
    except Exception as e:
        logger.error("model_load_failed", error=str(e))
    
    # Connect Redis
    try:
        redis_client = redis.from_url("redis://redis:6379", decode_responses=True)
        await redis_client.ping()
        logger.info("redis_connected")
    except Exception as e:
        logger.warning("redis_unavailable", error=str(e))
        redis_client = None
    
    yield
    
    # Cleanup
    ml_models.clear()
    if redis_client:
        await redis_client.close()

# ---------- App ----------
app = FastAPI(
    title="Churn Prediction API",
    description="Production-grade ML API for customer churn prediction.",
    version="2.3.0",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# ---------- Middleware ----------
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start = time.time()
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.exception(
            "unhandled_error",
            request_id=request_id,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id},
        )
    
    duration_ms = (time.time() - start) * 1000
    logger.info(
        "request",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration_ms, 2),
    )
    response.headers["X-Request-ID"] = request_id
    return response

# ---------- Helpers ----------
def extract_features(f: CustomerFeatures) -> list:
    return [f.age, f.monthly_spend, f.tenure_months, f.support_tickets, 
            1 if f.plan_type == PlanType.PRO else 0]

def assess_risk(proba: float, f: CustomerFeatures) -> tuple[str, list[str]]:
    if proba < 0.3:
        level = "low"
    elif proba < 0.6:
        level = "medium"
    else:
        level = "high"
    
    factors = []
    if f.support_tickets >= 5:
        factors.append("high_support_tickets")
    if f.tenure_months < 6:
        factors.append("low_tenure")
    if f.monthly_spend < 50:
        factors.append("low_spend")
    if f.plan_type == PlanType.FREE:
        factors.append("free_plan")
    return level, factors

# ---------- Endpoints ----------
@app.get("/health/live", tags=["health"])
def liveness():
    return {"status": "alive"}

@app.get("/health/ready", tags=["health"])
def readiness():
    if "churn" not in ml_models:
        raise HTTPException(503, "Model not loaded")
    return {"status": "ready", "models": list(ml_models.keys())}

@app.post(
    "/predict",
    response_model=PredictionResponse,
    tags=["predictions"],
    dependencies=[Depends(verify_api_key), Depends(rate_limit)],
)
async def predict(features: CustomerFeatures):
    if "churn" not in ml_models:
        raise HTTPException(503, "Model not loaded")
    
    start = time.perf_counter()
    X = [extract_features(features)]
    proba = ml_models["churn"].predict_proba(X)[0][1]
    
    PREDICTION_COUNT.labels(model="churn-v2", plan_type=features.plan_type).inc()
    PREDICTION_LATENCY.observe(time.perf_counter() - start)
    PREDICTION_VALUE.observe(proba)
    
    risk_level, risk_factors = assess_risk(proba, features)
    
    return PredictionResponse(
        customer_id=features.customer_id,
        churn_probability=round(proba, 4),
        will_churn=proba >= 0.5,
        risk_level=risk_level,
        risk_factors=risk_factors,
        model_version="v2.3",
        predicted_at=datetime.utcnow(),
    )

@app.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    tags=["predictions"],
    dependencies=[Depends(verify_api_key), Depends(rate_limit)],
)
async def predict_batch(req: BatchPredictionRequest):
    if "churn" not in ml_models:
        raise HTTPException(503, "Model not loaded")
    
    start = time.perf_counter()
    X = [extract_features(item) for item in req.items]
    probas = ml_models["churn"].predict_proba(X)[:, 1]
    
    predictions = []
    for item, p in zip(req.items, probas):
        risk_level, risk_factors = assess_risk(p, item)
        predictions.append(PredictionResponse(
            customer_id=item.customer_id,
            churn_probability=round(float(p), 4),
            will_churn=bool(p >= 0.5),
            risk_level=risk_level,
            risk_factors=risk_factors,
            model_version="v2.3",
            predicted_at=datetime.utcnow(),
        ))
        PREDICTION_COUNT.labels(model="churn-v2", plan_type=item.plan_type).inc()
        PREDICTION_VALUE.observe(float(p))
    
    elapsed_ms = (time.perf_counter() - start) * 1000
    PREDICTION_LATENCY.observe(elapsed_ms / 1000)
    
    return BatchPredictionResponse(
        predictions=predictions,
        count=len(predictions),
        processing_time_ms=round(elapsed_ms, 2),
    )

@app.get("/models", tags=["models"], dependencies=[Depends(verify_api_key)])
def list_models():
    return {
        "models": [
            {"name": name, "version": "v2.3", "loaded": True}
            for name in ml_models
        ]
    }

# Run with: uvicorn main:app --reload
```

### requirements.txt

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
gunicorn==22.0.0
pydantic==2.7.4
joblib==1.4.2
scikit-learn==1.5.0
redis==5.0.7
httpx==0.27.0
structlog==24.2.0
prometheus-fastapi-instrumentator==7.0.0
prometheus-client==0.20.0
python-multipart==0.0.9
```

### Test It

```bash
uvicorn main:app --reload

# Health
curl http://localhost:8000/health/ready

# Predict
curl -X POST http://localhost:8000/predict \
    -H "X-API-Key: demo-key-123" \
    -H "Content-Type: application/json" \
    -d '{
        "customer_id": "c123",
        "age": 35,
        "monthly_spend": 100.0,
        "tenure_months": 12,
        "support_tickets": 2,
        "plan_type": "pro"
    }'

# OpenAPI docs
open http://localhost:8000/docs
```

---

## 21. Summary & Next Steps

### What You Learned

1. FastAPI is the best choice for AI APIs — async, type-safe, auto-docs.
2. Pydantic schemas are the foundation — design them carefully.
3. Dependency injection (`Depends`) is your friend — auth, rate limiting, model loading.
4. Use `async def` only when you do async I/O. For CPU-heavy ML, use `def` or `run_in_executor`.
5. Load models at startup with `lifespan`, NOT in request handlers.
6. Master the 5 request/response patterns: single, batch, file, async, streaming.
7. Implement auth (API key, JWT, OAuth), rate limiting (Redis), caching (Redis).
8. SSE for LLM streaming. WebSocket for bidirectional.
9. Testing with TestClient + fixtures. Load testing with Locust.
10. Observability = structured logs + Prometheus metrics + OpenTelemetry tracing.

### What's Next

- **04_Docker_Kubernetes_for_ML.md** — package this FastAPI app in Docker, deploy on K8s.
- **05_10_Projects_Beginner_to_Pro.md** — apply everything in 10 graded projects.

### How to Practice

1. Copy the full example above into a real project.
2. Train a real churn model (use Kaggle's telco churn dataset).
3. Add a real Postgres DB to log predictions.
4. Add JWT auth instead of API key.
5. Add a `/v1/chat/completions` endpoint that proxies to a local LLM.
6. Dockerize it (next file).
7. Deploy to a free K8s cluster (DigitalOcean, GKE free tier).
8. Hit it from a Streamlit/Gradio frontend.

When you can do all 8, you have a portfolio piece worth showing in interviews.

---

**End of File 3. Continue to 04_Docker_Kubernetes_for_ML.md.**
