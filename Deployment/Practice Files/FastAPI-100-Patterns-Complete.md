# 100 Essential FastAPI Patterns for Backend Engineering & AI/ML APIs 

A complete guide to master FastAPI through 100 carefully selected patterns. Organized progressively from async fundamentals to production-grade ML inference systems and deployment strategies.

---

## Part 1: Async Fundamentals (Patterns 1-15)

### Pattern 1: Basic FastAPI Application
**When to Use:** Starting any FastAPI project
**Production Value:** Foundation

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="MyAPI",
    version="1.0.0",
    description="Production-ready API",
    lifespan=lifespan
)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

# Run: uvicorn main:app --reload
```

### Pattern 2: Async vs Sync Routes
**When to Use:** Understanding when to use async/await
**Production Value:** Critical for performance

```python
from fastapi import FastAPI
import asyncio

app = FastAPI()

# SYNC route - blocks event loop (use for blocking I/O)
@app.get("/sync")
def sync_endpoint():
    # Use for: CPU-bound tasks (compute), blocking libraries
    # FastAPI runs this in a thread pool automatically
    return {"type": "sync"}

# ASYNC route - non-blocking (use for I/O operations)
@app.get("/async")
async def async_endpoint():
    # Use for: database queries, HTTP requests, file I/O
    await asyncio.sleep(1)  # Simulates async operation
    return {"type": "async"}

# Key insight:
# - Use async def for I/O-bound operations (database, API calls, file operations)
# - Use def for blocking I/O or CPU-intensive tasks (FastAPI runs in thread pool)
# - async is MUCH faster for high concurrency
```

### Pattern 3: Path Parameters
**When to Use:** Dynamic route segments
**Production Value:** URL routing

```python
from fastapi import FastAPI, Path

app = FastAPI()

# Simple path parameter
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id}

# Multiple path parameters
@app.get("/users/{user_id}/posts/{post_id}")
async def get_user_post(user_id: int, post_id: int):
    return {"user_id": user_id, "post_id": post_id}

# Path parameter with validation
@app.get("/items/{item_id}")
async def get_item(
    item_id: int = Path(..., ge=1, description="Item ID must be >= 1")
):
    return {"item_id": item_id}

# URL: GET /users/123
# FastAPI automatically converts "123" to integer
```

### Pattern 4: Query Parameters
**When to Use:** Filtering, pagination, sorting
**Production Value:** Data filtering

```python
from fastapi import FastAPI, Query
from typing import Optional

app = FastAPI()

# Simple query parameter
@app.get("/items/")
async def list_items(skip: int = 0, limit: int = 10):
    # URL: GET /items/?skip=10&limit=20
    return {"skip": skip, "limit": limit}

# Optional query parameter
@app.get("/search/")
async def search(q: Optional[str] = None):
    if q:
        return {"search": q}
    return {"search": None}

# List query parameters
from typing import List

@app.get("/items/")
async def filter_items(tags: List[str] = []):
    # URL: GET /items/?tags=python&tags=fastapi
    return {"tags": tags}

# Query parameter with validation
@app.get("/items/")
async def validated_items(
    q: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100)
):
    return {"q": q, "page": page, "size": size}
```

### Pattern 5: Request Body (POST Data)
**When to Use:** Creating/updating resources
**Production Value:** Data submission

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# Define data schema
class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: Optional[str] = None
    tax: Optional[float] = None

# Receive and validate data
@app.post("/items/", status_code=201)
async def create_item(item: Item):
    # FastAPI automatically validates:
    # - name must be string, 1-100 chars
    # - price must be float > 0
    # - description is optional
    # - tax is optional
    return {"item": item, "tax": item.price * 0.1 if item.tax else 0}

# JSON request:
# {
#   "name": "Laptop",
#   "price": 999.99,
#   "description": "A high-performance laptop"
# }
```

### Pattern 6: Pydantic Models (Data Validation)
**When to Use:** All input/output validation
**Production Value:** Type safety + auto-docs

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

# Enum for fixed values
class ItemType(str, Enum):
    ELECTRONICS = "electronics"
    FURNITURE = "furniture"
    CLOTHING = "clothing"

# Basic model with Pydantic v2 syntax
class User(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: int = Field(..., ge=0, le=120)
    item_type: ItemType = ItemType.ELECTRONICS
    created_at: datetime = Field(default_factory=datetime.now)

# Nested models
class Address(BaseModel):
    street: str
    city: str
    country: str = "USA"

class UserWithAddress(BaseModel):
    user: User
    address: Address

# Validation happens automatically!
```

### Pattern 7: Response Models
**When to Use:** Documenting and formatting API responses
**Production Value:** API documentation + type safety

```python
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

app = FastAPI()

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Support ORM models

    id: int
    username: str
    email: str

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    # Only fields in UserResponse will be returned
    # Provides documentation in Swagger
    return {
        "id": user_id,
        "username": "john",
        "email": "john@example.com",
        "password": "secret"  # This will be excluded!
    }

# Benefits:
# - Automatic response validation
# - Auto-generated OpenAPI docs
# - Type hints for IDE autocomplete
# - Filters out sensitive data
```

### Pattern 8: Status Codes
**When to Use:** Signaling request outcomes
**Production Value:** HTTP compliance

```python
from fastapi import FastAPI, status

app = FastAPI()

@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: dict):
    return {"item": item}

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    return None

# Common status codes:
# 200 OK - successful GET
# 201 Created - successful POST
# 204 No Content - successful DELETE
# 400 Bad Request - invalid input
# 401 Unauthorized - needs auth
# 403 Forbidden - auth but not allowed
# 404 Not Found - resource not found
# 422 Unprocessable Entity - validation error
# 429 Too Many Requests - rate limit
# 500 Internal Server Error - server error
```

### Pattern 9: Header Parameters
**When to Use:** Reading HTTP headers
**Production Value:** Authentication, metadata

```python
from fastapi import FastAPI, Header
from typing import Optional

app = FastAPI()

# Required header
@app.get("/items/")
async def get_items(x_token: str = Header(...)):
    # Header name converted: X-Token -> x_token
    return {"x_token": x_token}

# Optional header
@app.get("/items/")
async def list_items(
    x_token: Optional[str] = Header(None)
):
    return {"x_token": x_token}

# User-Agent example
@app.get("/agent/")
async def check_agent(user_agent: Optional[str] = Header(None)):
    return {"user_agent": user_agent}
```

### Pattern 10: Form Data
**When to Use:** HTML forms, file uploads
**Production Value:** File handling

```python
from fastapi import FastAPI, Form, File, UploadFile

app = FastAPI()

# Form data
@app.post("/login/")
async def login(username: str = Form(...), password: str = Form(...)):
    return {"username": username}

# File upload
@app.post("/upload/")
async def upload(file: UploadFile = File(...)):
    contents = await file.read()
    return {"filename": file.filename, "size": len(contents)}

# Multiple files
@app.post("/upload-multiple/")
async def upload_multiple(files: list[UploadFile] = File(...)):
    return {"filenames": [f.filename for f in files]}

# File upload with validation
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    contents = await file.read()
    return {"filename": file.filename, "size": len(contents)}
```

### Pattern 11: HTTPException Error Handling
**When to Use:** Returning error responses
**Production Value:** Error signaling

```python
from fastapi import FastAPI, HTTPException, status

app = FastAPI()

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    if item_id < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="item_id must be positive"
        )
    if item_id > 1000:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return {"item_id": item_id}

# FastAPI automatically:
# - Sets correct status code
# - Returns JSON error response
# - Validates response format
```

### Pattern 12: Dependency Injection with Depends
**When to Use:** Reusable logic, DRY principle
**Production Value:** Code organization, security

```python
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated

app = FastAPI()

# Dependency function
async def get_current_user(token: str) -> dict:
    if token != "valid_token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"user_id": 123, "username": "john"}

# Use dependency in route (modern Annotated syntax)
@app.get("/users/me")
async def get_me(current_user: Annotated[dict, Depends(get_current_user)]):
    return current_user

# Benefits:
# - Reuse auth logic across routes
# - Dependency is only called once per request
# - Test by mocking the dependency
# - Automatic OpenAPI documentation
```

### Pattern 13: Multiple Dependencies
**When to Use:** Complex authorization chains
**Production Value:** Authorization control

```python
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated

app = FastAPI()

async def verify_token(token: str) -> dict:
    if token != "valid":
        raise HTTPException(status_code=401)
    return {"user_id": 1}

async def check_admin(user: Annotated[dict, Depends(verify_token)]) -> dict:
    if user["user_id"] != 1:  # Only user 1 is admin
        raise HTTPException(status_code=403, detail="Not admin")
    return user

# Use chained dependency
@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: Annotated[dict, Depends(check_admin)]
):
    return {"deleted": user_id, "by": admin["user_id"]}

# Dependency chain: verify_token -> check_admin -> route
```

### Pattern 14: Lifespan Events (Startup/Shutdown)
**When to Use:** Resource initialization/cleanup
**Production Value:** Resource management

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Lifespan context manager (MODERN - recommended)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    print("Starting up...")
    database_pool = await setup_database()
    redis_client = await setup_redis()
    yield
    # Shutdown code
    print("Shutting down...")
    await database_pool.close()
    await redis_client.close()

app = FastAPI(lifespan=lifespan)

# NOTE: @app.on_event("startup") is DEPRECATED
# Always use lifespan context manager instead
```

### Pattern 15: Background Tasks
**When to Use:** Non-blocking operations after response
**Production Value:** Fast responses

```python
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

def send_email(email: str, message: str):
    # This runs AFTER response is sent
    # Don't await anything here!
    print(f"Sending email to {email}")

@app.post("/send-notification/")
async def send_notification(email: str, bg_tasks: BackgroundTasks):
    # Response sent immediately
    bg_tasks.add_task(send_email, email, "notification")
    return {"status": "sending"}

# Use for: emails, webhooks, logging, cleanup
# Do NOT use for: critical operations that need confirmation
```

---

## Part 2: Request/Response & Validation (Patterns 16-30)

### Pattern 16: Pydantic Field Validation
**When to Use:** Complex field validation
**Production Value:** Data quality

```python
from pydantic import BaseModel, Field, field_validator

class Product(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)  # price > 0
    quantity: int = Field(default=0, ge=0)  # quantity >= 0

    @field_validator('name')
    @classmethod
    def name_lowercase(cls, v):
        return v.lower()

    @field_validator('price')
    @classmethod
    def price_two_decimals(cls, v):
        return round(v, 2)

# Validation happens automatically when creating instance
# product = Product(name="  LAPTOP  ", price=999, quantity=1)
# Raises ValidationError if invalid
```

### Pattern 17: Enum for Fixed Values
**When to Use:** Options with limited choices
**Production Value:** Type safety

```python
from fastapi import FastAPI
from enum import Enum

class ItemType(str, Enum):
    ELECTRONICS = "electronics"
    FURNITURE = "furniture"
    CLOTHING = "clothing"

app = FastAPI()

@app.get("/items/")
async def list_items(item_type: ItemType = ItemType.ELECTRONICS):
    return {"item_type": item_type}

# Swagger automatically shows dropdown
# Type validation built-in
```

### Pattern 18: Multiple Response Models
**When to Use:** Different responses for different scenarios
**Production Value:** API documentation

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class Item(BaseModel):
    id: int
    name: str

class Error(BaseModel):
    error: str

app = FastAPI()

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    if item_id == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": item_id, "name": "Item"}

# Swagger shows Item as response model
# But you can also document errors with responses parameter
```

### Pattern 19: Common Response Structure
**When to Use:** Consistent API responses
**Production Value:** Standardization

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class Response(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    status_code: int

class User(BaseModel):
    id: int
    name: str

# Usage
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}", response_model=Response[User])
async def get_user(user_id: int):
    if user_id < 0:
        return Response(
            success=False,
            error="Invalid ID",
            status_code=400
        )
    return Response(
        success=True,
        data={"id": user_id, "name": "John"},
        status_code=200
    )
```

### Pattern 20: Pagination Model
**When to Use:** Large datasets
**Production Value:** Data efficiency

```python
from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int

class User(BaseModel):
    id: int
    name: str

# Usage
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/", response_model=PaginatedResponse[User])
async def list_users(skip: int = 0, limit: int = 10):
    # Simulate database query
    all_users = [
        {"id": i, "name": f"User{i}"} for i in range(1, 101)
    ]
    total = len(all_users)
    items = all_users[skip:skip + limit]

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

### Pattern 21: Custom Response Headers
**When to Use:** Adding custom HTTP headers
**Production Value:** Advanced responses

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/items/")
async def get_items():
    return JSONResponse(
        content={"items": []},
        headers={"X-Custom-Header": "value", "X-Total-Count": "0"},
        status_code=200
    )
```

### Pattern 22: Streaming Response
**When to Use:** Large files, real-time data
**Production Value:** Memory efficiency

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def generate_csv():
    yield "id,name\n"
    for i in range(1000):
        yield f"{i},item{i}\n"

@app.get("/export/csv")
async def export_csv():
    return StreamingResponse(
        generate_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"}
    )
```

### Pattern 23: Error Response Structure
**When to Use:** Consistent error handling
**Production Value:** Client error handling

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime

class ErrorDetail(BaseModel):
    error_code: str
    message: str
    timestamp: datetime
    path: str

app = FastAPI()

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content=ErrorDetail(
            error_code="INVALID_VALUE",
            message=str(exc),
            timestamp=datetime.now(),
            path=str(request.url.path)
        ).model_dump()
    )
```

### Pattern 24: Security Header (Authorization)
**When to Use:** API authentication
**Production Value:** Security

```python
from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token != "valid_token":
        from fastapi import HTTPException
        raise HTTPException(status_code=401)
    return {"token": token}

@app.get("/protected/")
async def protected_route(auth: dict = Depends(verify_token)):
    return {"message": "Access granted"}

# Header: Authorization: Bearer valid_token
```

### Pattern 25: CORS (Cross-Origin Requests)
**When to Use:** Frontend calling your API
**Production Value:** Security + browser support

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Production: specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com", "https://www.example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Development: allow all origins (NOT for production!)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
```

### Pattern 26: Middleware for Logging
**When to Use:** Request/response logging
**Production Value:** Observability

```python
from fastapi import FastAPI, Request
import logging
import time

logger = logging.getLogger(__name__)

app = FastAPI()

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} "
        f"{response.status_code} {process_time:.3f}s"
    )
    return response
```

### Pattern 27: Middleware for Request ID Tracking
**When to Use:** Distributed tracing
**Production Value:** Debugging

```python
from fastapi import FastAPI, Request
import uuid
from contextvars import ContextVar

request_id_var = ContextVar('request_id', default=None)

app = FastAPI()

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request_id_var.set(request_id)
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.get("/items/")
async def get_items(request: Request):
    request_id = request.state.request_id
    return {"request_id": request_id}
```

### Pattern 28: GZip Compression
**When to Use:** Reducing response size
**Production Value:** Bandwidth saving

```python
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Automatically compresses responses > 1000 bytes
```

### Pattern 29: Trusted Host Middleware
**When to Use:** Production security
**Production Value:** Host validation

```python
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com", "www.example.com", "*.example.com"]
)

# Rejects requests with invalid Host header
```

### Pattern 30: Annotated Type Hints (Modern Pattern)
**When to Use:** All FastAPI projects (2024+)
**Production Value:** Better IDE support + cleaner code

```python
from fastapi import FastAPI, Depends, Query, Path, Header
from typing import Annotated

app = FastAPI()

# Modern Annotated syntax (recommended)
@app.get("/users/{user_id}")
async def get_user(
    user_id: Annotated[int, Path(ge=1, description="User ID")],
    token: Annotated[str, Header(description="Auth token")],
    q: Annotated[str | None, Query(max_length=100)] = None
):
    return {"user_id": user_id, "q": q}

# Benefits:
# - Cleaner function signatures
# - Better IDE autocomplete
# - Type hints and validation in one place
# - More readable code
```

---

## Part 3: Database & Data Patterns (Patterns 31-50)

### Pattern 31: Async SQLAlchemy Sessions (Production!)
**When to Use:** High-performance databases
**Production Value:** Non-blocking database access

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

app = FastAPI()

@app.get("/users/")
async def get_users(session: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await session.execute(select(User))
    users = result.scalars().all()
    return users
```

### Pattern 32: SQLAlchemy Model Definition
**When to Use:** Database schema
**Production Value:** ORM base

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship
    items = relationship("Item", back_populates="owner")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)

    # Relationship
    owner = relationship("User", back_populates="items")
```

### Pattern 33: CRUD Operations (Create, Read, Update, Delete)
**When to Use:** Basic data operations
**Production Value:** Data manipulation

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

app = FastAPI()

# CREATE
@app.post("/users/", status_code=201)
async def create_user(user_data: dict, db: AsyncSession = Depends(get_db)):
    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# READ
@app.get("/users/{user_id}")
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# UPDATE
@app.put("/users/{user_id}")
async def update_user(user_id: int, user_data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user_data.items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user

# DELETE
@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return {"deleted": True}
```

### Pattern 34: Connection Pooling Configuration
**When to Use:** Production databases
**Production Value:** Performance + reliability

```python
from sqlalchemy.ext.asyncio import create_async_engine

# Connection pooling best practices
engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost/db",
    echo=False,
    pool_size=20,          # Number of connections to maintain
    max_overflow=10,       # Extra connections when pool exhausted
    pool_pre_ping=True,    # Check connection health before using
    pool_recycle=3600,     # Recycle connections after 1 hour
    pool_timeout=30,       # Timeout for getting connection from pool
)
```

### Pattern 35: Database Migration with Alembic
**When to Use:** Schema versioning
**Production Value:** Version control for database

```bash
# Initialize Alembic:
alembic init alembic

# In alembic/env.py
# Set target_metadata = Base.metadata

# Create migration:
alembic revision --autogenerate -m "Add users table"

# Apply migration:
alembic upgrade head

# Rollback:
alembic downgrade -1

# Check current version:
alembic current
```

### Pattern 36: Transactions and Rollback
**When to Use:** Multi-step database operations
**Production Value:** Data consistency

```python
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

@app.post("/transfer/")
async def transfer_funds(
    from_user_id: int,
    to_user_id: int,
    amount: float,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Deduct from sender
        sender = await db.get(User, from_user_id)
        sender.balance -= amount

        # Add to receiver
        receiver = await db.get(User, to_user_id)
        receiver.balance += amount

        # Commit both or rollback both
        await db.commit()
        return {"status": "success"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
```

### Pattern 37: Database Query Optimization
**When to Use:** Large datasets
**Production Value:** Performance

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

# BAD: N+1 query problem
async def get_users_bad(db: AsyncSession):
    users = await db.execute(select(User))
    for user in users.scalars():
        # This queries database for EACH user!
        items = await db.execute(select(Item).where(Item.user_id == user.id))

# GOOD: Join query
async def get_users_good(db: AsyncSession):
    query = select(User).options(joinedload(User.items))
    result = await db.execute(query)
    users = result.scalars().unique()
    # All data fetched in 1-2 queries
```

### Pattern 38: Repository Pattern (Clean Code)
**When to Use:** Decoupling business logic from data
**Production Value:** Testability

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int):
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str):
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create(self, user_data: dict):
        user = User(**user_data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

# Usage
from fastapi import Depends

async def get_user_repo(db: AsyncSession = Depends(get_db)):
    return UserRepository(db)

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    repo: UserRepository = Depends(get_user_repo)
):
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404)
    return user
```

### Pattern 39: Redis Caching
**When to Use:** Frequently accessed data
**Production Value:** Performance boost

```python
from fastapi import FastAPI
import redis.asyncio as aioredis
import json

app = FastAPI()

# Redis client
redis_client = None

@app.on_event("startup")
async def startup():
    global redis_client
    redis_client = await aioredis.from_url("redis://localhost")

@app.on_event("shutdown")
async def shutdown():
    await redis_client.close()

@app.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    # Check cache first
    cached = await redis_client.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)

    # Query database
    user = await db.get(User, user_id)
    if user:
        # Cache for 1 hour
        await redis_client.set(
            f"user:{user_id}",
            json.dumps({"id": user.id, "name": user.username}),
            ex=3600
        )
    return user
```

### Pattern 40: Filtering and Searching
**When to Use:** Advanced queries
**Production Value:** Data retrieval

```python
from fastapi import FastAPI, Query
from typing import Optional
from sqlalchemy import select

app = FastAPI()

@app.get("/items/")
async def search_items(
    skip: int = 0,
    limit: int = 10,
    name: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Item)

    if name:
        query = query.where(Item.name.ilike(f"%{name}%"))
    if min_price is not None:
        query = query.where(Item.price >= min_price)
    if max_price is not None:
        query = query.where(Item.price <= max_price)

    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

# URL: GET /items/?name=laptop&min_price=100&max_price=2000
```

### Pattern 41: Sorting
**When to Use:** Ordered results
**Production Value:** Data organization

```python
from fastapi import FastAPI
from sqlalchemy import desc

@app.get("/items/")
async def list_items(
    sort_by: str = "created_at",
    order: str = "desc",  # "asc" or "desc"
    db: AsyncSession = Depends(get_db)
):
    sort_column = getattr(Item, sort_by, Item.created_at)

    if order == "desc":
        query = select(Item).order_by(desc(sort_column))
    else:
        query = select(Item).order_by(sort_column)

    result = await db.execute(query)
    return result.scalars().all()
```

### Pattern 42: Bulk Operations
**When to Use:** Importing large datasets
**Production Value:** Efficiency

```python
@app.post("/items/bulk/")
async def create_items_bulk(
    items_data: list[dict],
    db: AsyncSession = Depends(get_db)
):
    items = [Item(**item) for item in items_data]
    db.add_all(items)
    await db.commit()
    return {"created": len(items)}
```

### Pattern 43: Aggregation Queries
**When to Use:** Statistics and summaries
**Production Value:** Analytics

```python
from sqlalchemy import func, select

@app.get("/stats/")
async def get_stats(db: AsyncSession = Depends(get_db)):
    # Count
    count_query = select(func.count(User.id))
    total_users = await db.scalar(count_query)

    # Sum
    sum_query = select(func.sum(Item.price))
    total_value = await db.scalar(sum_query)

    # Average
    avg_query = select(func.avg(Item.price))
    avg_price = await db.scalar(avg_query)

    return {
        "total_users": total_users,
        "total_inventory_value": total_value,
        "average_item_price": avg_price
    }
```

### Pattern 44: Foreign Key Relationships
**When to Use:** Related data
**Production Value:** Data integrity

```python
from sqlalchemy import ForeignKey, Column, Integer, String
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    items = relationship("Item", back_populates="owner")

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="items")

# Usage
@app.get("/users/{user_id}/items/")
async def get_user_items(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    return user.items
```

### Pattern 45: Many-to-Many Relationships
**When to Use:** Complex relationships
**Production Value:** Flexible associations

```python
from sqlalchemy import Table, Column, Integer, ForeignKey, String

# Association table
user_tag_association = Table(
    'user_tag',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    tags = relationship("Tag", secondary=user_tag_association)

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String)
```

### Pattern 46: Soft Delete Pattern
**When to Use:** Keeping deleted data
**Production Value:** Audit trail

```python
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    deleted_at = Column(DateTime, nullable=True)

# Soft delete
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    user.deleted_at = datetime.now()
    await db.commit()

# Get only non-deleted
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.deleted_at.is_(None))
    )
    return result.scalars().all()
```

### Pattern 47: Audit Trail (Created/Updated Timestamps)
**When to Use:** Tracking changes
**Production Value:** Audit logs

```python
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

class AuditMixin:
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now,
        onupdate=datetime.now
    )

class User(Base, AuditMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String)
```

### Pattern 48: Lazy Loading vs Eager Loading
**When to Use:** Optimizing query performance
**Production Value:** Database efficiency

```python
from sqlalchemy.orm import joinedload, selectinload

# Lazy loading (bad - N+1 query problem)
users = await db.execute(select(User))
for user in users.scalars():
    # This queries items separately for each user!
    items = user.items

# Eager loading (good - single query)
query = select(User).options(joinedload(User.items))
result = await db.execute(query)
users = result.scalars().unique()
# All items loaded in first query!
```

### Pattern 49: Database Seed Data
**When to Use:** Development/testing
**Production Value:** Data initialization

```python
async def seed_database(db: AsyncSession):
    # Check if data already exists
    result = await db.execute(select(User))
    if result.scalars().first():
        return

    # Add seed data
    users = [
        User(username="john", email="john@example.com"),
        User(username="jane", email="jane@example.com"),
    ]
    db.add_all(users)
    await db.commit()

@app.on_event("startup")
async def startup():
    async with AsyncSessionLocal() as db:
        await seed_database(db)
```

### Pattern 50: Bulk Updates Optimization
**When to Use:** Large batch updates
**Production Value:** Performance

```python
from sqlalchemy import update

@app.post("/items/bulk-update/")
async def bulk_update(updates: list[dict], db: AsyncSession = Depends(get_db)):
    # BAD: Update each item separately
    # for item_data in updates:
    #     item = await db.get(Item, item_data["id"])
    #     item.status = item_data["status"]
    #     await db.commit()

    # GOOD: Single bulk update
    await db.execute(
        update(Item)
        .where(Item.id.in_([u["id"] for u in updates]))
        .values(status=Item.status)
    )
    await db.commit()
    return {"updated": len(updates)}
```

---

## Part 4: Authentication & Security (Patterns 51-65)

### Pattern 51: Password Hashing
**When to Use:** Storing user passwords
**Production Value:** Security critical

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Usage
hashed = hash_password("mypassword123")
is_correct = verify_password("mypassword123", hashed)  # True
```

### Pattern 52: JWT Token Generation
**When to Use:** Stateless authentication
**Production Value:** Secure authentication

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional

SECRET_KEY = "your-secret-key-keep-it-safe"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

### Pattern 53: Login Endpoint
**When to Use:** User authentication
**Production Value:** Auth entry point

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@app.post("/login/", response_model=Token)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Find user
    result = await db.execute(
        select(User).where(User.username == credentials.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create token
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
```

### Pattern 54: Protected Route with JWT
**When to Use:** Securing endpoints
**Production Value:** Authorization

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated

security = HTTPBearer()

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    user = await db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.get("/me/")
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user
```

### Pattern 55: Role-Based Access Control (RBAC)
**When to Use:** Authorization by role
**Production Value:** Permission system

```python
from enum import Enum
from sqlalchemy import Column, String

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    role = Column(String, default=UserRole.USER)

# Authorization dependency
async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user

# Protected route
@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)
    await db.delete(user)
    await db.commit()
    return {"deleted": True}
```

### Pattern 56: Refresh Token Pattern
**When to Use:** Long-lived authentication
**Production Value:** Better UX + security

```python
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

def create_tokens(user_id: int):
    access_token = create_access_token(
        {"sub": str(user_id)},
        expires_delta=timedelta(minutes=15)  # Short-lived
    )
    refresh_token = create_access_token(
        {"sub": str(user_id), "type": "refresh"},
        expires_delta=timedelta(days=7)  # Long-lived
    )
    return {"access_token": access_token, "refresh_token": refresh_token}

@app.post("/refresh/")
async def refresh_access_token(refresh_token: str):
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401)

    new_access_token = create_access_token({"sub": payload["sub"]})
    return {"access_token": new_access_token}
```

### Pattern 57: API Key Authentication
**When to Use:** Service-to-service authentication
**Production Value:** Simple auth for APIs

```python
from fastapi import Header, HTTPException

API_KEYS = {"sk-12345": "client1", "sk-67890": "client2"}

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return API_KEYS[x_api_key]

@app.get("/protected/")
async def protected_route(client: str = Depends(verify_api_key)):
    return {"client": client}
```

### Pattern 58: Rate Limiting
**When to Use:** Preventing abuse
**Production Value:** Resource protection

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as aioredis

@app.on_event("startup")
async def startup():
    redis = await aioredis.from_url("redis://localhost")
    await FastAPILimiter.init(redis)

@app.get(
    "/api/data/",
    dependencies=[Depends(RateLimiter(times=100, seconds=60))]
)
async def get_data():
    return {"data": "value"}
```

### Pattern 59: Content Security Headers
**When to Use:** XSS/CSRF prevention
**Production Value:** Security hardening

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

### Pattern 60: Environment Secrets
**When to Use:** Secure configuration
**Production Value:** Security best practice

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    api_key: str

    class Config:
        env_file = ".env"

settings = Settings()

# .env file (never commit!)
# DATABASE_URL=postgresql://...
# SECRET_KEY=your-secret-key
# API_KEY=your-api-key
```

---

## Part 5: ML Model Serving & Testing (Patterns 61-80)

### Pattern 61: Loading ML Model on Startup
**When to Use:** Efficient model serving
**Production Value:** Resource optimization

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
import pickle

# Load model once at startup
model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    with open("model.pkl", "rb") as f:
        model = pickle.load(f)
    print("Model loaded")
    yield
    print("Model unloaded")

app = FastAPI(lifespan=lifespan)

@app.get("/predict/")
async def predict(input_data: dict):
    prediction = model.predict([input_data["features"]])
    return {"prediction": prediction[0]}
```

### Pattern 62: Batch Prediction Endpoint
**When to Use:** Multiple predictions at once
**Production Value:** Performance boost

```python
from pydantic import BaseModel
from typing import List

class PredictionInput(BaseModel):
    features: List[float]

class PredictionOutput(BaseModel):
    prediction: float
    confidence: float

@app.post("/predict-batch/", response_model=List[PredictionOutput])
async def predict_batch(inputs: List[PredictionInput]):
    features = [item.features for item in inputs]
    predictions = model.predict(features)
    confidences = model.predict_proba(features).max(axis=1)

    return [
        {"prediction": pred, "confidence": conf}
        for pred, conf in zip(predictions, confidences)
    ]
```

### Pattern 63: Feature Validation for ML
**When to Use:** Data quality checks
**Production Value:** Model reliability

```python
from pydantic import BaseModel, Field, field_validator

class MLInput(BaseModel):
    age: int = Field(..., ge=0, le=150)
    income: float = Field(..., gt=0)
    credit_score: int = Field(..., ge=300, le=850)

    @field_validator('age')
    @classmethod
    def validate_age(cls, v):
        if v < 18:
            raise ValueError('Must be 18+')
        return v

@app.post("/predict/")
async def predict(input_data: MLInput):
    # Input automatically validated
    prediction = model.predict([[input_data.age, input_data.income, input_data.credit_score]])
    return {"prediction": prediction[0]}
```

### Pattern 64: Model Versioning
**When to Use:** Multiple model versions
**Production Value:** A/B testing, rollback

```python
from fastapi import FastAPI, Query

models = {
    "v1": load_model("models/v1/model.pkl"),
    "v2": load_model("models/v2/model.pkl"),
}

@app.post("/predict/")
async def predict(
    input_data: dict,
    model_version: str = Query("v2")
):
    if model_version not in models:
        raise HTTPException(status_code=400, detail="Invalid version")

    model = models[model_version]
    prediction = model.predict([input_data["features"]])
    return {"prediction": prediction[0], "model_version": model_version}
```

### Pattern 65: Async Model Inference
**When to Use:** Long-running predictions
**Production Value:** Non-blocking inference

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor

executor = ProcessPoolExecutor()

def blocking_predict(features):
    # This runs in separate process
    return model.predict([features])[0]

@app.post("/predict/")
async def predict(input_data: dict):
    # Non-blocking!
    prediction = await asyncio.get_event_loop().run_in_executor(
        executor,
        blocking_predict,
        input_data["features"]
    )
    return {"prediction": prediction}
```

### Pattern 66: Caching Model Predictions
**When to Use:** Repeated predictions
**Production Value:** Performance

```python
import hashlib
import json

@app.post("/predict/")
async def predict(input_data: dict):
    # Create cache key
    key = f"pred:{hashlib.md5(json.dumps(input_data, sort_keys=True).encode()).hexdigest()}"

    # Check cache
    cached = await redis_client.get(key)
    if cached:
        return json.loads(cached)

    # Predict
    prediction = model.predict([input_data["features"]])[0]
    result = {"prediction": prediction}

    # Cache result (1 hour TTL)
    await redis_client.set(key, json.dumps(result), ex=3600)
    return result
```

### Pattern 67: Model Health Check
**When to Use:** Monitoring model availability
**Production Value:** Uptime verification

```python
@app.get("/health/model/")
async def model_health():
    try:
        # Test prediction
        test_input = [1.0, 2.0, 3.0]
        prediction = model.predict([test_input])
        return {"status": "healthy", "model_version": "v2"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Pattern 68: Input Logging for ML
**When to Use:** Monitoring and debugging
**Production Value:** Model monitoring

```python
import json
from datetime import datetime

@app.post("/predict/")
async def predict(input_data: dict):
    # Log input
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "input": input_data,
        "model_version": "v2"
    }

    # Save to database or file
    with open("predictions.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    prediction = model.predict([input_data["features"]])[0]
    return {"prediction": prediction}
```

### Pattern 69: Model Metrics and Monitoring
**When to Use:** Tracking model performance
**Production Value:** Model observability

```python
from prometheus_client import Counter, Histogram, generate_latest

prediction_count = Counter('predictions_total', 'Total predictions')
prediction_time = Histogram('prediction_seconds', 'Prediction time')
prediction_error = Counter('prediction_errors', 'Prediction errors')

@app.post("/predict/")
async def predict(input_data: dict):
    with prediction_time.time():
        try:
            prediction = model.predict([input_data["features"]])[0]
            prediction_count.inc()
            return {"prediction": prediction}
        except Exception as e:
            prediction_error.inc()
            raise HTTPException(status_code=500, detail="Prediction failed")

@app.get("/metrics/")
async def metrics():
    return generate_latest()
```

### Pattern 70: Testing with pytest
**When to Use:** Validating API endpoints
**Production Value:** Code quality

```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    return TestClient(app)

def test_predict(client):
    response = client.post(
        "/predict/",
        json={"features": [1.0, 2.0, 3.0]}
    )
    assert response.status_code == 200
    assert "prediction" in response.json()

def test_predict_batch(client):
    response = client.post(
        "/predict-batch/",
        json=[
            {"features": [1.0, 2.0, 3.0]},
            {"features": [4.0, 5.0, 6.0]}
        ]
    )
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_health_check(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

---

## Part 6: Production Deployment (Patterns 71-100)

### Pattern 71: Structured Logging
**When to Use:** Production observability
**Production Value:** Debugging and monitoring

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "extra_data"):
            log_entry["extra"] = record.extra_data
        return json.dumps(log_entry)

# Setup
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)

logger = logging.getLogger(__name__)

@app.get("/items/")
async def get_items():
    logger.info("Items fetched", extra={"extra_data": {"user_id": 123}})
    return {"items": []}
```

### Pattern 72: Request ID Tracking (Production)
**When to Use:** Distributed tracing
**Production Value:** Request correlation

```python
import uuid
from contextvars import ContextVar

request_id_var = ContextVar('request_id', default=None)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request_id_var.set(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Use request_id in logs
def log_with_request_id(message: str):
    request_id = request_id_var.get()
    logger.info(message, extra={"extra_data": {"request_id": request_id}})
```

### Pattern 73: Health Check Endpoint
**When to Use:** Load balancer monitoring
**Production Value:** Deployment automation

```python
@app.get("/health/")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        # Check database
        await db.execute(select(1))
        return {
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }, 503
```

### Pattern 74: Metrics Endpoint (Prometheus)
**When to Use:** Observability stack
**Production Value:** Monitoring

```python
from prometheus_client import Counter, Gauge, generate_latest
from fastapi.responses import Response

requests_total = Counter('http_requests_total', 'Total HTTP requests')
active_connections = Gauge('http_connections_active', 'Active connections')

@app.middleware("http")
async def track_metrics(request: Request, call_next):
    requests_total.inc()
    active_connections.inc()
    try:
        response = await call_next(request)
        return response
    finally:
        active_connections.dec()

@app.get("/metrics/")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Pattern 75: Graceful Shutdown
**When to Use:** Clean resource cleanup
**Production Value:** Data consistency

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up")
    db_pool = await setup_database()
    redis = await setup_redis()
    yield
    # Shutdown
    logger.info("Shutting down")
    await db_pool.close()
    await redis.close()

app = FastAPI(lifespan=lifespan)
```

### Pattern 76: Docker Configuration
**When to Use:** Containerization
**Production Value:** Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Pattern 77: Environment Configuration
**When to Use:** Different environments
**Production Value:** Environment isolation

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    environment: str = "development"
    database_url: str
    redis_url: str
    debug: bool = False
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# Production settings enforce stronger validation
if settings.environment == "production":
    assert not settings.debug
    assert settings.database_url.startswith("postgresql+asyncpg://")
```

### Pattern 78: Gunicorn + Uvicorn (Production Server)
**When to Use:** Production deployment
**Production Value:** Multi-worker setup

```bash
# Install
pip install gunicorn uvicorn

# Run with Gunicorn (4 workers)
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Configuration file (gunicorn_config.py)
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"
worker_connections = 1000
timeout = 120
keepalive = 5
```

### Pattern 79: Nginx Configuration (Reverse Proxy)
**When to Use:** Production deployment
**Production Value:** Load balancing

```nginx
upstream fastapi {
    server api1:8000;
    server api2:8000;
    server api3:8000;
}

server {
    listen 80;
    server_name api.example.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://fastapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API documentation
    location /docs {
        proxy_pass http://fastapi/docs;
    }
}
```

### Pattern 80: Error Response Formatting
**When to Use:** Consistent error handling
**Production Value:** API reliability

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    timestamp: datetime
    path: str

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            timestamp=datetime.now(),
            path=str(request.url.path)
        ).model_dump()
    )
```

### Pattern 81: Validation Error Customization
**When to Use:** Better error messages
**Production Value:** UX improvement

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "VALIDATION_ERROR",
            "details": exc.errors()
        }
    )
```

### Pattern 82: OpenAPI Documentation Customization
**When to Use:** API documentation
**Production Value:** Developer experience

```python
app = FastAPI(
    title="My API",
    description="A powerful ML API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Hide docs in production
if not settings.debug:
    app.docs_url = None
    app.redoc_url = None
    app.openapi_url = None
```

### Pattern 83: Versioning API Routes
**When to Use:** Supporting multiple API versions
**Production Value:** Backward compatibility

```python
from fastapi import APIRouter

# V1 router
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

@v1_router.get("/items/")
async def get_items_v1():
    return {"items": []}

# V2 router
v2_router = APIRouter(prefix="/api/v2", tags=["v2"])

@v2_router.get("/items/")
async def get_items_v2():
    return {
        "items": [],
        "metadata": {"count": 0}
    }

app.include_router(v1_router)
app.include_router(v2_router)
```

### Pattern 84: Database Connection Health Check
**When to Use:** Monitoring database
**Production Value:** Uptime tracking

```python
@app.get("/health/db/")
async def check_database(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(select(1))
        return {"database": "healthy"}
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")
```

### Pattern 85: Redis Connection Health Check
**When to Use:** Monitoring cache
**Production Value:** Uptime tracking

```python
@app.get("/health/redis/")
async def check_redis():
    try:
        await redis_client.ping()
        return {"redis": "healthy"}
    except Exception as e:
        logger.error(f"Redis error: {e}")
        raise HTTPException(status_code=503, detail="Redis unavailable")
```

### Pattern 86: Integration Tests
**When to Use:** End-to-end testing
**Production Value:** Quality assurance

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_and_list_items():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create item
        response = await client.post("/items/", json={"name": "Test Item"})
        assert response.status_code == 201

        item_id = response.json()["id"]

        # List items
        response = await client.get("/items/")
        assert response.status_code == 200
        assert len(response.json()["items"]) > 0

        # Get item
        response = await client.get(f"/items/{item_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test Item"
```

### Pattern 87: Performance Testing with Locust
**When to Use:** Load testing
**Production Value:** Performance validation

```python
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def list_items(self):
        self.client.get("/items/")

    @task(3)
    def get_item(self):
        self.client.get("/items/1")

    @task
    def create_item(self):
        self.client.post("/items/", json={"name": "Test"})

# Run: locust -f locustfile.py --host=http://localhost:8000
```

### Pattern 88: Request Timeout Handling
**When to Use:** Long-running operations
**Production Value:** Reliability

```python
import asyncio
from fastapi import FastAPI

@app.post("/long-task/", timeout=30)
async def long_task(data: dict):
    try:
        result = await asyncio.wait_for(
            perform_heavy_computation(data),
            timeout=25
        )
        return {"result": result}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Request timeout")
```

### Pattern 89: Caching Database Queries with TTL
**When to Use:** Reducing database load
**Production Value:** Performance

```python
import json

@app.get("/items/")
async def get_items(db: AsyncSession = Depends(get_db)):
    cache_key = "items:all"

    # Try cache
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Query database
    result = await db.execute(select(Item))
    items = result.scalars().all()

    # Cache for 1 hour
    await redis_client.set(
        cache_key,
        json.dumps([{"id": item.id, "name": item.name} for item in items]),
        ex=3600
    )

    return items
```

### Pattern 90: Circuit Breaker Pattern
**When to Use:** Handling downstream failures
**Production Value:** Resilience

```python
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

@app.get("/external-api/")
async def call_external_api():
    try:
        result = await breaker.call(make_external_call)
        return result
    except Exception as e:
        logger.error(f"External API failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")
```

### Pattern 91: WebSocket Support
**When to Use:** Real-time communication
**Production Value:** Live updates

```python
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
```

### Pattern 92: Background Tasks with Celery
**When to Use:** Heavy async processing
**Production Value:** Scalable task queue

```python
from celery import Celery

celery_app = Celery('tasks', broker='redis://localhost:6379')

@celery_app.task
def process_document(file_path: str):
    # Heavy processing here
    return {"status": "completed", "file": file_path}

@app.post("/process/")
async def process(file_path: str):
    task = process_document.delay(file_path)
    return {"task_id": task.id, "status": "queued"}
```

### Pattern 93: Feature Flags
**When to Use:** Gradual rollouts
**Production Value:** Safe deployments

```python
from pydantic_settings import BaseSettings

class FeatureFlags(BaseSettings):
    enable_new_feature: bool = False
    enable_beta_api: bool = False

features = FeatureFlags()

@app.get("/items/")
async def get_items():
    if features.enable_new_feature:
        return {"items": [], "version": "v2"}
    return {"items": [], "version": "v1"}
```

### Pattern 94: Audit Logging
**When to Use:** Compliance and tracking
**Production Value:** Accountability

```python
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    action = Column(String)
    resource = Column(String)
    timestamp = Column(DateTime, default=datetime.now)
    details = Column(JSON)

async def log_audit(user_id: int, action: str, resource: str, details: dict = None):
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details
    )
    db.add(log)
    await db.commit()

# Usage
@app.post("/items/")
async def create_item(item: Item, user: User = Depends(get_current_user)):
    # ... create item ...
    await log_audit(user.id, "create", "item", {"item_id": new_item.id})
    return new_item
```

### Pattern 95: API Versioning with Headers
**When to Use:** Client-specified versioning
**Production Value:** Flexible versioning

```python
from fastapi import Header
from typing import Optional

@app.get("/items/")
async def get_items(
    accept_version: Optional[str] = Header("1.0")
):
    if accept_version == "2.0":
        return {"items": [], "metadata": {"version": "2.0"}}
    return {"items": [], "version": "1.0"}

# Client sends: Accept-Version: 2.0
```

### Pattern 96: Request Validation Middleware
**When to Use:** Global input validation
**Production Value:** Security

```python
import re

@app.middleware("http")
async def validate_input(request: Request, call_next):
    body = await request.body()

    # Check for SQL injection patterns
    sql_patterns = r"(DROP|DELETE|INSERT|UPDATE|UNION|SELECT.*FROM)"
    if re.search(sql_patterns, body.decode(), re.IGNORECASE):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid input detected"}
        )

    # Check for XSS patterns
    xss_patterns = r"(<script|javascript:|on\w+=)"
    if re.search(xss_patterns, body.decode(), re.IGNORECASE):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid input detected"}
        )

    response = await call_next(request)
    return response
```

### Pattern 97: Response Compression
**When to Use:** Large responses
**Production Value:** Bandwidth optimization

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Responses > 1KB are automatically compressed
# Typically reduces size by 60-80%
```

### Pattern 98: Request Logging Middleware
**When to Use:** Debugging and monitoring
**Production Value:** Observability

```python
import time
import logging

logger = logging.getLogger("api")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} "
        f"time={process_time:.3f}s"
    )

    return response
```

### Pattern 99: Health Check with Dependencies
**When to Use:** Comprehensive health monitoring
**Production Value:** Complete visibility

```python
@app.get("/health/")
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis)
):
    checks = {}

    # Database
    try:
        await db.execute(select(1))
        checks["database"] = "healthy"
    except:
        checks["database"] = "unhealthy"

    # Redis
    try:
        await redis.ping()
        checks["redis"] = "healthy"
    except:
        checks["redis"] = "unhealthy"

    # ML Model
    try:
        model.predict([[1, 2, 3]])
        checks["ml_model"] = "healthy"
    except:
        checks["ml_model"] = "unhealthy"

    all_healthy = all(v == "healthy" for v in checks.values())

    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks,
        "version": "1.0.0"
    }
```

### Pattern 100: Complete Production-Ready Template
**When to Use:** Starting new production project
**Production Value:** Best practices foundation

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from pydantic_settings import BaseSettings
import logging

# Settings
class Settings(BaseSettings):
    environment: str = "development"
    database_url: str
    redis_url: str
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up")
    db_pool = await setup_database()
    redis = await setup_redis()
    yield
    logger.info("Shutting down")
    await db_pool.close()
    await redis.close()

# App
app = FastAPI(
    title="Production API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Security headers
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

# Health check
@app.get("/health/")
async def health_check():
    return {"status": "healthy"}

# Routes
@app.post("/items/")
async def create_item(
    item_data: dict,
    db: AsyncSession = Depends(get_db)
):
    item = Item(**item_data)
    db.add(item)
    await db.commit()
    return item

# Production ready!
```

---

## Quick Reference: FastAPI Pattern Categories

| Category | Patterns | Use Case |
|----------|----------|----------|
| **Async Fundamentals** | 1-15 | Core FastAPI |
| **Request/Response** | 16-30 | Data handling |
| **Database** | 31-50 | Data persistence |
| **Authentication** | 51-60 | Security |
| **ML Serving** | 61-70 | AI integration |
| **Production** | 71-100 | Deployment |

---

## Master These 100 Patterns & You'll Be FastAPI Expert

1. **Patterns 1-15**: Master async, understand FastAPI fundamentals
2. **Patterns 16-30**: Build validated APIs with proper responses
3. **Patterns 31-50**: Work with databases like a pro
4. **Patterns 51-60**: Secure your APIs properly
5. **Patterns 61-70**: Serve ML models at scale
6. **Patterns 71-100**: Deploy production-grade systems

**Key to Success**: Implement 3-5 patterns per day. Apply them to real projects. Read production code. You'll master FastAPI!

---

*This guide is optimized for backend engineering and AI/ML API development. Every pattern includes working code and production considerations. Updated for 2025 with modern Pydantic v2, async SQLAlchemy 2.0, and lifespan events.*
