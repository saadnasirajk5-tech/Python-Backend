# Docker & Kubernetes for ML — The Complete Guide

> "It works on my machine" is a developer excuse. "It works in our container" is engineering.

---

## Table of Contents

1. [Why Docker for ML?](#1-why-docker-for-ml)
2. [Docker Fundamentals](#2-docker-fundamentals)
3. [Writing Great Dockerfiles for ML](#3-writing-great-dockerfiles-for-ml)
4. [Multi-Stage Builds](#4-multi-stage-builds)
5. [Docker Compose for ML Services](#5-docker-compose-for-ml-services)
6. [GPU Containers with NVIDIA Runtime](#6-gpu-containers-with-nvidia-runtime)
7. [Image Optimization — Size & Speed](#7-image-optimization--size--speed)
8. [Docker Registry & Pushing Images](#8-docker-registry--pushing-images)
9. [Kubernetes Fundamentals](#9-kubernetes-fundamentals)
10. [Deploying an ML API on K8s](#10-deploying-an-ml-api-on-k8s)
11. [ConfigMaps & Secrets](#11-configmaps--secrets)
12. [Storage — Persistent Volumes](#12-storage--persistent-volumes)
13. [GPU Scheduling on K8s](#13-gpu-scheduling-on-k8s)
14. [Autoscaling](#14-autoscaling)
15. [Helm Charts for ML](#15-helm-charts-for-ml)
16. [Ingress & TLS](#16-ingress--tls)
17. [Service Mesh & Advanced Networking](#17-service-mesh--advanced-networking)
18. [Observability on K8s](#18-observability-on-k8s)
19. [Production Deployment Patterns](#19-production-deployment-patterns)
20. [Disaster Recovery & Backup](#20-disaster-recovery--backup)
21. [Summary & Next Steps](#21-summary--next-steps)

---

## 1. Why Docker for ML?

### The Five Problems Docker Solves for ML

1. **Dependency Hell.** Project A needs `numpy==1.21`, Project B needs `numpy==1.26`. Without Docker: virtualenvs everywhere, conflicts on shared servers. With Docker: each project in its own container.

2. **Training-Serving Skew.** You train with `scikit-learn==1.3`. Production has `scikit-learn==1.5`. Model behaves differently. Docker eliminates this — same image in train and serve.

3. **Reproducibility.** "This notebook worked last year" is a lie. Docker images are immutable. The same image always behaves the same way.

4. **Environment Parity.** Dev = Staging = Prod. No more "but it works in dev!" — all three run the same image.

5. **GPU Management.** Different CUDA versions for different models? Docker + NVIDIA Container Runtime = isolated CUDA per container.

### Why NOT Just Use `pip install`?

| Concern | pip + venv | Docker |
|---------|-----------|--------|
| Python version | Manual management | Pinned in image |
| OS-level deps (libsm, CUDA) | Manual install | Built into image |
| Reproducibility | Loose (depends on system) | Strict (image is immutable) |
| Portability | Same OS only | Any OS with Docker |
| Isolation | Per-project | Per-container (stronger) |
| Production parity | Hard | Easy (same image) |

For ML specifically, Docker is **non-negotiable** in production.

---

## 2. Docker Fundamentals

### The Mental Model

```
Docker Engine
├── Images (templates — read-only)
│   ├── ubuntu:22.04
│   ├── python:3.11-slim
│   └── your-ml-app:v1
└── Containers (running instances of images)
    ├── container_1 (running python:3.11-slim)
    ├── container_2 (running your-ml-app:v1)
    └── ...
```

- **Image** = blueprint (immutable)
- **Container** = running instance of an image (mutable, ephemeral)
- **Dockerfile** = recipe to build an image
- **Registry** = where images are stored (Docker Hub, ECR, GCR, private)
- **Volume** = persistent storage that survives container restarts
- **Network** = how containers talk to each other

### Essential Commands

```bash
# Images
docker build -t my-app:v1 .           # build image from Dockerfile in current dir
docker images                          # list images
docker rmi my-app:v1                   # remove image
docker pull python:3.11-slim           # pull from registry
docker push myuser/my-app:v1           # push to registry

# Containers
docker run -p 8000:8000 my-app:v1     # run with port mapping
docker run -it python:3.11 bash       # interactive shell
docker run --rm my-app:v1 pytest      # run command, auto-remove
docker ps                              # list running containers
docker ps -a                           # list all (including stopped)
docker logs <container>                # view logs
docker exec -it <container> bash       # exec into running container
docker stop <container>                # graceful stop
docker kill <container>                # force kill
docker rm <container>                  # remove stopped container

# Volumes
docker volume create mydata            # create named volume
docker run -v mydata:/data my-app      # mount volume
docker run -v $(pwd):/app my-app       # bind mount current dir

# Networks
docker network create mynet            # create network
docker run --network mynet my-app      # attach to network

# System
docker system df                       # disk usage
docker system prune -a                 # cleanup unused everything
docker buildx build ...                # multi-arch builds
```

---

## 3. Writing Great Dockerfiles for ML

### Basic Python ML Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies (some ML libs need these)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Run
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build & Run

```bash
docker build -t churn-api:v1 .
docker run -p 8000:8000 churn-api:v1
```

### Production-Grade ML Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim AS base

# Set environment vars for Python best practice
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps (cache this layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code (changes most frequently, so last)
COPY --chown=appuser:appuser . .

# Switch to non-root
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

EXPOSE 8000

# Use gunicorn for production
CMD ["gunicorn", "main:app", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--graceful-timeout", "30"]
```

### Why Each Line Matters

1. **`python:3.11-slim`** — not `python:3.11` (full) which is 1GB+. Slim is ~150MB.
2. **`PYTHONDONTWRITEBYTECODE=1`** — no `.pyc` files, smaller image.
3. **`PYTHONUNBUFFERED=1`** — logs flush immediately (you see them in `docker logs`).
4. **Non-root user** — security best practice. If attacker breaks in, they're not root.
5. **`--no-cache-dir`** — pip cache wastes space in image.
6. **Copy `requirements.txt` first** — leverages Docker layer caching. If only app code changes, deps don't reinstall.
7. **`HEALTHCHECK`** — Docker (and K8s) can detect unhealthy containers.
8. **`gunicorn` over `uvicorn`** in prod — multi-process management.

---

## 4. Multi-Stage Builds

Multi-stage builds keep images **small** by compiling in one stage and copying only the result to the final image.

### Example: PyTorch Model with Heavy Build Deps

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

# Copy only installed packages from builder
COPY --from=builder /root/.local /root/.local

WORKDIR /app
COPY . .

ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### Multi-Stage for Compiled Models

```dockerfile
# Stage 1: Train model
FROM python:3.11-slim AS trainer
WORKDIR /train
COPY requirements-train.txt .
RUN pip install -r requirements-train.txt
COPY train.py data/ .
RUN python train.py  # produces model.pkl

# Stage 2: Serve (much smaller — no training deps)
FROM python:3.11-slim AS server
WORKDIR /app
COPY requirements-serve.txt .
RUN pip install --no-cache-dir -r requirements-serve.txt
COPY main.py .
COPY --from=trainer /train/model.pkl ./models/
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

The final image is much smaller because it doesn't include pandas, scikit-learn's training utils, etc. — only what's needed for serving.

---

## 5. Docker Compose for ML Services

Real ML apps need multiple services: API + DB + Redis + MLflow + Prometheus. Docker Compose orchestrates them locally.

### docker-compose.yml

```yaml
version: "3.9"

services:
  # Your FastAPI ML app
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/ml
      - REDIS_URL=redis://redis:6379
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
      mlflow:
        condition: service_started
    volumes:
      - ./models:/app/models:ro  # mount models read-only
    restart: unless-stopped

  # PostgreSQL for predictions log
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: ml
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  # Redis for rate limiting & caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data

  # MLflow tracking server
  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.13.2
    ports:
      - "5000:5000"
    environment:
      - BACKEND_STORE_URI=postgresql://postgres:postgres@db:5432/mlflow
      - ARTIFACT_ROOT=/mlruns
    volumes:
      - mlruns:/mlruns
    command: mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri postgresql://postgres:postgres@db:5432/mlflow --default-artifact-root /mlruns

  # Prometheus for metrics
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - promdata:/prometheus

  # Grafana for dashboards
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafanadata:/var/lib/grafana

volumes:
  pgdata:
  redisdata:
  mlruns:
  promdata:
  grafanadata:
```

### prometheus.yml

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "api"
    static_configs:
      - targets: ["api:8000"]
    metrics_path: /metrics
```

### Run It All

```bash
docker compose up -d           # start all services
docker compose ps              # see status
docker compose logs -f api     # tail API logs
docker compose down            # stop everything
docker compose down -v         # stop + delete volumes (DESTRUCTIVE)
```

This single command spins up a **complete ML platform** locally. That's the power of Compose.

---

## 6. GPU Containers with NVIDIA Runtime

For deep learning, you need GPU access inside containers.

### Prerequisites

On the host:
1. NVIDIA driver installed
2. NVIDIA Container Toolkit installed:
```bash
# Ubuntu
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
    && curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add - \
    && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### GPU Dockerfile

```dockerfile
# Use NVIDIA CUDA base image
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "-m", "vllm.entrypoints.openai.api_server", "--model", "meta-llama/Llama-2-7b", "--port", "8000"]
```

### Run with GPU

```bash
docker run --gpus all -p 8000:8000 my-llm-server:v1

# Or specify how many GPUs
docker run --gpus 2 -p 8000:8000 my-llm-server:v1

# Or specific GPUs
docker run --gpus '"device=0,1"' -p 8000:8000 my-llm-server:v1
```

### Verify GPU Access Inside Container

```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-runtime-ubuntu22.04 nvidia-smi
```

### Docker Compose with GPU

```yaml
services:
  llm:
    build: .
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    ports:
      - "8000:8000"
```

---

## 7. Image Optimization — Size & Speed

ML images can easily balloon to 5-10GB. Here's how to keep them lean.

### Size Optimization Checklist

1. **Use slim/alpine base images**
   - `python:3.11` = 1GB
   - `python:3.11-slim` = 150MB
   - `python:3.11-alpine` = 50MB (but compile issues with some libs)

2. **Multi-stage builds** (see Section 4)

3. **`.dockerignore`** (often forgotten)
```
# .dockerignore
.git
.github
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
.pytest_cache
htmlcov/
*.egg-info/
instance/
.webassets-cache
.terraform
*.tfstate
notebooks/
data/raw/
data/processed/
models/*.pkl
models/*.pt
models/*.h5
.env
.env.local
.DS_Store
.idea/
.vscode/
```

4. **Combine RUN commands** (fewer layers)
```dockerfile
# BAD — 3 layers
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*

# GOOD — 1 layer
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
```

5. **Don't install dev deps in prod image**
```dockerfile
# Install only prod deps in final image
RUN pip install --no-cache-dir -r requirements.txt
# NOT requirements-dev.txt
```

6. **Use `.dockerignore` for big data files** — never bake datasets into images.

7. **Squash images** (experimental)
```bash
docker build --squash -t my-app:v1 .
```

### Build Speed Optimization

1. **Layer caching** — order Dockerfile from least-frequently-changed to most:
```dockerfile
# System deps (rarely change)
RUN apt-get install ...

# Python deps (change weekly)
COPY requirements.txt .
RUN pip install -r requirements.txt

# App code (changes every commit)
COPY . .
```

2. **Use BuildKit for parallel stages**
```bash
DOCKER_BUILDKIT=1 docker build -t my-app:v1 .
```

3. **Cache pip with BuildKit**
```dockerfile
# syntax=docker/dockerfile:1.4
FROM python:3.11-slim
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt
```

4. **Remote cache** (CI/CD)
```bash
docker build \
    --cache-from type=registry,ref=myuser/my-app:cache \
    --cache-to type=registry,ref=myuser/my-app:cache,mode=max \
    -t myuser/my-app:v1 .
```

---

## 8. Docker Registry & Pushing Images

### Docker Hub (Public)

```bash
# Login
docker login

# Tag with your username
docker tag my-app:v1 myusername/my-app:v1

# Push
docker push myusername/my-app:v1
```

### AWS ECR (Private, Production)

```bash
# Login
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

# Create repo
aws ecr create-repository --repository-name churn-api

# Tag
docker tag churn-api:v1 <account>.dkr.ecr.us-east-1.amazonaws.com/churn-api:v1

# Push
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/churn-api:v1
```

### GCP Artifact Registry

```bash
gcloud auth configure-docker us-docker.pkg.dev

docker tag churn-api:v1 us-docker.pkg.dev/<project>/ml-images/churn-api:v1
docker push us-docker.pkg.dev/<project>/ml-images/churn-api:v1
```

### Image Tagging Strategy

Don't just use `:latest`. Use a layered tagging strategy:

| Tag Type | Example | When to Use |
|----------|---------|-------------|
| `:latest` | `myuser/api:latest` | Convenience only, never for prod |
| `:sha-<git>` | `myuser/api:sha-a1b2c3d` | Traceability — every commit |
| `:v<semver>` | `myuser/api:v2.3.1` | Releases |
| `:v<major>` | `myuser/api:v2` | "Latest v2" pointer |
| `:branch-<name>` | `myuser/api:branch-feature-x` | Branch builds |
| `:<date>` | `myuser/api:2024-03-15` | Time-based |

**Recommended:** Always tag with git SHA + semver. E.g., `myuser/api:sha-a1b2c3d` AND `myuser/api:v2.3.1`. K8s deployments reference the SHA tag (immutable). Semver is for human reference.

---

## 9. Kubernetes Fundamentals

### What is Kubernetes?

Kubernetes (K8s) is a container orchestrator. It:
- Schedules containers across multiple machines
- Restart failed containers
- Scales containers up/down based on load
- Routes traffic between containers
- Manages secrets, configs, storage
- Does rolling updates + rollbacks

### Core Concepts

```
Cluster
├── Control Plane (managed)
│   ├── API Server — entry point
│   ├── Scheduler — assigns pods to nodes
│   ├── Controller Manager — reconciles state
│   └── etcd — key-value store of cluster state
└── Worker Nodes
    ├── kubelet — talks to control plane
    ├── kube-proxy — networking
    └── Container Runtime (containerd/Docker)
        └── Pods (smallest unit)
            └── Containers
```

### The K8s Object Hierarchy

| Object | What It Is |
|--------|-----------|
| **Pod** | 1+ containers, smallest deployable unit |
| **Deployment** | Manages replicas of pods, handles rollout |
| **Service** | Stable network endpoint for pods |
| **Ingress** | HTTP/HTTPS routing from outside |
| **ConfigMap** | Non-secret config |
| **Secret** | Secret config (encoded) |
| **PersistentVolume** | Storage |
| **PersistentVolumeClaim** | Request for storage |
| **StatefulSet** | Like Deployment but for stateful apps (DBs) |
| **DaemonSet** | Pod on every node |
| **Job / CronJob** | Run-to-completion / scheduled |
| **HorizontalPodAutoscaler** | Auto-scale based on metrics |
| **Namespace** | Logical cluster partition |

### Essential kubectl Commands

```bash
# Info
kubectl get pods                          # list pods in current namespace
kubectl get pods -A                       # all namespaces
kubectl get pods -o wide                  # more details
kubectl get deployments
kubectl get services
kubectl get ingress
kubectl get configmaps
kubectl get secrets
kubectl get nodes
kubectl get events --sort-by=.lastTimestamp

# Inspect
kubectl describe pod <pod-name>
kubectl logs <pod-name>
kubectl logs <pod-name> -f                # follow
kubectl logs <pod-name> -c <container>    # specific container
kubectl exec -it <pod-name> -- bash

# Apply changes
kubectl apply -f deployment.yaml
kubectl apply -f ./k8s/                   # all YAMLs in dir
kubectl delete -f deployment.yaml
kubectl delete pod <pod-name>             # kill (Deployment will recreate)

# Scaling
kubectl scale deployment api --replicas=5
kubectl autoscale deployment api --min=3 --max=10 --cpu-percent=70

# Rolling updates
kubectl set image deployment/api api=myuser/api:v2
kubectl rollout status deployment/api
kubectl rollout undo deployment/api
kubectl rollout history deployment/api

# Namespaces
kubectl create namespace ml-prod
kubectl config set-context --current --namespace=ml-prod

# Port forwarding (debug locally)
kubectl port-forward svc/api 8080:80

# Contexts (multiple clusters)
kubectl config get-contexts
kubectl config use-context my-prod-cluster
```

---

## 10. Deploying an ML API on K8s

Let's deploy the FastAPI app from File 3 to K8s. We need 4 objects: Deployment, Service, ConfigMap, Secret.

### 10.1 Namespace

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ml-prod
```

### 10.2 Secret (sensitive data)

```bash
# Create from literals
kubectl create secret generic api-secrets \
    --namespace=ml-prod \
    --from-literal=mlflow-uri=http://mlflow:5000 \
    --from-literal=api-key-secret=$(openssl rand -hex 16) \
    --from-literal=database-url=postgresql://user:pass@db:5432/ml

# Or from file
kubectl create secret generic api-secrets --from-env-file=.env.prod
```

### 10.3 ConfigMap (non-sensitive config)

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
  namespace: ml-prod
data:
  LOG_LEVEL: "INFO"
  MODEL_NAME: "churn-prediction"
  MODEL_VERSION: "Production"
  RATE_LIMIT_PER_MINUTE: "60"
  ENVIRONMENT: "production"
```

### 10.4 Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: churn-api
  namespace: ml-prod
  labels:
    app: churn-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: churn-api
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0       # never go below desired replicas
      maxSurge: 1             # at most 1 extra pod during rollout
  template:
    metadata:
      labels:
        app: churn-api
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: api
        image: myuser/churn-api:sha-a1b2c3d  # use SHA tag, not latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
        envFrom:
        - configMapRef:
            name: api-config
        - secretRef:
            name: api-secrets
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 5
          failureThreshold: 3
        startupProbe:
          httpGet:
            path: /health/live
            port: 8000
          failureThreshold: 30
          periodSeconds: 10
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop: ["ALL"]
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}
      terminationGracePeriodSeconds: 60  # let in-flight requests finish
```

### 10.5 Service

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: churn-api
  namespace: ml-prod
spec:
  type: ClusterIP  # internal only; use Ingress for external
  selector:
    app: churn-api
  ports:
  - port: 80
    targetPort: 8000
    name: http
```

### 10.6 Apply Everything

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml     # or use kubectl create secret
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Verify
kubectl get pods -n ml-prod
kubectl get svc -n ml-prod

# Test
kubectl port-forward svc/churn-api 8080:80 -n ml-prod
curl http://localhost:8080/health/ready
```

---

## 11. ConfigMaps & Secrets

### ConfigMap Patterns

```yaml
# 1. As environment variables
spec:
  containers:
  - name: app
    envFrom:
    - configMapRef:
        name: api-config

# 2. Specific env vars
spec:
  containers:
  - name: app
    env:
    - name: LOG_LEVEL
      valueFrom:
        configMapKeyRef:
          name: api-config
          key: LOG_LEVEL

# 3. As files (volume mount)
spec:
  containers:
  - name: app
    volumeMounts:
    - name: config
      mountPath: /etc/config
  volumes:
  - name: config
    configMap:
      name: api-config
```

### Secrets

```bash
# Create
kubectl create secret generic db-secret \
    --from-literal=password=supersecret \
    --from-literal=username=admin

# View (base64-encoded — not encrypted!)
kubectl get secret db-secret -o yaml
# data:
#   password: c3VwZXJzZWNyZXQ=
#   username: YWRtaW4=

# Decode
echo "c3VwZXJzZWNyZXQ=" | base64 -d
# supersecret
```

### Important: Secrets Are NOT Encrypted by Default

By default, K8s secrets are **base64-encoded** in etcd. Anyone with cluster read access can decode them. For real security:

1. **Enable etcd encryption at rest** (cluster-level setting)
2. **Use a KMS provider** (AWS KMS, GCP KMS, HashiCorp Vault)
3. **Use External Secrets Operator** to sync from Vault/AWS Secrets Manager

```yaml
# ExternalSecret example
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: api-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: SecretStore
  target:
    name: api-secrets  # K8s Secret to create
    creationPolicy: Owner
  data:
  - secretKey: database-url
    remoteRef:
      key: prod/api/database-url  # AWS Secrets Manager path
```

---

## 12. Storage — Persistent Volumes

For stateful workloads (databases, model caches, MLflow artifact store).

### PersistentVolume + PersistentVolumeClaim

```yaml
# k8s/pv.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: mlflow-pv
spec:
  capacity:
    storage: 50Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: gp2  # AWS EBS
  hostPath:
    path: /mnt/data/mlflow  # in real life, use cloud storage

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mlflow-pvc
  namespace: ml-prod
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp2
  resources:
    requests:
      storage: 50Gi
```

### Using PVC in a Pod

```yaml
spec:
  containers:
  - name: mlflow
    image: ghcr.io/mlflow/mlflow:v2.13.2
    volumeMounts:
    - name: mlflow-storage
      mountPath: /mlruns
  volumes:
  - name: mlflow-storage
    persistentVolumeClaim:
      claimName: mlflow-pvc
```

### Storage Classes (Cloud)

| Cloud | StorageClass | Use Case |
|-------|-------------|----------|
| AWS | `gp2`, `gp3`, `io1` | General purpose, SSD |
| GCP | `standard`, `pd-ssd` | Standard, SSD |
| Azure | `default`, `premium-lrs` | Standard, Premium SSD |
| Local | `local-storage` | High I/O, ephemeral |

### RWX (ReadWriteMany) — Multiple pods same volume

For shared model storage across replicas:
- AWS EFS
- GCP Filestore
- Azure Files
- NFS

---

## 13. GPU Scheduling on K8s

### Prerequisites

1. GPU nodes in cluster (e.g., AWS p4d, GCP a2, Azure NC-series)
2. NVIDIA device plugin installed:
```bash
kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.5/nvidia-device-plugin.yml
```

### Requesting GPUs

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: llm
  template:
    metadata:
      labels:
        app: llm
    spec:
      containers:
      - name: llm
        image: myuser/llm-server:v1
        resources:
          limits:
            nvidia.com/gpu: 1  # request 1 GPU
            memory: 32Gi
            cpu: 8
      nodeSelector:
        accelerator: nvidia-a100  # only schedule on A100 nodes
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
```

### Fractional GPU Sharing (Advanced)

For inference workloads that don't need a full GPU:

1. **NVIDIA Multi-Instance GPU (MIG)** — A100/H100 only, hardware partitioning
2. **Time-slicing** — `nvidia.com/gpu.shared` config
3. **Run:AI** / **Aliyun GPU sharing** — third-party solutions

### GPU Monitoring

```bash
# Install DCGM exporter
helm install nvidia-dcgm nvdp/nvidia-dcgm-exporter

# Query GPU metrics in Prometheus
nvidia_gpu_memory_used_bytes
nvidia_gpu_utilization
nvidia_gpu_power_watts
```

---

## 14. Autoscaling

### Horizontal Pod Autoscaler (HPA)

Scales number of pods based on CPU/memory/custom metrics.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: churn-api
  namespace: ml-prod
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
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods  # custom metric
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
      - type: Percent
        value: 100  # can double in 30s
        periodSeconds: 30
    scaleDown:
      stabilizationWindowSeconds: 300  # don't scale down for 5 min
      policies:
      - type: Percent
        value: 10  # only shrink by 10% per minute
        periodSeconds: 60
```

### Vertical Pod Autoscaler (VPA)

Adjusts resource requests/limits based on usage. Useful for right-sizing.

```bash
# Install
git clone https://github.com/kubernetes/autoscaler.git
cd autoscaler/vertical-pod-autoscaler
./hack/vpa-up.sh

# Apply
kubectl apply -f - <<EOF
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: churn-api
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: churn-api
  updatePolicy:
    updateMode: Auto  # or Off (recommend-only), Initial
EOF
```

### Cluster Autoscaler

Adds/removes nodes when pods can't be scheduled or nodes are underutilized.

```bash
# AWS EKS — install via Helm
helm install cluster-autoscaler autoscaler/cluster-autoscaler \
    --set autoDiscovery.clusterName=my-cluster \
    --set awsRegion=us-east-1 \
    --set rbac.serviceAccount.create=true \
    --set rbac.serviceAccount.name=cluster-autoscaler
```

### KEDA — Event-Driven Autoscaling

For ML, KEDA is amazing — scale based on Kafka queue length, SQS messages, Prometheus queries, etc.

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: batch-predictor
spec:
  scaleTargetRef:
    name: batch-predictor
  minReplicaCount: 0   # scale to zero when no work!
  maxReplicaCount: 50
  pollingInterval: 30
  triggers:
  - type: aws-sqs
    metadata:
      queueURL: https://sqs.us-east-1.amazonaws.com/123/predictions
      queueLength: "10"  # 1 pod per 10 messages
      awsRegion: us-east-1
```

---

## 15. Helm Charts for ML

Helm is the package manager for K8s. It lets you template + parameterize your YAMLs.

### Install Helm

```bash
curl https://get.helm.sh/helm-v3.15.0-linux-amd64.tar.gz | tar xz
sudo mv linux-amd64/helm /usr/local/bin/
```

### Chart Structure

```
churn-api-chart/
├── Chart.yaml          # chart metadata
├── values.yaml         # default config values
├── values-prod.yaml    # prod overrides
├── values-staging.yaml # staging overrides
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    ├── configmap.yaml
    ├── secret.yaml
    ├── hpa.yaml
    └── _helpers.tpl    # reusable template snippets
```

### Chart.yaml

```yaml
apiVersion: v2
name: churn-api
description: Churn prediction API
type: application
version: 1.0.0
appVersion: "2.3.1"
maintainers:
  - name: ML Team
```

### values.yaml

```yaml
replicaCount: 3

image:
  repository: myuser/churn-api
  tag: ""  # set in CI, defaults to Chart appVersion
  pullPolicy: IfNotPresent

resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 1000m
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilization: 70

ingress:
  enabled: true
  className: nginx
  host: api.example.com
  tls: true

env:
  LOG_LEVEL: INFO
  MODEL_NAME: churn-prediction

secrets:
  databaseUrl: ""
  mlflowUri: ""

probe:
  livenessPath: /health/live
  readinessPath: /health/ready
```

### templates/deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-churn-api
  labels:
    app: {{ .Release.Name }}-churn-api
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}-churn-api
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}-churn-api
    spec:
      containers:
      - name: api
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: {{ .Release.Name }}-config
        - secretRef:
            name: {{ .Release.Name }}-secret
        resources:
          {{- toYaml .Values.resources | nindent 10 }}
        livenessProbe:
          httpGet:
            path: {{ .Values.probe.livenessPath }}
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: {{ .Values.probe.readinessPath }}
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 5
```

### Install the Chart

```bash
# Add your chart repo (or install locally)
helm install churn-api ./churn-api-chart -n ml-prod

# Override values
helm install churn-api ./churn-api-chart -n ml-prod \
    -f values-prod.yaml \
    --set image.tag=sha-a1b2c3d \
    --set secrets.databaseUrl=$DB_URL

# Upgrade
helm upgrade churn-api ./churn-api-chart -n ml-prod -f values-prod.yaml

# Rollback
helm rollback churn-api 1 -n ml-prod

# Uninstall
helm uninstall churn-api -n ml-prod
```

### Popular Helm Charts for ML

```bash
# MLflow
helm install mlflow community/mlflow

# KServe (model serving)
helm install kserve kserve/kserve

# Seldon Core
helm install seldon-core seldon-core-operator/seldon-core-operator

# NVIDIA GPU operator
helm install nvdp nvdp/gpu-operator

# Prometheus stack
helm install kube-prom prometheus-community/kube-prometheus-stack

# EFK stack (Elasticsearch + Fluent Bit + Kibana)
helm install efk elastic/eck-stack
```

---

## 16. Ingress & TLS

### NGINX Ingress Controller

```bash
helm install ingress-nginx ingress-nginx/ingress-nginx \
    --namespace ingress-nginx \
    --create-namespace \
    --set controller.service.type=LoadBalancer
```

### Ingress Resource

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: churn-api
  namespace: ml-prod
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    # For SSE / streaming
    nginx.ingress.kubernetes.io/proxy-buffering: "off"
spec:
  ingressClassName: nginx
  tls:
  - hosts: [api.example.com]
    secretName: api-tls
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: churn-api
            port:
              number: 80
```

### TLS with cert-manager (Let's Encrypt)

```bash
# Install cert-manager
helm install cert-manager jetstack/cert-manager \
    --namespace cert-manager \
    --create-namespace \
    --set installCRDs=true
```

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: you@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

Now your Ingress just needs:
```yaml
annotations:
  cert-manager.io/cluster-issuer: letsencrypt-prod
```

cert-manager will auto-issue + renew certs.

---

## 17. Service Mesh & Advanced Networking

### When You Need a Service Mesh

- mTLS between services (zero trust)
- Fine-grained traffic control (canary, mirroring)
- Observability without code changes
- Multi-cluster federation

**Popular options:** Istio, Linkerd, Consul.

### Istio Canary Deployment

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: churn-api
spec:
  hosts: [churn-api]
  http:
  - route:
    - destination:
        host: churn-api
        subset: v1
      weight: 90
    - destination:
        host: churn-api
        subset: v2
      weight: 10
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: churn-api
spec:
  host: churn-api
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
```

Gradually shift `weight` from 10 → 50 → 100 as you gain confidence in v2.

---

## 18. Observability on K8s

### The Three Pillars

1. **Metrics** — Prometheus + Grafana
2. **Logs** — Loki + Grafana (or ELK)
3. **Traces** — Jaeger / Tempo / OpenTelemetry

### Install the Stack

```bash
# Prometheus + Grafana + AlertManager
helm install monitoring prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --create-namespace

# Loki (logs)
helm install loki grafana/loki-stack \
    --namespace monitoring \
    --set promtail.enabled=true

# Jaeger (traces)
helm install jaeger jaegertracing/jaeger \
    --namespace monitoring
```

### Example: Prometheus Alert for ML

```yaml
# prometheus-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: ml-alerts
  namespace: ml-prod
spec:
  groups:
  - name: ml.rules
    rules:
    - alert: HighErrorRate
      expr: |
        rate(http_requests_total{job="churn-api",status=~"5.."}[5m])
        / rate(http_requests_total{job="churn-api"}[5m]) > 0.05
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Churn API error rate > 5%"
        description: "{{ $value | humanizePercentage }} of requests are 5xx"

    - alert: HighLatency
      expr: |
        histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{job="churn-api"}[5m])) > 2
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Churn API p99 latency > 2s"

    - alert: PredictionDrift
      expr: |
        avg_over_time(prediction_value_sum[1h]) / avg_over_time(prediction_value_count[1h]) > 0.7
      for: 30m
      labels:
        severity: warning
      annotations:
        summary: "Average prediction > 0.7 — possible drift"
```

---

## 19. Production Deployment Patterns

### Blue/Green

```yaml
# Two deployments: blue (current) and green (new)
# Service points to blue initially
kubectl apply -f deployment-green.yaml
kubectl wait --for=condition=ready pod -l app=churn-api,version=green

# Test green
kubectl port-forward svc/churn-api-green 8080:80
# ... smoke tests ...

# Switch service selector
kubectl patch svc churn-api -p '{"spec":{"selector":{"version":"green"}}}'

# After validation, delete blue
kubectl delete deployment churn-api-blue
```

### Canary with Argo Rollouts

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: churn-api
spec:
  replicas: 10
  strategy:
    canary:
      steps:
      - setWeight: 10
      - pause: { duration: 30m }
      - analysis:
          templates:
          - templateName: success-rate
      - setWeight: 30
      - pause: { duration: 1h }
      - setWeight: 50
      - pause: { duration: 1h }
      - setWeight: 100
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
        image: myuser/churn-api:v2
```

### GitOps with ArgoCD

```bash
# Install ArgoCD
helm install argocd argo/argo-cd --namespace argocd --create-namespace

# Port-forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Apply an Application
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: churn-api-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/myuser/ml-infra
    targetRevision: HEAD
    path: charts/churn-api
  destination:
    server: https://kubernetes.default.svc
    namespace: ml-prod
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF
```

Now any change to your git repo automatically syncs to the cluster. **This is the modern way.**

---

## 20. Disaster Recovery & Backup

### What to Back Up

| Component | Tool | Frequency |
|-----------|------|-----------|
| etcd (cluster state) | `etcdctl snapshot save` | Daily |
| PVs (data) | Velero, cloud snapshots | Daily |
| Container images | Registry replication | On push |
| K8s manifests | Git (ArgoCD) | Continuous |
| Secrets | Vault / SOPS | On change |

### Velero — Backup & Restore

```bash
# Install
velero install \
    --provider aws \
    --bucket my-backup-bucket \
    --backup-location-config region=us-east-1 \
    --snapshot-location-config region=us-east-1 \
    --secret-file credentials-velero

# Backup
velero backup create churn-api-backup --include-namespaces ml-prod

# Schedule
velero schedule create daily-ml-prod \
    --schedule="0 1 * * *" \
    --include-namespaces ml-prod

# Restore
velero restore create --from-backup churn-api-backup
```

### Multi-Cluster / Multi-Region

For production-grade ML:
- Run primary cluster in us-east-1
- Run standby cluster in us-west-2
- Replicate images to both registries
- Use Route53 / Cloud LB for DNS failover
- Practice failover drills quarterly

---

## 21. Summary & Next Steps

### What You Learned

1. Docker solves dependency hell, training-serving skew, reproducibility for ML.
2. Multi-stage builds keep images small.
3. Docker Compose orchestrates multi-service ML stacks locally.
4. NVIDIA Container Runtime gives containers GPU access.
5. Kubernetes deploys + scales + heals your containers across multiple machines.
6. Core K8s objects: Pod, Deployment, Service, Ingress, ConfigMap, Secret, PVC.
7. HPA scales on CPU/metrics, KEDA scales on events (e.g., queue length).
8. Helm packages your K8s YAMLs into reusable charts.
9. cert-manager auto-issues TLS certs.
10. ArgoCD + Git = GitOps (the modern deployment pattern).
11. Observability stack: Prometheus + Loki + Jaeger.
12. Velero for backups, multi-cluster for DR.

### What's Next

- **05_10_Projects_Beginner_to_Pro.md** — apply everything in 10 graded projects.
- **06_Interview_Questions_and_Cheatsheets.md** — prep for job interviews.

### How to Practice

1. Install Docker Desktop (or minikube on Linux).
2. Build the Dockerfile from Section 3, run it.
3. Add docker-compose.yml from Section 5, run the whole stack.
4. Install `kind` or `minikube`, deploy the manifests from Section 10.
5. Install Helm, package your app as a chart.
6. Install ArgoCD, set up GitOps for your repo.
7. Add Prometheus + Grafana, dashboards for your API.
8. Set up HPA, load-test with Locust, watch it scale.

When you can do all 8, you can confidently apply for any MLOps / Platform / ML Infrastructure role.

---

**End of File 4. Continue to 05_10_Projects_Beginner_to_Pro.md.**
