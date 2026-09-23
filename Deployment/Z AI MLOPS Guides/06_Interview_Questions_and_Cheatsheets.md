# Interview Questions & Cheatsheets — Job-Ready Pack

> "You don't rise to the level of your goals. You fall to the level of your preparation."
>
> This file has everything you need to walk into any MLOps / AI Engineer interview with confidence.

---

## Table of Contents

1. [Interview Question Bank (100+ Questions with Answers)](#1-interview-question-bank)
2. [FastAPI Cheatsheet](#2-fastapi-cheatsheet)
3. [Docker Cheatsheet](#3-docker-cheatsheet)
4. [Kubernetes Cheatsheet](#4-kubernetes-cheatsheet)
5. [MLflow Cheatsheet](#5-mlflow-cheatsheet)
6. [DVC Cheatsheet](#6-dvc-cheatsheet)
7. [GitHub Actions Cheatsheet](#7-github-actions-cheatsheet)
8. [Prometheus / Grafana Cheatsheet](#8-prometheus--grafana-cheatsheet)
9. [Python Async Cheatsheet](#9-python-async-cheatsheet)
10. [SQL Cheatsheet for ML](#10-sql-cheatsheet-for-ml)
11. [Behavioral Interview STAR Templates](#11-behavioral-interview-star-templates)
12. [System Design for ML — Frameworks](#12-system-design-for-ml--frameworks)
13. [The 7-Day Pre-Interview Cram Plan](#13-the-7-day-pre-interview-cram-plan)

---

## 1. Interview Question Bank

### MLOps Fundamentals

**Q1: What is MLOps and how is it different from DevOps?**

MLOps is the discipline of unifying ML systems development and operations. The key differences from DevOps:
1. **Inputs**: DevOps deals with code only. MLOps deals with code + data + hyperparameters.
2. **Outputs**: DevOps produces binaries. MLOps produces models + code + config + metrics.
3. **Testing**: DevOps tests logic. MLOps tests logic + data quality + model performance + fairness.
4. **Deployment**: DevOps deploys once per release. MLOps redeploys continuously (model drift).
5. **Monitoring**: DevOps monitors uptime/latency. MLOps also monitors drift, prediction distribution, ground truth feedback.

**Q2: Explain the ML lifecycle stages.**

1. Business problem framing
2. Data engineering
3. Experimentation (training)
4. Validation (offline + online)
5. Deployment
6. Monitoring
7. Retraining
8. Retirement

**Q3: What are the 3 MLOps maturity levels?**

- **Level 0**: Manual process. Notebooks, hand-coded training, manual deployment. No CI/CD.
- **Level 1**: ML pipeline automation. Reproducible training, experiment tracking, data versioning. CT introduced.
- **Level 2**: CI/CD pipeline automation. Full automation from commit to prod, multiple environments, automated rollback.

**Q4: What is model drift? Name two types.**

Model drift is the degradation of model performance over time. Two types:
1. **Data drift (covariate shift)**: Input feature distribution changes. Example: A model trained on 2020 customer behavior breaks when customers' habits change post-pandemic.
2. **Concept drift**: The relationship between features and target changes. Example: A fraud model trained when most transactions were in-store breaks when e-commerce dominates.

Detection methods: PSI (Population Stability Index), KS test, KL divergence, chi-square for categorical.

**Q5: What's the difference between training-serving skew and concept drift?**

- **Training-serving skew**: The features used at training differ from features at serving (preprocessing mismatch). It's a bug — fix it.
- **Concept drift**: The world changed. Retraining is needed.

**Q6: Name 5 components of an MLOps system.**

1. Experiment tracking (MLflow, W&B)
2. Data versioning (DVC, LakeFS)
3. Pipeline orchestration (Airflow, Prefect, Kubeflow)
4. Feature store (Feast, Tecton)
5. Model registry (MLflow Model Registry)
6. Model serving (BentoML, Seldon, KServe)
7. Monitoring (Evidently, Arize)

(Any 5 of these.)

**Q7: What is a feature store and why do you need one?**

A feature store is a centralized system that defines features once and computes them for both training (batch, offline) and serving (real-time, online). Benefits:
1. Eliminates training-serving skew (same code computes features both places)
2. Reusable across teams
3. Point-in-time correctness for training
4. Low-latency online serving

Examples: Feast (open-source), Tecton (managed), Hopsworks, SageMaker Feature Store.

**Q8: What's the difference between batch, real-time, and streaming inference?**

- **Batch**: Predictions pre-computed on a schedule, stored, then read by apps. Use case: nightly churn scoring.
- **Real-time (synchronous)**: API call returns prediction immediately. Use case: fraud check at checkout.
- **Streaming**: Predictions triggered by events on Kafka/Kinesis. Use case: real-time anomaly detection.

**Q9: What is a model registry? Why not just use a file system?**

A model registry is a centralized, versioned, auditable catalog of ML models. Features:
- Versioning (v1, v2, v3...)
- Stage transitions (None → Staging → Production → Archived)
- Lineage (which experiment run produced it)
- Metadata (metrics, params, training data)
- Audit trail (who promoted, when, why)

A file system can't do any of this reliably. Use MLflow Model Registry, W&B Registry, or cloud-native (Vertex, SageMaker).

**Q10: What is continuous training (CT)?**

CT is the automated, scheduled, or triggered retraining of ML models. Triggers include:
- Schedule (daily/weekly)
- Data-driven (N new labeled rows arrive)
- Drift-driven (PSI > threshold)
- Performance-driven (F1 drops below floor)
- Manual

CT is what differentiates MLOps from DevOps.

### FastAPI / API Development

**Q11: Why FastAPI over Flask for ML APIs?**

- Async-first (handles thousands of concurrent requests)
- Type hints → automatic validation via Pydantic
- Auto-generated OpenAPI docs at /docs
- Built-in dependency injection
- Comparable speed to Node.js/Go
- Modern Python features (async/await, type hints)

**Q12: When should you use `async def` vs `def` in FastAPI?**

- `async def`: When the function does async I/O (async DB, async HTTP, async file)
- `def`: When the function does CPU work or sync I/O. FastAPI runs these in a threadpool, so they don't block the event loop.

For ML inference (CPU/GPU work), use `def` OR `async def` with `run_in_executor`.

**Q13: What is Pydantic and why is it useful?**

Pydantic is a data validation library that uses Python type hints. Benefits:
- Automatic validation (rejects bad input with 422)
- Automatic serialization (Python objects ↔ JSON)
- Auto-generated OpenAPI schema
- Nested models supported
- Custom validators via `@field_validator`

**Q14: How do you load a model in FastAPI without loading it on every request?**

Use `lifespan` (the modern way):

```python
from contextlib import asynccontextmanager

ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    ml_models["churn"] = joblib.load("model.pkl")
    yield
    ml_models.clear()

app = FastAPI(lifespan=lifespan)
```

**Q15: What's the difference between `Depends()` and `Security()`?**

Both work the same way, but `Security()` lets you declare `scopes` for OAuth2. Use `Security()` for auth dependencies, `Depends()` for everything else.

**Q16: How do you handle errors in FastAPI?**

Three ways:
1. Raise `HTTPException` in your code (returns the specified status + detail)
2. Custom exception handlers via `@app.exception_handler(MyException)`
3. Middleware to catch unhandled exceptions

Always return standardized error responses.

**Q17: How do you implement rate limiting in FastAPI?**

Options:
1. **In-memory**: dict with timestamps per API key. Simple, not for multi-instance.
2. **Redis**: `INCR` + `EXPIRE` per minute window. Distributed, production-grade.
3. **slowapi library**: Decorator-based, easy.

For production: Redis with sliding window (Lua script for accuracy).

**Q18: How do you do streaming responses in FastAPI?**

```python
from fastapi.responses import StreamingResponse

@app.post("/stream")
async def stream(req: Request):
    async def gen():
        async for token in llm_stream(req):
            yield f"data: {token}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")
```

Critical for LLM APIs — users want to see tokens stream, not wait for full response.

**Q19: What's the difference between WebSocket and SSE?**

- **SSE (Server-Sent Events)**: Server → client only. HTTP-based. Simple. Use for LLM token streaming.
- **WebSocket**: Bidirectional. Persistent connection. Use for chat apps, multiplayer games.

For LLM APIs where client sends one request and server streams tokens back, SSE is simpler and sufficient.

**Q20: How do you test a FastAPI app?**

Use `TestClient` (sync) or `AsyncClient` from `httpx` (async):

```python
from fastapi.testclient import TestClient
client = TestClient(app)

def test_predict():
    r = client.post("/predict", json={...})
    assert r.status_code == 200
```

For async, use `pytest-asyncio` + `httpx.AsyncClient(app=app)`.

### Docker

**Q21: What's the difference between an image and a container?**

- **Image**: Read-only template (blueprint). Built from Dockerfile.
- **Container**: Running instance of an image. Mutable, ephemeral.

Multiple containers can run from the same image.

**Q22: How do you reduce Docker image size?**

1. Use slim/alpine base images
2. Multi-stage builds
3. `.dockerignore` to exclude build context
4. Combine RUN commands (fewer layers)
5. Don't install dev deps in prod image
6. Clear apt/pip caches within the same RUN command

**Q23: What's a multi-stage build?**

A Dockerfile with multiple `FROM` statements. The first stage (builder) compiles/installs; later stages copy only what's needed. Reduces image size by excluding build tools.

```dockerfile
FROM python:3.11 AS builder
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
```

**Q24: What's the difference between CMD and ENTRYPOINT?**

- **CMD**: Default command, easily overridden by `docker run my-image other-command`
- **ENTRYPOINT**: The command always runs; CMD becomes arguments to it

Best practice for ML APIs: use `CMD` (flexible). Use `ENTRYPOINT` for "run this script always" containers.

**Q25: How do you pass secrets to Docker containers?**

Three ways (in order of preference):
1. **Environment variables** (simple, but visible in `docker inspect`)
2. **Docker secrets** (Swarm/K8s only, more secure)
3. **Mount secret files** (read from `/run/secrets/...`)

Never bake secrets into images. Never commit `.env` to git.

**Q26: How do you debug a Docker container that won't start?**

```bash
# Check logs
docker logs <container>

# Inspect the image
docker inspect <image>

# Run with shell entrypoint to explore
docker run -it --entrypoint bash my-image

# Check the container's filesystem (even if exited)
docker cp <container>:/app /tmp/debug
```

### Kubernetes

**Q27: What is a Pod in Kubernetes?**

A Pod is the smallest deployable unit in K8s. It contains 1+ containers that share network + storage. Most Pods run a single container.

**Q28: What's the difference between a Deployment and a StatefulSet?**

- **Deployment**: For stateless apps. Pods are interchangeable. Use for APIs, web servers.
- **StatefulSet**: For stateful apps. Pods have stable identities (name-0, name-1, ...) and persistent storage. Use for databases, message queues.

**Q29: How does a Service route traffic to Pods?**

A Service has a selector (e.g., `app: churn-api`) and routes to all Pods matching that selector. It provides a stable DNS name (e.g., `churn-api.ml-prod.svc.cluster.local`) and load-balances across Pods.

**Q30: What's the difference between ClusterIP, NodePort, and LoadBalancer services?**

- **ClusterIP** (default): Internal only. Only reachable from within cluster.
- **NodePort**: Exposes on each node's IP at a static port (30000-32767).
- **LoadBalancer**: Cloud provider provisions an external load balancer (ELB, etc.). Production-grade.

For ML APIs, use ClusterIP + Ingress (TLS, routing, rate limiting).

**Q31: What's an Ingress?**

An Ingress is an L7 routing rule that maps HTTP/HTTPS paths/hosts to Services. Requires an Ingress Controller (nginx, traefik, alb). Handles TLS termination, virtual hosts, path-based routing.

**Q32: How do you do a rolling update?**

K8s does this automatically when you change a Deployment's image:
```bash
kubectl set image deployment/api api=myuser/api:v2
kubectl rollout status deployment/api
```

Controlled by `strategy.rollingUpdate.maxUnavailable` and `maxSurge` in the Deployment spec.

**Q33: How do you roll back a deployment?**

```bash
kubectl rollout undo deployment/api
# Or to specific revision
kubectl rollout undo deployment/api --to-revision=2
kubectl rollout history deployment/api
```

**Q34: What are liveness, readiness, and startup probes?**

- **liveness**: "Is the app alive?" If fails, restart container.
- **readiness**: "Is the app ready to serve?" If fails, remove from Service endpoints (no traffic).
- **startup**: "Has the app started?" Disables liveness/readiness until success. Useful for slow-starting apps (model loading).

```yaml
livenessProbe:
  httpGet: { path: /health/live, port: 8000 }
readinessProbe:
  httpGet: { path: /health/ready, port: 8000 }
startupProbe:
  httpGet: { path: /health/live, port: 8000 }
  failureThreshold: 30
  periodSeconds: 10
```

**Q35: How do you request GPUs in K8s?**

```yaml
resources:
  limits:
    nvidia.com/gpu: 1
```

Requires NVIDIA Device Plugin installed on the cluster. The node must have GPUs.

**Q36: What's a ConfigMap vs a Secret?**

- **ConfigMap**: Non-sensitive config (log level, feature flags, model name). Stored as plain text.
- **Secret**: Sensitive data (API keys, passwords, certs). Stored as base64 (NOT encrypted by default — enable encryption at rest).

Both can be mounted as env vars or files.

**Q37: How does HPA work?**

HorizontalPodAutoscaler watches a metric (CPU, memory, or custom). When the average crosses a threshold, it scales the Deployment's replica count. Requires Metrics Server.

```yaml
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      type: Utilization
      averageUtilization: 70
```

**Q38: What's a Helm chart?**

A Helm chart is a packaged set of K8s manifests with templated values. Lets you install complex apps with one command: `helm install ml-api ./chart`. Like `apt` for Kubernetes.

**Q39: What's GitOps?**

GitOps is a deployment paradigm where Git is the single source of truth. You commit changes to Git; a tool (ArgoCD, Flux) automatically syncs the cluster to match. Benefits: audit trail, easy rollback, no kubectl access needed for devs.

**Q40: How do you debug a Pod that's CrashLoopBackOff?**

```bash
# 1. Describe the pod (look at Events section)
kubectl describe pod <pod>

# 2. Check logs (current and previous container)
kubectl logs <pod>
kubectl logs <pod> --previous

# 3. Exec into the pod (if it's running)
kubectl exec -it <pod> -- bash

# 4. Check resource usage
kubectl top pod <pod>

# 5. Check node resources
kubectl describe node <node>
```

Common causes: missing env vars, missing secrets, command/args wrong, OOMKilled, app crashes on startup.

### CI/CD

**Q41: What's the difference between Continuous Delivery and Continuous Deployment?**

- **Continuous Delivery**: Every successful build is *deployable* with one click. Deployment is a manual choice.
- **Continuous Deployment**: Every successful build is *automatically deployed* to prod. No human approval.

Most enterprises do CD (delivery). High-velocity companies (Netflix, Etsy) do CD (deployment).

**Q42: Write a GitHub Actions workflow that runs tests on PRs.**

```yaml
name: CI
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: pip }
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```

**Q43: How do you cache dependencies in GitHub Actions?**

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.11"
    cache: pip  # auto-caches based on requirements.txt
```

Or for custom caching:
```yaml
- uses: actions/cache@v4
  with:
    path: .dvc/cache
    key: dvc-${{ hashFiles('**/*.dvc') }}
```

**Q44: How do you require manual approval before production deploy?**

Use GitHub Environments:
```yaml
jobs:
  deploy-prod:
    environment: production  # requires approval in repo settings
    runs-on: ubuntu-latest
    steps: ...
```

Or for Jenkins: `input { message "Deploy?" }`

**Q45: How do you do canary deployment in CI/CD?**

Use Argo Rollouts or Flagger:
1. Deploy new version with 5% traffic
2. Wait X minutes, check SLOs (error rate, latency)
3. If OK, ramp to 25%, then 50%, then 100%
4. If SLO breached, auto-rollback

Without these tools: use Istio VirtualService to split traffic between two deployments.

### ML Specific

**Q46: What's training-serving skew? How do you prevent it?**

Training-serving skew is when features computed differently at training vs serving. Causes:
1. Different preprocessing code in train vs serve
2. Different library versions
3. Different feature definitions

Prevention:
1. Use the same code path (e.g., a `preprocess.py` module imported by both)
2. Use a feature store (Feast) — features defined once
3. Pin library versions in Docker

**Q47: How do you detect data drift in production?**

1. **PSI (Population Stability Index)**: Compare distribution bins. PSI > 0.2 = significant drift.
2. **KS test**: Statistical test for distribution difference (continuous features).
3. **Chi-square test**: For categorical features.
4. **KL divergence**: Information-theoretic measure.
5. **Evidently library**: Computes all of these automatically.

Alert when drift is detected → trigger retraining.

**Q48: What's the difference between offline and online evaluation?**

- **Offline**: Held-out test set, computed before deployment. F1, AUC, RMSE.
- **Online**: Real users in production. A/B test, bandit, business metrics.

Online is more important — it reflects real impact. But it's harder and slower (need statistically significant sample).

**Q49: How do you A/B test an ML model?**

1. Split live traffic (e.g., 90% control / 10% treatment)
2. Define business metric (conversion, revenue, retention)
3. Compute required sample size for statistical significance
4. Run until sample size reached
5. Compute p-value; if p < 0.05, declare winner
6. Promote winner to 100% traffic

Tools: Optimizely, GrowthBook, Statsig, or build your own with feature flags.

**Q50: What's a model card?**

A model card is documentation for an ML model. Contains:
- Intended use
- Training data description
- Evaluation metrics
- Ethical considerations
- Limitations
- Caveats

Originated from Google (Mitchell et al., 2019). Required for compliance in regulated industries (finance, healthcare).

**Q51: How do you handle the cold-start problem in recommendations?**

Cold start = new user/item with no history. Solutions:
1. **Content-based**: Use item/user metadata (genre, tags, demographics)
2. **Popularity**: Recommend most popular items
3. **Onboarding survey**: Ask new users for preferences
4. **Hybrid**: Combine content + collaborative filtering
5. **Multi-armed bandit**: Explore-exploit trade-off

**Q52: How would you serve a 7B parameter LLM in production?**

1. **Quantization**: Convert FP16 → INT8 or INT4. 2-4x smaller, minimal quality loss.
2. **vLLM or TGI**: High-throughput serving engines with PagedAttention
3. **GPU**: At least 1x A10G (24GB) for INT8 7B
4. **Batching**: Continuous batching for throughput
5. **Caching**: Prefix caching for common system prompts
6. **Streaming**: SSE for token-by-token responses
7. **Load balancing**: Multiple replicas behind LB

**Q53: What's RAG and when do you use it?**

RAG = Retrieval Augmented Generation. Pattern: retrieve relevant documents → feed to LLM as context → LLM generates answer using those documents.

Use when:
- Knowledge is too large to fit in context
- Knowledge changes frequently (no need to retrain)
- Need citations / explainability
- Want to use a smaller model with external knowledge

Stack: Vector DB (Pinecone, Weaviate, pgvector) + Embeddings (text-embedding-3-small) + LLM (GPT-4, Claude).

**Q54: How do you minimize LLM API costs?**

1. **Prompt caching**: Cache responses for common prompts
2. **Model tiering**: Use GPT-3.5 for simple tasks, GPT-4 for complex
3. **Prompt engineering**: Shorter prompts = fewer tokens
4. **Batch API**: 50% discount for async batch jobs
5. **Fine-tune small model**: Often cheaper than calling GPT-4
6. **Local models**: For high-volume, run Llama-3-8B locally
7. **Token counting**: Reject prompts exceeding budget before sending to API

**Q55: How do you handle PII in ML pipelines?**

1. **Detection**: Use Presidio or AWS Comprehend to detect PII in data
2. **Redaction**: Mask/redact before training
3. **Differential privacy**: Add noise during training (DP-SGD)
4. **Access controls**: Role-based, audit logged
5. **Data residency**: Keep EU data in EU regions (GDPR)
6. **Retention policies**: Auto-delete after N days

### System Design (ML)

**Q56: Design a real-time fraud detection system.**

Requirements: 1M transactions/day, p99 latency < 100ms, 24/7.

Components:
1. **Ingestion**: Kafka (transactions stream)
2. **Feature store**: Feast (online + offline)
3. **Model**: XGBoost (fast inference, ~5ms)
4. **Serving**: FastAPI on K8s with GPU (for feature engineering)
5. **Decisioning**: API returns risk score → business rules block/allow
6. **Feedback loop**: Label as fraud/not fraud later → retrain daily
7. **Monitoring**: Drift detection, latency SLOs
8. **Storage**: Snowflake (training data), Redis (online features), S3 (model artifacts)

**Q57: Design a recommendation system for an e-commerce site.**

Two-tower:
1. **Candidate generation**: Collaborative filtering (matrix factorization) → top 1000 candidates
2. **Ranking**: Gradient-boosted trees with features (user, item, context) → top 10
3. **Real-time serving**: Embeddings in vector DB, fast ANN search (HNSW)
4. **Cold start**: Content-based for new users/items
5. **Feedback loop**: Clicks/purchases logged → retrain weekly

**Q58: Design a chatbot API (OpenAI-compatible).**

1. **API**: FastAPI, OpenAI-compatible endpoints (`/v1/chat/completions`, `/v1/models`)
2. **Auth**: API keys (Bearer token)
3. **Rate limiting**: Redis-backed, per-tenant
4. **Model serving**: vLLM for high throughput
5. **Streaming**: SSE for token streaming
6. **Load balancing**: Multiple GPU replicas, sticky sessions for KV cache
7. **Observability**: Prometheus (latency, tokens/s), trace each request
8. **Billing**: Token usage logged per request → Stripe

**Q59: How would you deploy a model that needs 30 seconds to inference?**

Synchronous API won't work. Options:
1. **Async pattern**: Submit job → get job_id → poll for result
2. **Background tasks**: Use Celery/RQ, return 202 Accepted with job_id
3. **Streaming**: If intermediate results (LLM tokens), use SSE
4. **Batch**: Pre-compute overnight, store, look up

For 30s model: async pattern with job queue (SQS, Celery+Redis).

**Q60: How would you migrate a model from v1 to v2 with zero downtime?**

1. Deploy v2 in shadow mode (receives traffic, predictions logged, not served)
2. Compare v1 vs v2 predictions on same inputs for 1 week
3. Promote v2 to canary (5% real traffic)
4. Monitor SLOs (errors, latency, business metrics) for 1 day
5. Ramp: 5% → 25% → 50% → 100%
6. Auto-rollback on SLO breach
7. Decommission v1 after 1 week stable

---

## 2. FastAPI Cheatsheet

### Setup

```bash
pip install fastapi uvicorn[standard]
uvicorn main:app --reload --port 8000
```

### App Creation

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    app.state.model = load_model()
    yield
    # shutdown
    app.state.model = None

app = FastAPI(
    title="My API",
    version="1.0.0",
    lifespan=lifespan,
)
```

### Path Operations

```python
@app.get("/items/{id}")
async def get_item(id: int): ...

@app.post("/items")
async def create_item(item: Item): ...

@app.put("/items/{id}")
async def update_item(id: int, item: Item): ...

@app.delete("/items/{id}")
async def delete_item(id: int): ...
```

### Pydantic Models

```python
from pydantic import BaseModel, Field, field_validator

class User(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=100)
    email: str
    age: int = Field(0, ge=0, le=150)
    
    @field_validator("email")
    @classmethod
    def valid_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email")
        return v
```

### Dependency Injection

```python
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/{id}")
def get_user(id: int, db = Depends(get_db)):
    return db.query(User).get(id)
```

### Auth

```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_key(key: str = Security(api_key_header)):
    if key not in VALID_KEYS:
        raise HTTPException(401, "Invalid key")
    return key

@app.post("/predict", dependencies=[Depends(verify_key)])
def predict(...): ...
```

### Background Tasks

```python
from fastapi import BackgroundTasks

@app.post("/predict")
async def predict(req: Request, bg: BackgroundTasks):
    result = do_predict(req)
    bg.add_task(send_notification, result)  # runs after response
    return result
```

### Streaming

```python
from fastapi.responses import StreamingResponse

@app.post("/stream")
async def stream():
    async def gen():
        for i in range(10):
            yield f"data: {i}\n\n"
            await asyncio.sleep(0.5)
    return StreamingResponse(gen(), media_type="text/event-stream")
```

### Middleware

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    print(f"{request.method} {request.url.path} → {response.status_code} ({duration:.2f}s)")
    return response
```

### Testing

```python
from fastapi.testclient import TestClient
client = TestClient(app)

def test_predict():
    r = client.post("/predict", json={...})
    assert r.status_code == 200
```

---

## 3. Docker Cheatsheet

### Dockerfile Template

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd -m -u 1000 appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

### Common Commands

```bash
# Build
docker build -t myapp:v1 .

# Run
docker run -p 8000:8000 myapp:v1
docker run -it myapp:v1 bash           # interactive
docker run --rm myapp:v1 pytest        # one-shot

# Manage
docker ps                              # running containers
docker ps -a                           # all containers
docker images                          # list images
docker rmi <image>                     # remove image
docker rm <container>                  # remove container

# Debug
docker logs <container>                # view logs
docker logs -f <container>             # follow logs
docker exec -it <container> bash       # exec in
docker inspect <container>             # full info

# Clean up
docker system prune -a                 # remove everything unused
docker volume prune                    # remove unused volumes

# Compose
docker compose up -d                   # start in background
docker compose logs -f api             # tail logs
docker compose down                    # stop + remove
docker compose down -v                 # also remove volumes
```

### Multi-Stage Build

```dockerfile
FROM python:3.11 AS builder
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
```

### GPU

```dockerfile
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04
RUN apt-get update && apt-get install -y python3 python3-pip
```

```bash
docker run --gpus all my-image
```

### .dockerignore

```
.git
__pycache__
*.pyc
venv/
.env
data/
models/
*.md
```

---

## 4. Kubernetes Cheatsheet

### Common kubectl Commands

```bash
# Get info
kubectl get pods -A                   # all pods all namespaces
kubectl get pods -o wide              # more details
kubectl get svc,deployment,ingress    # multiple resource types
kubectl describe pod <pod>            # full info
kubectl get nodes -o wide

# Logs
kubectl logs <pod>
kubectl logs -f <pod>                 # follow
kubectl logs <pod> --previous         # last crashed container
kubectl logs <pod> -c <container>     # specific container

# Exec
kubectl exec -it <pod> -- bash
kubectl exec -it <pod> -- python script.py

# Apply / Delete
kubectl apply -f deployment.yaml
kubectl apply -f ./k8s/               # all YAMLs in dir
kubectl delete -f deployment.yaml
kubectl delete pod <pod>              # kill (Deployment recreates)

# Scale
kubectl scale deployment api --replicas=5
kubectl autoscale deployment api --min=3 --max=10 --cpu-percent=70

# Rolling
kubectl set image deployment/api api=myuser/api:v2
kubectl rollout status deployment/api
kubectl rollout undo deployment/api
kubectl rollout history deployment/api

# Port forward (debug)
kubectl port-forward svc/api 8080:80

# Config
kubectl config get-contexts
kubectl config use-context <name>

# Namespaces
kubectl create ns ml-prod
kubectl config set-context --current --namespace=ml-prod

# Events
kubectl get events --sort-by=.lastTimestamp

# Resources
kubectl top pod
kubectl top node
```

### Deployment Template

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-api
  template:
    metadata:
      labels:
        app: my-api
    spec:
      containers:
      - name: api
        image: myuser/my-api:v1
        ports: [{containerPort: 8000}]
        resources:
          requests: {cpu: 250m, memory: 512Mi}
          limits: {cpu: 1000m, memory: 1Gi}
        livenessProbe:
          httpGet: {path: /health/live, port: 8000}
        readinessProbe:
          httpGet: {path: /health/ready, port: 8000}
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-api
spec:
  selector:
    app: my-api
  ports:
  - port: 80
    targetPort: 8000
```

### HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-api
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

## 5. MLflow Cheatsheet

### Setup

```bash
pip install mlflow
mlflow server --backend-store-uri sqlite:///mlflow.db --port 5000
```

### Tracking

```python
import mlflow

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("my-experiment")

with mlflow.start_run(run_name="my-run"):
    mlflow.log_params({"lr": 0.01, "epochs": 10})
    mlflow.log_metrics({"accuracy": 0.85, "loss": 0.32})
    mlflow.log_artifact("confusion_matrix.png")
    mlflow.sklearn.log_model(model, "model")
```

### Autologging

```python
mlflow.sklearn.autolog()  # or xgboost, tensorflow, etc.
# Now any .fit() call auto-logs params + metrics
```

### Model Registry

```python
client = mlflow.tracking.MlflowClient()

# Create registered model
client.create_registered_model("churn-prediction")

# Create version from a run
client.create_model_version(
    name="churn-prediction",
    source="runs:/<run_id>/model",
    run_id="<run_id>",
)

# Transition stages
client.transition_model_version_stage(
    name="churn-prediction",
    version=1,
    stage="Staging",  # or "Production", "Archived"
    archive_existing_versions=True,  # auto-archive previous prod
)

# Load Production model
model = mlflow.sklearn.load_model("models:/churn-prediction/Production")
```

### Serve a Model

```bash
mlflow models serve -m "models:/churn-prediction/Production" --port 5001
```

---

## 6. DVC Cheatsheet

### Setup

```bash
pip install dvc
git init && dvc init
dvc remote add -d storage s3://my-bucket/dvc
```

### Data Versioning

```bash
dvc add data/raw/customers.csv     # creates .dvc pointer (commit to git)
dvc push                            # upload to remote
dvc pull                            # download from remote
dvc checkout                        # restore data for current commit
```

### Pipeline (dvc.yaml)

```yaml
stages:
  prepare:
    cmd: python src/prepare.py
    deps: [src/prepare.py, data/raw]
    outs: [data/processed]
  train:
    cmd: python src/train.py
    deps: [src/train.py, data/processed]
    outs: [models/model.pkl]
  evaluate:
    cmd: python src/evaluate.py
    deps: [src/evaluate.py, models/model.pkl]
    metrics: [metrics/eval.json]
```

### Commands

```bash
dvc repro                # run pipeline (only changed stages)
dvc repro -f             # force re-run all
dvc dag                  # visualize pipeline
dvc metrics show         # show metrics
dvc metrics diff         # compare to previous commit
dvc push                 # push data to remote
dvc pull                 # pull data from remote
```

---

## 7. GitHub Actions Cheatsheet

### Workflow Structure

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: "0 2 * * 0"  # weekly Sunday
  workflow_dispatch:     # manual

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - run: pip install -r requirements.txt
      - run: pytest
```

### Useful Snippets

```yaml
# Conditional step
- name: Deploy
  if: github.ref == 'refs/heads/main'
  run: ./deploy.sh

# Matrix (test on multiple Python versions)
strategy:
  matrix:
    python-version: ["3.10", "3.11", "3.12"]

# Secrets
env:
  API_KEY: ${{ secrets.API_KEY }}

# Manual approval gate (Environments)
environment: production

# Cache
- uses: actions/cache@v4
  with:
    path: .dvc/cache
    key: dvc-${{ hashFiles('**/*.dvc') }}

# Upload artifact
- uses: actions/upload-artifact@v4
  with:
    name: metrics
    path: metrics/

# Service container (Postgres)
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_PASSWORD: test
    ports: ["5432:5432"]
```

---

## 8. Prometheus / Grafana Cheatsheet

### PromQL Queries

```promql
# Request rate (per second, last 5 min)
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# p99 latency
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Average CPU per pod
rate(container_cpu_usage_seconds_total[5m])

# Memory usage
container_memory_usage_bytes / container_spec_memory_limit_bytes

# Top 5 pods by CPU
topk(5, rate(container_cpu_usage_seconds_total[5m]))

# Predictions per minute
rate(predictions_total[1m]) * 60
```

### Custom Metrics in FastAPI

```python
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

PREDICTIONS = Counter("predictions_total", "Predictions", ["model"])
LATENCY = Histogram("prediction_latency_seconds", "Latency")

@app.post("/predict")
def predict():
    with LATENCY.time():
        result = model.predict(...)
    PREDICTIONS.labels(model="v1").inc()
    return result
```

### Grafana Dashboard JSON

Just use the dashboards from `grafana.com/dashboards`:
- ID 3119: Kubernetes cluster overview
- ID 12740: FastAPI
- ID 179: Node exporter

---

## 9. Python Async Cheatsheet

### When to Use async

```python
# SYNC (use def in FastAPI)
def predict_sync(features):
    # CPU-bound work, sync I/O
    return model.predict(features)

# ASYNC (use async def)
async def predict_async(features):
    # Async I/O (DB, HTTP, file)
    features = await fetch_features()
    return await model.predict_async(features)
```

### Running Sync Code in Async

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

async def predict(features):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, model.predict, features)
```

### Gathering Concurrent Operations

```python
import asyncio
import httpx

async def fetch_all(urls):
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
```

### Async Patterns

```python
# Semaphore (limit concurrency)
sem = asyncio.Semaphore(10)
async def limited_fetch(url):
    async with sem:
        return await httpx.get(url)

# Wait for first N to complete
done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

# Timeout
try:
    result = await asyncio.wait_for(slow_call(), timeout=10)
except asyncio.TimeoutError:
    print("Timed out")
```

---

## 10. SQL Cheatsheet for ML

### Common Patterns

```sql
-- Aggregate by time bucket
SELECT
    date_trunc('hour', created_at) AS hour,
    COUNT(*) AS request_count,
    AVG(latency_ms) AS avg_latency,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms) AS p99
FROM api_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour;

-- Join predictions with outcomes (for offline eval)
SELECT
    p.request_id,
    p.prediction,
    p.predicted_at,
    o.actual_outcome,
    CASE WHEN p.prediction = o.actual_outcome THEN 1 ELSE 0 END AS correct
FROM predictions p
LEFT JOIN outcomes o ON p.request_id = o.request_id
WHERE p.predicted_at > NOW() - INTERVAL '7 days';

-- Top customers by prediction value
SELECT
    customer_id,
    AVG(churn_probability) AS avg_churn_prob,
    COUNT(*) AS predictions_count
FROM predictions
WHERE predicted_at > NOW() - INTERVAL '30 days'
GROUP BY customer_id
HAVING AVG(churn_probability) > 0.5
ORDER BY avg_churn_prob DESC
LIMIT 100;

-- Cohort analysis (retention)
WITH cohorts AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', signup_date) AS cohort_month
    FROM customers
),
activity AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', activity_date) AS active_month
    FROM customer_activity
)
SELECT
    c.cohort_month,
    COUNT(DISTINCT c.customer_id) AS cohort_size,
    a.active_month,
    COUNT(DISTINCT a.customer_id) AS active_users,
    COUNT(DISTINCT a.customer_id)::FLOAT / COUNT(DISTINCT c.customer_id) AS retention_rate
FROM cohorts c
LEFT JOIN activity a ON c.customer_id = a.customer_id
GROUP BY 1, 3
ORDER BY 1, 3;
```

### Useful Window Functions

```sql
-- Row number (top 1 per group)
SELECT * FROM (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC) AS rn
    FROM predictions
) t WHERE rn = 1;

-- Moving average
SELECT
    date,
    value,
    AVG(value) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma_7d
FROM daily_metrics;

-- Cumulative sum
SELECT
    date,
    revenue,
    SUM(revenue) OVER (ORDER BY date) AS cumulative_revenue
FROM daily_revenue;
```

---

## 11. Behavioral Interview STAR Templates

### Template 1: "Tell me about a project you're proud of."

**Situation**: At my previous role, our churn prediction model was deployed but had no monitoring. We discovered it had degraded from F1=0.83 to F1=0.62 over 4 months without anyone noticing, costing the company an estimated $200k in lost retention.

**Task**: I was asked to design and implement a monitoring system that would detect such degradation automatically.

**Action**: I evaluated several monitoring tools (Arize, Fiddler, Evidently) and chose Evidently for its open-source nature and Python-native API. I implemented:
1. Daily drift detection on input features using PSI
2. Weekly ground-truth comparison when labels arrived
3. Alerting via Slack and PagerDuty when PSI > 0.2
4. Auto-trigger of retraining pipeline via Prefect

I also wrote runbooks for the on-call engineer explaining how to interpret alerts and what actions to take.

**Result**: Within 2 weeks of deployment, the system caught a drift event early (after a major product change), triggered retraining, and the new model restored F1 to 0.81 — all before the business impact became material. The CTO cited this as a model for how all our ML systems should be monitored going forward.

### Template 2: "Tell me about a time you disagreed with a teammate."

**Situation**: My teammate wanted to deploy a model directly to production after only offline evaluation. I argued for a canary deployment.

**Task**: Convince the team that canary deployment was worth the extra engineering effort.

**Action**: I prepared a 1-pager showing:
1. The cost of canary infrastructure (~1 day of engineering)
2. The expected cost of a bad model deploy (lost revenue + brand damage + remediation time)
3. A real example from a competitor who had skipped canary and shipped a biased model that went viral negatively

I also offered to do the extra engineering work myself if the team agreed.

**Result**: The team agreed. The first canary deploy caught a 2x latency regression that offline testing missed (we hadn't tested with realistic feature payloads). We rolled back in 10 minutes. The team adopted canary as standard practice for all model deploys after that.

### Template 3: "Describe a technical challenge you faced."

**Situation**: Our LLM API was getting 5x more traffic than expected after a product launch, and p99 latency went from 800ms to 5s.

**Task**: Reduce latency without provisioning 5x more GPUs (cost-prohibitive).

**Action**: I profiled the system and found:
1. **No batching**: Each request ran a separate forward pass. → Implemented continuous batching via vLLM
2. **Cold KV cache**: Each request computed attention from scratch. → Enabled prefix caching for the common system prompt
3. **No connection pooling**: Each request opened a new HTTPX connection to the model server. → Reused a connection pool
4. **Synchronous post-processing**: After getting a response, we did 3 sync API calls (logging, billing, analytics). → Moved to background tasks

**Result**: p99 latency dropped from 5s to 700ms. Throughput increased 4x. Cost per request dropped 60%. We handled the 5x traffic surge without adding any GPUs.

---

## 12. System Design for ML — Frameworks

### Framework: CIRCLES Method (adapted for ML)

1. **Comprehend** the requirements
2. **Identify** the users
3. **Report** the overall design
4. **Cut** through priorities (latency vs accuracy vs cost)
5. **List** the components
6. **E**valuate trade-offs
7. **Summarize**

### 5-Step ML System Design

1. **Problem framing** (10 min)
   - What's the business metric? (revenue, retention, cost)
   - What's the ML metric? (F1, NDCG, RMSE)
   - What are constraints? (latency, fairness, cost)

2. **Data** (10 min)
   - Where does it come from?
   - How is it labeled?
   - Volume, velocity, variety
   - Privacy/compliance constraints

3. **Modeling** (10 min)
   - Baseline (heuristics, simple model)
   - Production model (architecture)
   - Offline evaluation
   - Fairness/bias considerations

4. **Serving** (10 min)
   - Real-time vs batch vs streaming
   - Latency SLO
   - Throughput requirements
   - Rollout strategy (canary, shadow)

5. **Monitoring** (10 min)
   - Operational metrics
   - ML metrics (drift, quality)
   - Retraining triggers
   - Alert routing

### Example: "Design YouTube recommendations"

**Problem**: Recommend videos to maximize engagement (watch time) + user satisfaction.

**Data**: User watch history, search history, demographics, video metadata, explicit feedback (likes, not-interested), implicit feedback (watch time, completion rate).

**Modeling**:
- Candidate generation: Two-tower neural network (user embedding + video embedding), ANN search → 1000 candidates
- Ranking: Gradient-boosted trees with hundreds of features (user, video, context) → top 20
- Multi-objective: predict watch time, satisfaction, engagement → combine with weights

**Serving**:
- Real-time (< 200ms)
- Distributed model serving on TPUs
- Cache embeddings in memory
- Pre-compute embeddings for new videos in batch

**Monitoring**:
- Watch time per session (engagement)
- Session retention (satisfaction)
- Drift on feature distributions
- A/B test every model change (50M+ users per arm for significance)
- Auto-rollback on metric regression

---

## 13. The 7-Day Pre-Interview Cram Plan

### Day 7 (1 week before): Resume + Portfolio Review

- Update resume: 1-page, action verbs, quantified impact
- Pin your top 3 GitHub projects on profile
- Make sure each project README has: architecture diagram, "what I learned", screenshot
- Prepare 2-min verbal walkthrough of each project

### Day 6: Behavioral Prep

- Write out STAR stories for:
  - "Tell me about yourself"
  - "Tell me about a project you're proud of"
  - "Tell me about a time you failed"
  - "Tell me about a conflict with a teammate"
  - "Why this company?"
- Practice saying them OUT LOUD, not just reading

### Day 5: MLOps Theory

- Re-read File 1 sections: MLOps maturity levels, ML lifecycle, drift types
- Re-read File 2 sections: 4 pipeline types, promotion strategies
- Quiz yourself on the 60 interview questions above

### Day 4: Coding Practice

- Solve 5 easy + 5 medium LeetCode (Python)
- Focus on: arrays, hashmaps, two pointers, sliding window
- Time-box: 25 min per problem max
- Practice talking through solution out loud

### Day 3: System Design Practice

- Pick 3 ML system design questions:
  - "Design a recommendation system"
  - "Design a real-time fraud detection system"
  - "Design an LLM API gateway"
- Practice drawing the architecture on a whiteboard / Excalidraw
- Practice explaining out loud in 30 min

### Day 2: Tools Review

- Skim cheatsheets (Sections 2-10 above)
- Make sure you can:
  - Write a Dockerfile from memory
  - Write a basic GitHub Actions YAML from memory
  - Write a basic FastAPI endpoint from memory
  - Explain every line of a K8s Deployment YAML

### Day 1 (day before): Rest + Light Review

- 1 hour max: re-read your STAR stories
- 1 hour max: re-read the company's product/blog posts
- Prepare questions to ask THEM:
  - "What's your model deployment process like?"
  - "How do you handle model monitoring?"
  - "What's the team structure?"
  - "What's the biggest ML challenge you're facing?"
- Sleep 8 hours

### Day 0 (interview day)

- Eat a real meal beforehand
- Have water nearby
- For phone/video: test your mic/camera 30 min before
- For onsite: arrive 15 min early, not 30 (don't be awkward)
- Take notes during the interview
- Send a thank-you email within 24 hours

---

## Bonus: Questions to Ask the Interviewer

Always have 3-5 ready. Shows engagement.

### Technical questions
- "What's your MLOps maturity level — Level 0, 1, or 2?"
- "What does your model deployment process look like end-to-end?"
- "How do you handle model monitoring and drift detection?"
- "What's your tech stack? (orchestration, serving, feature store, monitoring)"
- "How often do models get retrained? Manual or automatic?"

### Team questions
- "How big is the ML team? How is it structured?"
- "How do ML engineers collaborate with data scientists and software engineers?"
- "What's the on-call rotation like?"
- "How do you handle incidents when a model misbehaves?"

### Career questions
- "What does success look like in this role at 3 months / 6 months / 12 months?"
- "What's the typical career path for someone in this role?"
- "What's the biggest learning opportunity here?"
- "How does the team invest in learning (conferences, courses)?"

### Business questions
- "What's the biggest ML initiative the company is investing in?"
- "How does ML drive revenue or cost savings today?"
- "Who are the customers of your ML systems?"

---

## Final Words

You have everything. Theory. Code. Projects. Interview prep. Cheatsheets.

**Now go.**

Apply to 50 jobs. Do 10 interviews. Get 3 offers. Negotiate. Accept the best one.

Then come back in 6 months and tell me you made it.

**Good luck.**

---

*End of File 6. End of curriculum. You did it.*
