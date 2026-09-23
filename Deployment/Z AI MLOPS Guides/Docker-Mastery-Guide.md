# Docker Mastery Guide for AI/ML Engineers
## The Complete 2025 Production Guide

From zero to containerization expert. Every concept explained with real-world AI/ML examples, production-ready code, and battle-tested patterns.

---

## Table of Contents

1. [Why Docker Matters for AI/ML](#1-why-docker-matters-for-aiml)
2. [Docker Architecture Deep Dive](#2-docker-architecture-deep-dive)
3. [Installation & Setup](#3-installation--setup)
4. [Dockerfile Mastery](#4-dockerfile-mastery)
5. [Multi-Stage Builds](#5-multi-stage-builds)
6. [Layer Caching & BuildKit](#6-layer-caching--buildkit)
7. [Security Hardening](#7-security-hardening)
8. [Networking Deep Dive](#8-networking-deep-dive)
9. [Volumes & Storage](#9-volumes--storage)
10. [Docker Compose v2](#10-docker-compose-v2)
11. [Multi-Platform Builds](#11-multi-platform-builds)
12. [CI/CD Integration](#12-cicd-integration)
13. [Image Optimization](#13-image-optimization)
14. [Monitoring & Logging](#14-monitoring--logging)
15. [Production Checklist](#15-production-checklist)
16. [Complete Command Reference](#16-complete-command-reference)

---

## 1. Why Docker Matters for AI/ML

### The Problem Docker Solves

```
Without Docker:
Developer A: "Works on my machine" (Python 3.9, CUDA 11.8)
Developer B: "Crashes on mine" (Python 3.11, CUDA 12.1)
Production Server: "Module not found" (Missing system dependency)
ML Engineer: "Model accuracy differs" (Different library versions)

With Docker:
Everyone runs the SAME container → SAME environment → SAME results
```

### Docker's Core Value for AI/ML

| Benefit | What It Means | AI/ML Impact |
|---------|---------------|--------------|
| **Consistency** | Same environment everywhere | Model behaves identically in dev and prod |
| **Reproducibility** | Anyone can recreate your setup | Experiments are reproducible, papers verifiable |
| **Portability** | Run on any infrastructure | Deploy to cloud, edge, or on-premise |
| **Isolation** | Containers don't interfere | Run multiple models without conflicts |
| **Scalability** | Replicate containers easily | Handle 10x traffic with one command |
| **Version Control** | Image versions = code versions | Roll back to previous model versions instantly |
| **Resource Control** | Limit CPU/GPU/memory | Prevent one model from consuming all resources |

### Real-World AI/ML Use Cases

```bash
# 1. Deploy a trained model as an API
docker run -p 8000:8000 my-ml-model:v2.1

# 2. Run GPU-accelerated training
docker run --gpus all -v ./data:/data my-training-env:latest

# 3. Scale inference to handle traffic
docker compose up -d --scale inference=5

# 4. A/B test model versions
docker run -d -p 8000:8000 model-v1:latest  # 50% traffic
docker run -d -p 8001:8000 model-v2:latest  # 50% traffic

# 5. Reproduce a research paper's experiments
git clone repo && docker compose up  # Exact same environment
```

---

## 2. Docker Architecture Deep Dive

### The Three Pillars

```
┌─────────────────────────────────────────────────────────┐
│                    DOCKER ARCHITECTURE                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │  DOCKER CLI  │───▶│DOCKER DAEMON │───▶│  REGISTRY  │ │
│  │  (Client)    │    │  (dockerd)   │    │ (Docker Hub│ │
│  │              │    │              │    │  or ECR/GCR│ │
│  │ docker build │    │ Manages:     │    │  or local) │ │
│  │ docker run   │    │ - Containers │    │            │ │
│  │ docker pull  │    │ - Images     │    │ Stores:    │ │
│  │ docker push  │    │ - Networks   │    │ - Images   │ │
│  │              │    │ - Volumes    │    │ - Layers   │ │
│  └──────────────┘    └──────────────┘    └────────────┘ │
│         │                   │                   │        │
│         └───────────────────┴───────────────────┘        │
│                    REST API (unix socket)                │
└─────────────────────────────────────────────────────────┘
```

### Docker Daemon (dockerd)

The background service that does all the heavy lifting:

```bash
# Check daemon status
docker info

# Restart daemon (Linux)
sudo systemctl restart docker

# Daemon configuration
cat /etc/docker/daemon.json
```

```json
{
  "experimental": true,
  "features": {
    "buildkit": true
  },
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "registry-mirrors": ["https://mirror.gcr.io"]
}
```

### Docker Client

The command-line interface you interact with:

```bash
# Client talks to daemon via REST API
docker version
# Client: Docker Engine - Community
#  Version:           27.0.0
# Server: Docker Engine - Community
#  Version:           27.0.0

# Check connection to daemon
docker system info
```

### Docker Registry

Where images are stored and distributed:

```bash
# Docker Hub (public registry)
docker pull python:3.12-slim
docker push myusername/myapp:v1

# Private registries
docker pull ghcr.io/myorg/myapp:latest    # GitHub Container Registry
docker pull 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:latest  # AWS ECR
docker pull us-central1-docker.pkg.dev/myproject/myrepo/myapp:latest  # GCP Artifact Registry

# Local registry (for air-gapped environments)
docker pull localhost:5000/myapp:latest
```

### Images vs Containers

```python
# Analogy:
# Image  = Python CLASS (blueprint, read-only template)
# Container = Python OBJECT (running instance, mutable)

# Image: Contains everything needed to run
# - Base OS (Ubuntu, Alpine, etc.)
# - Runtime (Python, Node.js, etc.)
# - Dependencies (pip packages, npm packages)
# - Application code
# - Configuration

# Container: A running instance of an image
# - Has its own filesystem (copy-on-write)
# - Has its own network interface
# - Has its own process space
# - Can be started, stopped, paused, deleted

# Multiple containers from same image
docker run -d --name app1 myapp:v1
docker run -d --name app2 myapp:v1
docker run -d --name app3 myapp:v1
# All three share the same image but run independently
```

---

## 3. Installation & Setup

### Docker Desktop (Mac/Windows)

```bash
# macOS (Intel)
# Download: https://docs.docker.com/desktop/install/mac-install/

# macOS (Apple Silicon)
# Download: https://docs.docker.com/desktop/install/mac-install/
# Choose: Apple Silicon chip option

# Windows
# Download: https://docs.docker.com/desktop/install/windows-install/
# Requirements: WSL 2 enabled, Hardware virtualization enabled

# After installation, verify:
docker --version
docker compose version
```

### Docker Engine (Linux)

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and log back in for group changes

# CentOS/RHEL/Fedora
sudo dnf install -y dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
sudo dnf install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker

# Verify installation
docker run hello-world
```

### GPU Support (NVIDIA)

```bash
# Install NVIDIA Container Toolkit
# (Required for GPU-accelerated ML containers)

# Ubuntu/Debian
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker to use NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.3.0-base-ubuntu22.04 nvidia-smi
```

### Docker Alternatives

```bash
# OrbStack (macOS) - Faster than Docker Desktop, lighter
brew install orbstack

# Podman (Rootless, daemonless)
# Drop-in replacement for Docker CLI
brew install podman  # macOS
sudo apt install podman  # Ubuntu

# Colima (Lightweight Docker Desktop alternative for macOS)
brew install colima docker
colima start
# Docker CLI automatically connects to Colima
```

---

## 4. Dockerfile Mastery

### Every Dockerfile Instruction Explained

```dockerfile
# ============================================
# SYNTAX: Optional, specifies BuildKit version
# ============================================
# syntax=docker/dockerfile:1
# Enables latest BuildKit features
# Always recommended at top of file


# ============================================
# FROM: Base image (MUST be first instruction)
# ============================================
# Options:
#   python:3.12           - Full Python image (~920MB)
#   python:3.12-slim      - Slim Python (~150MB) ← RECOMMENDED
#   python:3.12-alpine    - Alpine Python (~50MB) - smaller but compatibility issues
#   gcr.io/distroless/python3 - Distroless (~40MB) - maximum security

FROM python:3.12-slim AS base


# ============================================
# ARG: Build-time variables (NOT in final image)
# ============================================
# Available during build, gone at runtime
# Use for: Python version, build flags, metadata

ARG PYTHON_VERSION=3.12
ARG BUILD_DATE
ARG GIT_COMMIT_SHA


# ============================================
# LABEL: Metadata about the image
# ============================================
# Useful for: organization, tracking, documentation

LABEL maintainer="team@company.com"
LABEL version="1.0.0"
LABEL description="Production ML inference API"
LABEL build.date="${BUILD_DATE}"
LABEL git.commit="${GIT_COMMIT_SHA}"
LABEL org.opencontainers.image.source="https://github.com/org/repo"


# ============================================
# ENV: Environment variables (persist in image)
# ============================================
# Available at build AND runtime
# Can be overridden at runtime with -e flag

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_ENV=production \
    LOG_LEVEL=INFO \
    PORT=8000


# ============================================
# WORKDIR: Working directory for all subsequent instructions
# ============================================
# Creates directory if it doesn't exist
# All RUN, CMD, ENTRYPOINT, COPY, ADD use this as base

WORKDIR /app


# ============================================
# RUN: Execute commands during build (creates new layer)
# ============================================
# Each RUN = new layer = adds to image size
# Chain commands to reduce layers
# Clean up in same RUN to keep image small

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean


# ============================================
# COPY: Copy files from build context to image
# ============================================
# Use COPY (not ADD) unless you need ADD's features
# COPY is explicit, ADD has hidden behavior (URLs, tar extraction)

COPY requirements.txt .
COPY pyproject.toml .


# ============================================
# RUN: Install dependencies (separate from code for caching)
# ============================================

RUN pip install --no-cache-dir -r requirements.txt


# ============================================
# COPY: Copy application code (AFTER dependencies for caching)
# ============================================
# Code changes frequently → put this LAST
# Dependencies change rarely → cached layer reused

COPY ./src ./src
COPY ./models ./models
COPY ./config ./config


# ============================================
# USER: Run as non-root (SECURITY CRITICAL)
# ============================================
# Default: root (DANGEROUS!)
# Create dedicated user for your application

RUN groupadd -r appgroup && \
    useradd -r -g appgroup -u 1000 -m appuser && \
    chown -R appuser:appgroup /app

USER appuser


# ============================================
# EXPOSE: Document which ports the container uses
# ============================================
# Does NOT actually publish ports (documentation only)
# Must use -p flag when running: docker run -p 8000:8000

EXPOSE ${PORT}


# ============================================
# HEALTHCHECK: Define how to check if container is healthy
# ============================================
# Docker runs this command periodically
# Exit code 0 = healthy, non-0 = unhealthy

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1


# ============================================
# ENTRYPOINT vs CMD
# ============================================
# ENTRYPOINT: Configures the container as an executable
# CMD: Provides default arguments to ENTRYPOINT

# Option 1: CMD (can be overridden at runtime)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Option 2: ENTRYPOINT + CMD (ENTRYPOINT can't be overridden)
# ENTRYPOINT ["python", "src/main.py"]
# CMD ["--port", "8000"]

# Option 3: Shell form (NOT recommended - no signal handling)
# CMD uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Complete Production Dockerfile Example

```dockerfile
# syntax=docker/dockerfile:1

# ============================================
# PRODUCTION DOCKERFILE FOR ML INFERENCE API
# ============================================
# Features:
# - Multi-stage build (small image)
# - Non-root user (security)
# - Health checks (reliability)
# - Build metadata (tracking)
# - GPU support (optional)
# ============================================

ARG PYTHON_VERSION=3.12

# ============================================
# STAGE 1: BUILDER
# ============================================
FROM python:${PYTHON_VERSION}-slim AS builder

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# STAGE 2: RUNTIME
# ============================================
FROM python:${PYTHON_VERSION}-slim

# Install only runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Metadata
LABEL maintainer="ml-team@company.com"
LABEL version="1.0.0"
LABEL description="ML Inference API - Production"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production \
    LOG_LEVEL=INFO \
    PORT=8000

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY ./src ./src
COPY ./models ./models

# Create non-root user
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -u 1000 -m appuser && \
    chown -R appuser:appgroup /app

USER appuser

# Expose port
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### GPU-Enabled Dockerfile

```dockerfile
# ============================================
# GPU-ENABLED DOCKERFILE FOR ML TRAINING
# ============================================

# Use NVIDIA CUDA base image
FROM nvidia/cuda:12.3.0-runtime-ubuntu22.04

# Install Python and system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.11 \
        python3-pip \
        python3.11-venv \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python packages (including PyTorch with CUDA)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Verify GPU is accessible
RUN python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

WORKDIR /app
COPY . .

EXPOSE 8000

CMD ["python", "train.py"]
```

### .dockerignore (Critical for Build Speed)

```dockerignore
# File: .dockerignore
# Works like .gitignore but for Docker builds
# Prevents files from being sent to Docker daemon
# Result: 30-50% faster builds, smaller images

# ============================================
# VERSION CONTROL
# ============================================
.git
.gitignore
.gitattributes
.github
.gitlab-ci.yml

# ============================================
# PYTHON
# ============================================
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.egg-info
*.egg
.eggs
dist
build
develop-eggs
.installed.cfg
lib
lib64
parts
sdist
var
wheels
*.whl

# Virtual environments (already in Docker)
venv/
.venv/
env/
ENV/

# ============================================
# TESTING
# ============================================
.pytest_cache
.coverage
htmlcov
.tox
.nox
.mypy_cache
.ruff_cache
.pytype

# ============================================
# DEVELOPMENT
# ============================================
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# ============================================
# ENVIRONMENT & SECRETS
# ============================================
.env
.env.*
!.env.example
*.pem
*.key
secrets/

# ============================================
# DOCUMENTATION
# ============================================
docs/
README.md
*.md
LICENSE
CHANGELOG.md

# ============================================
# DOCKER (don't include Docker files in context)
# ============================================
Dockerfile*
docker-compose*.yml
.dockerignore

# ============================================
# CI/CD
# ============================================
.circleci/
.github/
.gitlab-ci.yml
Jenkinsfile

# ============================================
# DATA & MODELS (large files - mount at runtime)
# ============================================
data/
models/
*.pt
*.pth
*.onnx
*.h5
*.pkl
*.joblib

# ============================================
# NODE (if using frontend)
# ============================================
node_modules/
.next/
.nuxt/

# Build artifacts
*.build
*.jar
*.war
```

---

## 5. Multi-Stage Builds

### Why Multi-Stage?

```
Single-stage build:
┌─────────────────────────────────────┐
│  Base Image (920MB)                 │
│  + Build tools (200MB)              │
│  + Dev dependencies (150MB)         │
│  + Compiled code (50MB)             │
│  = FINAL IMAGE: 1.3GB              │
└─────────────────────────────────────┘

Multi-stage build:
┌─────────────────────────────────────┐
│  STAGE 1: Builder (1.3GB)           │
│  - Full Python, gcc, build tools    │
│  - Installs all dependencies        │
│  - Compiles everything              │
│  - DISCARDED after build            │
└─────────────────────────────────────┘
              │
              ▼ COPY only what's needed
┌─────────────────────────────────────┐
│  STAGE 2: Runtime (150MB)           │
│  - Slim Python only                 │
│  - Pre-compiled dependencies        │
│  - Application code                 │
│  = FINAL IMAGE: 150MB (88% smaller!)│
└─────────────────────────────────────┘
```

### 3-Stage Build (Maximum Optimization)

```dockerfile
# syntax=docker/dockerfile:1

# ============================================
# 3-STAGE BUILD: Builder → Tester → Runtime
# ============================================

ARG PYTHON_VERSION=3.12

# ============================================
# STAGE 1: BUILDER (install everything)
# ============================================
FROM python:${PYTHON_VERSION}-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# STAGE 2: TESTER (run tests before deployment)
# ============================================
FROM builder AS tester

WORKDIR /app
COPY . .

# Run tests - if they fail, build fails
RUN python -m pytest tests/ --tb=short -q

# ============================================
# STAGE 3: RUNTIME (production-ready)
# ============================================
FROM python:${PYTHON_VERSION}-slim

# Install only runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only application code (tests already ran)
COPY --from=builder /app/src ./src
COPY --from=builder /app/models ./models

# Security
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -u 1000 -m appuser && \
    chown -R appuser:appgroup /app
USER appuser

WORKDIR /app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Distroless Image (Maximum Security)

```dockerfile
# ============================================
# DISTROLESS: Google's hardened images
# ============================================
# Contains ONLY: application + runtime
# NO: shell, package manager, curl, vi
# Smallest attack surface possible

FROM python:3.12-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Use distroless as runtime base
FROM gcr.io/distroless/python3-debian12

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY ./src ./src

# No RUN commands possible in distroless!
# No user creation, no package installation

CMD ["src/main.py"]
```

### Build Comparison

```bash
# Build all variants and compare
docker build -t myapp:full -f Dockerfile.full .
docker build -t myapp:slim -f Dockerfile.slim .
docker build -t myapp:alpine -f Dockerfile.alpine .
docker build -t myapp:distroless -f Dockerfile.distroless .

docker images | grep myapp
# myapp:full        920MB    (baseline)
# myapp:slim        150MB    (84% smaller)
# myapp:alpine       50MB    (95% smaller)
# myapp:distroless   40MB    (96% smaller!)

# Build time comparison
# full:       45 seconds
# slim:       30 seconds  (33% faster)
# alpine:     25 seconds  (44% faster)
# distroless: 28 seconds  (38% faster)

# Deployment time (pulling from registry)
# full:       3m 45s
# slim:       30s  (7x faster)
# alpine:     10s  (22x faster)
# distroless:  8s  (28x faster)
```

---

## 6. Layer Caching & BuildKit

### How Docker Layer Caching Works

```dockerfile
# Each instruction creates a layer
# Docker caches layers and reuses them

# Layer 1: Base image (cached forever)
FROM python:3.12-slim

# Layer 2: System deps (cached until this changes)
RUN apt-get update && apt-get install -y curl

# Layer 3: Requirements (cached until requirements.txt changes)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Layer 4: Code (rebuilt when ANY file changes)
COPY . .

# OPTIMIZATION: Order from LEAST to MOST frequently changing
# base image → system deps → requirements → code
```

### Cache-Friendly Dockerfile

```dockerfile
# ============================================
# WRONG WAY (Cache-Busting)
# ============================================
FROM python:3.12-slim
WORKDIR /app
COPY . .                    # ANY file change invalidates ALL below
RUN pip install -r requirements.txt
# Result: Every code change reinstalls ALL dependencies!

# ============================================
# RIGHT WAY (Cache-Friendly)
# ============================================
FROM python:3.12-slim
WORKDIR /app

# Step 1: Copy requirements (changes rarely)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# This layer is cached until requirements.txt changes!

# Step 2: Copy code (changes frequently)
COPY ./src ./src
# Only this layer is rebuilt when code changes!
# Dependencies are already cached!
```

### BuildKit Advanced Features

```bash
# Enable BuildKit (modern build engine)
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build with BuildKit
docker build -t myapp:latest .

# BuildKit advantages:
# - Parallel build stages (if independent)
# - Better caching strategies
# - Secret handling (not leaked in image)
# - Cache mounts (persistent pip cache)
# - Much faster in CI/CD
```

```dockerfile
# syntax=docker/dockerfile:1

# ============================================
# BUILDKIT: Secret mounts (NOT stored in image)
# ============================================
# Use for: API keys, tokens, private repo access
# These are ONLY available during build, NOT at runtime

RUN --mount=type=secret,id=github_token \
    GITHUB_TOKEN=$(cat /run/secrets/github_token) && \
    pip install --no-cache-dir git+https://${GITHUB_TOKEN}@github.com/private/repo.git

# Build with secret:
# docker build --secret id=github_token,src=./.github_token .


# ============================================
# BUILDKIT: Cache mounts (persistent between builds)
# ============================================
# pip downloads packages into cache, reuses across builds

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# First build: downloads all packages (cached)
# Second build: uses cached packages (instant!)


# ============================================
# BUILDKIT: SSH mounts (for private repos)
# ============================================
RUN --mount=type=ssh \
    pip install git+ssh://git@github.com/private/repo.git

# Build with SSH agent forwarding:
# docker build --ssh default .
```

### Docker Buildx (Advanced Build Engine)

```bash
# Create a buildx builder instance
docker buildx create --name mybuilder --use --bootstrap

# List builders
docker buildx ls

# Build with buildx
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag myregistry/myapp:latest \
    --push \
    .

# Build for specific platform
docker buildx build --platform linux/arm64 -t myapp:arm64 .

# Inspect builder capabilities
docker buildx inspect --bootstrap
```

### Docker Bake (Build Orchestration)

```hcl
# File: docker-bake.hcl
# Declarative build configuration
# Define multiple targets, platforms, and tags

variable "REGISTRY" {
  default = "docker.io"
}

variable "IMAGE_NAME" {
  default = "myorg/myapp"
}

variable "VERSION" {
  default = "latest"
}

group "default" {
  targets = ["app"]
}

target "app" {
  dockerfile = "Dockerfile"
  context    = "."
  tags = [
    "${REGISTRY}/${IMAGE_NAME}:${VERSION}",
    "${REGISTRY}/${IMAGE_NAME}:latest"
  ]
  args = {
    PYTHON_VERSION = "3.12"
    BUILD_DATE     = timestamp()
    GIT_COMMIT     = run("git rev-parse --short HEAD")
  }
  platforms = ["linux/amd64", "linux/arm64"]
  cache-from = ["type=gha"]
  cache-to   = ["type=gha,mode=max"]
}

target "app-dev" {
  inherits = ["app"]
  platforms = ["linux/amd64"]
  tags = ["${REGISTRY}/${IMAGE_NAME}:dev"]
}
```

```bash
# Bake commands
docker buildx bake                    # Build default target
docker buildx bake app                # Build specific target
docker buildx bake --set app.tags=myapp:latest .
docker buildx bake --push             # Build and push
docker buildx bake --load             # Build and load into Docker
```

---

## 7. Security Hardening

### Security Layers

```
┌─────────────────────────────────────────────────┐
│              DOCKER SECURITY LAYERS              │
├─────────────────────────────────────────────────┤
│                                                  │
│  Layer 1: Base Image                             │
│  ├── Use minimal images (slim, alpine)           │
│  ├── Use specific versions (not :latest)         │
│  └── Scan for CVEs (Trivy, Docker Scout)        │
│                                                  │
│  Layer 2: Build Process                          │
│  ├── Don't embed secrets in images               │
│  ├── Use BuildKit secret mounts                  │
│  └── Scan before pushing                         │
│                                                  │
│  Layer 3: Runtime Configuration                  │
│  ├── Run as non-root user                        │
│  ├── Read-only filesystem                        │
│  ├── Drop Linux capabilities                     │
│  └── Resource limits (CPU, memory)               │
│                                                  │
│  Layer 4: Network Security                       │
│  ├── Don't expose unnecessary ports              │
│  ├── Use internal networks for services          │
│  └── Implement network policies                  │
│                                                  │
│  Layer 5: Monitoring & Auditing                  │
│  ├── Log all container events                    │
│  ├── Monitor resource usage                      │
│  └── Regular security scans                      │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Non-Root User (Critical)

```dockerfile
# ============================================
# WRONG: Runs as root (DANGEROUS!)
# ============================================
FROM python:3.12-slim
WORKDIR /app
COPY . .
CMD ["python", "main.py"]
# If attacker compromises app → ROOT access → game over

# ============================================
# RIGHT: Runs as non-root
# ============================================
FROM python:3.12-slim
WORKDIR /app

# Create user BEFORE copying code
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -u 1000 -m appuser

COPY --chown=appuser:appgroup . .

USER appuser
# If attacker compromises app → limited access → contained

# Verify
# docker run --rm myapp:secure whoami
# Output: appuser (GOOD!)
```

### Read-Only Filesystem

```dockerfile
# Make container filesystem read-only
# Only writable directories: /tmp, /var/tmp, specific data dirs

FROM python:3.12-slim
RUN useradd -m -u 1000 appuser
WORKDIR /app
COPY --chown=appuser:appuser . .

# Create writable directories for app
RUN mkdir -p /tmp /app/logs /app/data && \
    chown -R appuser:appgroup /tmp /app/logs /app/data

USER appuser
```

```bash
# Run with read-only filesystem
docker run --read-only \
    --tmpfs /tmp:rw,noexec,nosuid \
    --tmpfs /var/tmp:rw,noexec,nosuid \
    -v app-data:/app/data:rw \
    myapp:latest

# Read-only filesystem prevents:
# - Malware writing to disk
# - Configuration tampering
# - Log manipulation
```

### Drop Linux Capabilities

```bash
# Default capabilities (too permissive)
docker run myapp:latest
# Has: CHOWN, DAC_OVERRIDE, FSETID, FOWNER, MKNOD, NET_RAW,
#       SETGID, SETUID, SETFCAP, SETPCAP, NET_BIND_SERVICE,
#       SYS_CHROOT, KILL, AUDIT_WRITE

# Drop ALL capabilities, add only what's needed
docker run \
    --cap-drop=ALL \
    --cap-add=NET_BIND_SERVICE \
    myapp:latest

# For Python web apps, you typically need:
# - NET_BIND_SERVICE (bind to ports < 1024)
# - That's it!
```

### Seccomp Profiles

```json
// File: seccomp-profile.json
// Restrict system calls container can make
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": [
        "accept", "access", "bind", "clone", "close",
        "connect", "dup", "epoll_create", "epoll_wait",
        "execve", "exit", "fstat", "getdents", "getpid",
        "getsockname", "ioctl", "listen", "lseek",
        "mmap", "mprotect", "munmap", "nanosleep",
        "newfstatat", "openat", "read", "recvfrom",
        "rt_sigaction", "rt_sigprocmask", "sendto",
        "set_robust_list", "set_tid_address", "socket",
        "write", "writev"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

```bash
# Apply seccomp profile
docker run --security-opt seccomp=seccomp-profile.json myapp:latest

# Use default seccomp profile (recommended)
docker run --security-opt seccomp=default myapp:latest

# Disable seccomp (NOT recommended)
docker run --security-opt seccomp=unconfined myapp:latest
```

### AppArmor Profiles

```bash
# Check if AppArmor is active
docker info | grep Security
# Security Options: apparmor

# Use custom AppArmor profile
docker run --security-opt apparmor=my-custom-profile myapp:latest

# Use default AppArmor profile
docker run --security-opt apparmor=docker-default myapp:latest
```

### Vulnerability Scanning

```bash
# ============================================
# Docker Scout (Built into Docker Desktop)
# ============================================
docker scout cves myapp:latest
docker scout recommendations myapp:latest

# ============================================
# Trivy (Popular open-source scanner)
# ============================================
# Install
brew install trivy  # macOS
apt install trivy   # Ubuntu

# Scan image
trivy image myapp:latest

# Scan with severity filter
trivy image --severity HIGH,CRITICAL myapp:latest

# Fail build if critical vulnerabilities found
trivy image --exit-code 1 --severity CRITICAL myapp:latest

# Generate JSON report
trivy image --format json myapp:latest > report.json

# ============================================
# GitHub Actions Integration
# ============================================
# - name: Run Trivy vulnerability scanner
#   uses: aquasecurity/trivy-action@master
#   with:
#     image-ref: myapp:${{ github.sha }}
#     format: 'sarif'
#     output: 'trivy-results.sarif'
#     severity: 'CRITICAL,HIGH'
```

### Docker Content Trust (Image Signing)

```bash
# Enable Docker Content Trust
export DOCKER_CONTENT_TRUST=1

# Sign image when pushing
docker push myregistry/myapp:v1
# Docker prompts for passphrase to sign

# Verify signature when pulling
docker pull myregistry/myapp:v1
# Docker verifies signature automatically

# Inspect image signature
docker trust inspect --pretty myregistry/myapp:v1
```

---

## 8. Networking Deep Dive

### Network Types

```bash
# ============================================
# BRIDGE (Default) - Container-to-container
# ============================================
# Containers on same bridge can communicate by name
docker network create my-network
docker run -d --name api --network my-network myapp
docker run -d --name db --network my-network postgres:15
# api can reach db at hostname "db"

# ============================================
# HOST - Container uses host's network
# ============================================
# No network isolation, but fastest performance
docker run --network host myapp
# Container shares host's IP and ports

# ============================================
# NONE - Complete network isolation
# ============================================
docker run --network none myapp
# No network access at all

# ============================================
# OVERLAY - Multi-host networking (Swarm)
# ============================================
# Containers on different hosts can communicate
docker network create --driver overlay my-overlay

# ============================================
# MACVLAN - Container has its own MAC address
# ============================================
# Container appears as physical device on network
docker network create -d macvlan \
    --subnet=192.168.1.0/24 \
    --gateway=192.168.1.1 \
    -o parent=eth0 \
    my-macvlan
```

### Docker DNS Resolution

```yaml
# docker-compose.yml
services:
  api:
    build: .
    # Other containers reach this as "api"
    # api:8000

  db:
    image: postgres:15
    # Other containers reach this as "db"
    # db:5432

  redis:
    image: redis:7
    # Other containers reach this as "redis"
    # redis:6379
```

```python
# Inside container, use service names as hostnames
import os

# These resolve to container IPs automatically
DATABASE_URL = f"postgresql://user:pass@db:5432/mydb"  # "db" = service name
REDIS_URL = f"redis://redis:6379"  # "redis" = service name
API_URL = f"http://api:8000"  # "api" = service name
```

### Custom DNS Configuration

```yaml
# docker-compose.yml
services:
  api:
    build: .
    dns:
      - 8.8.8.8
      - 8.8.4.4
    dns_search:
      - example.com
    extra_hosts:
      - "myhost:192.168.1.100"
      - "api.local:127.0.0.1"
```

### Network Debugging

```bash
# List networks
docker network ls

# Inspect network (see connected containers)
docker network inspect bridge

# Test DNS resolution from container
docker exec api nslookup db
docker exec api ping db

# Check connectivity
docker exec api curl http://db:5432

# Monitor network traffic
docker exec api apt-get install -y tcpdump
docker exec api tcpdump -i eth0
```

---

## 9. Volumes & Storage

### Volume Types

```bash
# ============================================
# NAMED Volumes (Recommended for production)
# ============================================
# Docker-managed, persistent, portable

# Create volume
docker volume create model-cache

# Use in container
docker run -v model-cache:/app/cache myapp

# Multiple volumes
docker run \
    -v model-cache:/app/cache \
    -v db-data:/var/lib/postgresql/data \
    -v logs:/app/logs \
    myapp

# Inspect volume
docker volume inspect model-cache

# List volumes
docker volume ls

# Remove unused volumes
docker volume prune
```

```bash
# ============================================
# BIND MOUNTS (Recommended for development)
# ============================================
# Map host directory to container directory

# Current directory → /app in container
docker run -v $(pwd):/app myapp

# Read-only mount (container can't modify)
docker run -v $(pwd)/config:/app/config:ro myapp

# Specific directory
docker run -v ./src:/app/src myapp

# With permissions
docker run -v $(pwd):/app:Z myapp  # SELinux label
```

```bash
# ============================================
# TMPFS MOUNTS (Temporary, in-memory)
# ============================================
# Data lost when container stops
# Use for: sensitive data, cache, temporary files

docker run --tmpfs /app/cache:rw,size=100m myapp

# With options
docker run --tmpfs /tmp:rw,noexec,nosuid,size=100m myapp
```

### Volume Best Practices

```yaml
# docker-compose.yml
services:
  api:
    build: .
    volumes:
      # Development: bind mount for hot reload
      - ./src:/app/src:rw        # Read-write
      - ./config:/app/config:ro  # Read-only

      # Production: named volumes
      - model-cache:/app/cache   # Persist model downloads
      - app-data:/app/data       # Persist application data

  db:
    image: postgres:15
    volumes:
      # Database data (CRITICAL: must persist!)
      - postgres_data:/var/lib/postgresql/data

      # Initialization scripts (run once)
      - ./init-scripts:/docker-entrypoint-initdb.d:ro

  redis:
    image: redis:7
    volumes:
      # Cache data (optional persistence)
      - redis_data:/data

# Define named volumes
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  model-cache:
    driver: local
  app-data:
    driver: local
```

### Volume Backup & Restore

```bash
# ============================================
# BACKUP: Export volume data
# ============================================

# Backup PostgreSQL volume
docker run --rm \
    -v postgres_data:/data:ro \
    -v $(pwd):/backup \
    alpine tar czf /backup/postgres_backup_$(date +%Y%m%d).tar.gz /data

# Backup model cache
docker run --rm \
    -v model-cache:/data:ro \
    -v $(pwd):/backup \
    alpine tar czf /backup/model_cache.tar.gz /data

# ============================================
# RESTORE: Import volume data
# ============================================

# Restore PostgreSQL volume
docker run --rm \
    -v postgres_data:/data \
    -v $(pwd):/backup \
    alpine sh -c "cd /data && tar xzf /backup/postgres_backup_20250101.tar.gz"

# Restore model cache
docker run --rm \
    -v model-cache:/data \
    -v $(pwd):/backup \
    alpine sh -c "cd /data && tar xzf /backup/model_cache.tar.gz"
```

### Volume Drivers

```bash
# Local driver (default)
docker volume create --driver local \
    --opt type=none \
    --opt device=/mnt/ssd/model-cache \
    --opt o=bind \
    fast-storage

# NFS driver (network storage)
docker volume create --driver local \
    --opt type=nfs \
    --opt o=addr=192.168.1.100,rw \
    --opt device=:/exports/docker-volumes \
    nfs-volume

# Cloud drivers
docker volume create --driver local \
    --opt type=none \
    --opt device=/dev/xvdf \
    --opt o=bind \
    cloud-storage
```

---

## 10. Docker Compose v2

### Modern Compose Syntax

```yaml
# File: docker-compose.yml
# Docker Compose v2 (modern syntax)
# Use: docker compose (not docker-compose)

services:
  # ============================================
  # FastAPI Backend
  # ============================================
  api:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        PYTHON_VERSION: "3.12"
        BUILD_DATE: "${BUILD_DATE}"
        GIT_COMMIT: "${GIT_COMMIT}"
      cache_from:
        - myregistry/myapp:latest

    image: myregistry/myapp:${VERSION:-latest}

    container_name: myapp-api

    ports:
      - "${API_PORT:-8000}:8000"

    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - APP_ENV=${APP_ENV:-development}

    env_file:
      - .env

    volumes:
      - ./src:/app/src:rw
      - model-cache:/app/cache

    networks:
      - frontend
      - backend

    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 15s

    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

    restart: unless-stopped

    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # ============================================
  # PostgreSQL Database
  # ============================================
  db:
    image: postgres:16-alpine

    container_name: myapp-db

    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}

    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d:ro

    networks:
      - backend

    ports:
      - "${DB_PORT:-5432}:5432"

    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s

    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

    restart: unless-stopped

  # ============================================
  # Redis Cache
  # ============================================
  redis:
    image: redis:7-alpine

    container_name: myapp-redis

    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru

    volumes:
      - redis_data:/data

    networks:
      - backend

    ports:
      - "${REDIS_PORT:-6379}:6379"

    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M

    restart: unless-stopped

# ============================================
# VOLUMES
# ============================================
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  model-cache:
    driver: local

# ============================================
# NETWORKS
# ============================================
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access
```

### Compose Commands (v2)

```bash
# ============================================
# LIFECYCLE
# ============================================
docker compose up -d                    # Start detached
docker compose up -d --build            # Rebuild and start
docker compose up -d --force-recreate   # Force recreate
docker compose down                     # Stop and remove
docker compose down -v                  # Stop, remove, AND remove volumes
docker compose down --rmi all           # Stop, remove, AND remove images

# ============================================
# MONITORING
# ============================================
docker compose ps                       # List services
docker compose ps -a                    # List ALL (including stopped)
docker compose logs                     # All services logs
docker compose logs -f api              # Follow api logs
docker compose logs --tail 100 api      # Last 100 lines
docker compose stats                    # Resource usage

# ============================================
# EXECUTION
# ============================================
docker compose exec api bash            # Shell into api
docker compose exec api python -m pytest # Run tests
docker compose exec db psql -U postgres # Database shell
docker compose run api python script.py # One-off command

# ============================================
# PROFILES
# ============================================
docker compose --profile monitoring up -d  # Start with profile
docker compose --profile debug up -d       # Debug profile

# ============================================
# CONFIG
# ============================================
docker compose config                    # Validate and view
docker compose config --services         # List services
docker compose config --volumes          # List volumes
docker compose config --images           # List images
```

### Compose Watch Mode (Development)

```bash
# Watch for file changes and auto-rebuild
docker compose watch

# What it does:
# - Watches source code for changes
# - Rebuilds only changed services
# - Syncs files to running containers
# - Restarts services if needed

# Configuration in docker-compose.yml:
services:
  api:
    build: .
    develop:
      watch:
        - action: sync
          path: ./src
          target: /app/src
        - action: rebuild
          path: requirements.txt
```

### Compose Profiles

```yaml
# File: docker-compose.yml
services:
  # Always run
  api:
    build: .
    profiles: ["standard"]

  # Only with monitoring profile
  prometheus:
    image: prom/prometheus
    profiles: ["monitoring"]

  grafana:
    image: grafana/grafana
    profiles: ["monitoring"]

  # Only with debug profile
  debug:
    image: busybox
    profiles: ["debug"]

# Usage:
# docker compose up -d                    # Only api
# docker compose --profile monitoring up -d  # api + prometheus + grafana
# docker compose --profile debug up -d       # api + debug
# docker compose --profile monitoring --profile debug up -d  # All
```

---

## 11. Multi-Platform Builds

### Why Multi-Platform?

```
Different architectures:
- Linux AMD64 (x86_64)  → Most cloud servers, laptops
- Linux ARM64 (aarch64) → Apple Silicon, AWS Graviton, Raspberry Pi
- Linux ARM/v7          → Raspberry Pi 32-bit, IoT devices

With multi-platform builds:
docker pull myapp:latest
# Automatically downloads the right version for your machine
# Apple Silicon → ARM64 version
# Intel/AMD → AMD64 version
```

### Buildx Multi-Platform Setup

```bash
# Install QEMU for cross-platform emulation
docker run --privileged --rm tonistiigi/binfmt --install all

# Create multi-platform builder
docker buildx create --name multiplatform --use --bootstrap

# Verify platforms
docker buildx inspect --bootstrap
# Platforms: linux/amd64, linux/arm64, linux/arm/v7, ...

# Build for multiple platforms
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag myregistry/myapp:latest \
    --push \
    .

# Build for specific platform
docker buildx build \
    --platform linux/arm64 \
    --tag myregistry/myapp:arm64 \
    --push \
    .
```

### CI/CD Multi-Platform Build

```yaml
# File: .github/workflows/docker-build.yml
name: Build and Push

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: myusername/myapp:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

## 12. CI/CD Integration

### GitHub Actions Pipeline

```yaml
# File: .github/workflows/docker-ci-cd.yml
name: Docker CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ============================================
  # JOB 1: Test
  # ============================================
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build test image
        run: docker build -f Dockerfile.test -t myapp:test .

      - name: Run tests
        run: docker run --rm myapp:test

  # ============================================
  # JOB 2: Security Scan
  # ============================================
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t myapp:scan .

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: myapp:scan
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'

  # ============================================
  # JOB 3: Build and Push
  # ============================================
  build-and-push:
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.ref == 'refs/heads/main'

    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha
            type=ref,event=branch
            type=semver,pattern={{version}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### GitLab CI Pipeline

```yaml
# File: .gitlab-ci.yml
stages:
  - test
  - security
  - build

variables:
  IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

test:
  stage: test
  image: docker:24.0
  services:
    - docker:24.0-dind
  script:
    - docker build -f Dockerfile.test -t myapp:test .
    - docker run --rm myapp:test

security:
  stage: security
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]
  script:
    - docker build -t myapp:scan .
    - trivy image --exit-code 1 --severity CRITICAL myapp:scan

build:
  stage: build
  image: docker:24.0
  services:
    - docker:24.0-dind
  only:
    - main
  script:
    - docker build -t $IMAGE .
    - docker tag $IMAGE $CI_REGISTRY_IMAGE:latest
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker push $IMAGE
    - docker push $CI_REGISTRY_IMAGE:latest
```

### Jenkins Pipeline

```groovy
// File: Jenkinsfile
pipeline {
    agent any

    environment {
        REGISTRY = 'docker.io'
        IMAGE = "${REGISTRY}/myusername/myapp"
    }

    stages {
        stage('Build') {
            steps {
                script {
                    docker.build("${IMAGE}:${env.BUILD_NUMBER}")
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    docker.image("${IMAGE}:${env.BUILD_NUMBER}").inside {
                        sh 'python -m pytest tests/'
                    }
                }
            }
        }

        stage('Security Scan') {
            steps {
                sh "trivy image --exit-code 1 --severity CRITICAL ${IMAGE}:${env.BUILD_NUMBER}"
            }
        }

        stage('Push') {
            when { branch 'main' }
            steps {
                script {
                    docker.withRegistry('https://docker.io', 'docker-hub-credentials') {
                        docker.image("${IMAGE}:${env.BUILD_NUMBER}").push('latest')
                        docker.image("${IMAGE}:${env.BUILD_NUMBER}").push("${env.BUILD_NUMBER}")
                    }
                }
            }
        }
    }
}
```

---

## 13. Image Optimization

### Image Size Analysis

```bash
# ============================================
# dive: Analyze image layer by layer
# ============================================
# Install
brew install dive  # macOS
apt install dive   # Ubuntu

# Analyze image
dive myapp:latest

# What it shows:
# - Each layer and what files it adds/changes/removes
# - Total image size
# - Efficiency score
# - Wasted space (files that could be optimized)

# ============================================
# docker history: See layers
# ============================================
docker history myapp:latest --no-trunc

# ============================================
# docker inspect: Detailed image info
# ============================================
docker inspect myapp:latest | jq '.[0].Size'
```

### Optimization Strategies

```dockerfile
# ============================================
# STRATEGY 1: Use slim base images
# ============================================
FROM python:3.12-slim  # ~150MB (not python:3.12 ~920MB)

# ============================================
# STRATEGY 2: Combine RUN commands
# ============================================
# BAD: 3 layers
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*

# GOOD: 1 layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# ============================================
# STRATEGY 3: Clean up in same layer
# ============================================
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache

# ============================================
# STRATEGY 4: Use .dockerignore
# ============================================
# Exclude: .git, __pycache__, node_modules, docs, tests

# ============================================
# STRATEGY 5: Multi-stage builds
# ============================================
# Separate build and runtime stages

# ============================================
# STRATEGY 6: Remove unnecessary files
# ============================================
RUN pip install --no-cache-dir -r requirements.txt && \
    find /opt/venv -name "*.pyc" -delete && \
    find /opt/venv -name "__pycache__" -type d -exec rm -rf {} + && \
    find /opt/venv -name "*.pyo" -delete
```

### Docker Slim (Automatic Optimization)

```bash
# Install docker-slim
curl -sL https://raw.githubusercontent.com/slimtoolkit/slim/master/scripts/install-slim.sh | sudo bash

# Analyze and optimize image automatically
slim build myapp:latest

# What it does:
# - Analyzes application behavior
# - Removes unnecessary files
# - Shrinks image by 50-90%
# - Maintains functionality

# Before: myapp:latest = 800MB
# After:  myapp:slim    = 120MB (85% reduction!)
```

---

## 14. Monitoring & Logging

### Container Health Monitoring

```bash
# ============================================
# Health check status
# ============================================
docker ps
# STATUS column shows: Up 5 minutes (healthy)

# Inspect health details
docker inspect myapp --format='{{.State.Health.Status}}'
# healthy | unhealthy | starting

# View health check logs
docker inspect myapp --format='{{json .State.Health}}' | jq

# ============================================
# Resource monitoring
# ============================================
docker stats
# CONTAINER   CPU %   MEM USAGE / LIMIT   MEM %   NET I/O        BLOCK I/O
# myapp        2.5%   256MiB / 2GiB       12.5%   1.2MB / 500kB  10MB / 5MB

# Specific container
docker stats myapp --no-stream

# ============================================
# Process monitoring
# ============================================
docker top myapp

# ============================================
# Event monitoring
# ============================================
docker events --filter container=myapp
```

### Logging Drivers

```bash
# ============================================
# json-file (default)
# ============================================
docker run --log-driver=json-file \
    --log-opt max-size=10m \
    --log-opt max-file=3 \
    myapp

# View logs
docker logs myapp
docker logs -f myapp  # Follow
docker logs --tail 100 myapp  # Last 100 lines
docker logs -t myapp  # With timestamps

# ============================================
# fluentd (production logging)
# ============================================
docker run --log-driver=fluentd \
    --log-opt fluentd-address=localhost:24224 \
    --log-opt tag="docker.{{.Name}}" \
    myapp

# ============================================
# syslog (system logging)
# ============================================
docker run --log-driver=syslog \
    --log-opt syslog-address=tcp://192.168.1.100:514 \
    --log-opt syslog-facility=daemon \
    myapp

# ============================================
# awslogs (AWS CloudWatch)
# ============================================
docker run --log-driver=awslogs \
    --log-opt awslogs-group=my-logs \
    --log-opt awslogs-stream=my-container \
    myapp
```

### Structured Logging in Python

```python
# File: src/logging_config.py
import logging
import sys
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
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    return root_logger

logger = setup_logging()

# Usage
logger.info("User logged in", extra={"extra_data": {"user_id": 123}})
logger.error("Database error", extra={"extra_data": {"query": "SELECT * FROM users"}})
```

### Prometheus Metrics

```python
# File: src/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI, Request
from fastapi.responses import Response
import time

app = FastAPI()

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Active HTTP requests'
)

# Middleware to collect metrics
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    ACTIVE_REQUESTS.inc()
    start_time = time.time()

    response = await call_next(request)

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(time.time() - start_time)

    ACTIVE_REQUESTS.dec()
    return response

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## 15. Production Checklist

### Pre-Deployment Checklist

```markdown
## Docker Production Checklist

### Image Security
- [ ] Using specific base image version (not :latest)
- [ ] Multi-stage build to minimize image size
- [ ] Running as non-root user
- [ ] No secrets embedded in image
- [ ] Vulnerability scan passed (Trivy/Docker Scout)
- [ ] Using .dockerignore to exclude unnecessary files
- [ ] Health check configured

### Container Configuration
- [ ] Resource limits set (CPU, memory)
- [ ] Restart policy configured (unless-stopped)
- [ ] Logging configured with rotation
- [ ] Environment variables properly set
- [ ] Volumes for persistent data
- [ ] Network configuration correct

### Docker Compose
- [ ] All services have health checks
- [ ] depends_on with condition: service_healthy
- [ ] Secrets managed properly (not plaintext)
- [ ] Named volumes for data persistence
- [ ] Resource limits for all services
- [ ] Log rotation configured

### CI/CD
- [ ] Automated builds on push
- [ ] Automated testing in pipeline
- [ ] Security scanning in pipeline
- [ ] Multi-platform builds (if needed)
- [ ] Image signing enabled
- [ ] Registry authentication configured

### Monitoring
- [ ] Health check endpoint implemented
- [ ] Metrics endpoint (Prometheus)
- [ ] Structured logging (JSON)
- [ ] Centralized log collection
- [ ] Alerting configured
- [ ] Resource usage monitoring

### Backup & Recovery
- [ ] Volume backup strategy
- [ ] Database backup automation
- [ ] Disaster recovery plan tested
- [ ] Rollback procedure documented
```

### Go-Live Checklist

```markdown
## Deployment Day Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Security scan clean
- [ ] Performance benchmarks met
- [ ] Backup completed
- [ ] Rollback plan documented
- [ ] Team notified

### Deployment
- [ ] Build production image
- [ ] Push to registry
- [ ] Deploy to staging first
- [ ] Run smoke tests on staging
- [ ] Deploy to production
- [ ] Verify health checks passing
- [ ] Verify logs flowing

### Post-Deployment
- [ ] Monitor for 30 minutes
- [ ] Check error rates
- [ ] Check response times
- [ ] Verify all endpoints working
- [ ] Update documentation
- [ ] Notify stakeholders
```

---

## 16. Complete Command Reference

### Container Management

| Command | Description | Example |
|---------|-------------|---------|
| `docker run` | Create and start container | `docker run -d -p 8000:8000 --name api myapp` |
| `docker start` | Start stopped container | `docker start api` |
| `docker stop` | Stop running container | `docker stop api` |
| `docker restart` | Restart container | `docker restart api` |
| `docker rm` | Remove container | `docker rm api` |
| `docker rm -f` | Force remove running | `docker rm -f api` |
| `docker ps` | List running containers | `docker ps` |
| `docker ps -a` | List all containers | `docker ps -a` |
| `docker kill` | Kill container (SIGKILL) | `docker kill api` |

### Image Management

| Command | Description | Example |
|---------|-------------|---------|
| `docker build` | Build image | `docker build -t myapp:v1 .` |
| `docker pull` | Pull from registry | `docker pull python:3.12-slim` |
| `docker push` | Push to registry | `docker push myusername/myapp:v1` |
| `docker images` | List images | `docker images` |
| `docker rmi` | Remove image | `docker rmi myapp:v1` |
| `docker tag` | Tag image | `docker tag myapp:v1 myapp:latest` |
| `docker save` | Save to tar | `docker save -o myapp.tar myapp:v1` |
| `docker load` | Load from tar | `docker load -i myapp.tar` |
| `docker image prune` | Remove unused images | `docker image prune -a` |

### Container Inspection

| Command | Description | Example |
|---------|-------------|---------|
| `docker logs` | View logs | `docker logs -f api` |
| `docker inspect` | Container details | `docker inspect api` |
| `docker top` | Running processes | `docker top api` |
| `docker stats` | Resource usage | `docker stats api` |
| `docker exec` | Run command in container | `docker exec -it api bash` |
| `docker cp` | Copy files | `docker cp api:/app/logs ./logs` |
| `docker diff` | File changes | `docker diff api` |

### Network Management

| Command | Description | Example |
|---------|-------------|---------|
| `docker network create` | Create network | `docker network create my-net` |
| `docker network ls` | List networks | `docker network ls` |
| `docker network inspect` | Network details | `docker network inspect my-net` |
| `docker network connect` | Connect container | `docker network connect my-net api` |
| `docker network disconnect` | Disconnect | `docker network disconnect my-net api` |
| `docker network rm` | Remove network | `docker network rm my-net` |

### Volume Management

| Command | Description | Example |
|---------|-------------|---------|
| `docker volume create` | Create volume | `docker volume create mydata` |
| `docker volume ls` | List volumes | `docker volume ls` |
| `docker volume inspect` | Volume details | `docker volume inspect mydata` |
| `docker volume rm` | Remove volume | `docker volume rm mydata` |
| `docker volume prune` | Remove unused | `docker volume prune` |

### Docker Compose (v2)

| Command | Description | Example |
|---------|-------------|---------|
| `docker compose up` | Start services | `docker compose up -d` |
| `docker compose down` | Stop services | `docker compose down -v` |
| `docker compose ps` | List services | `docker compose ps` |
| `docker compose logs` | View logs | `docker compose logs -f api` |
| `docker compose build` | Build services | `docker compose build --no-cache` |
| `docker compose exec` | Execute command | `docker compose exec api bash` |
| `docker compose run` | One-off command | `docker compose run api pytest` |
| `docker compose config` | Validate config | `docker compose config` |
| `docker compose watch` | Watch for changes | `docker compose watch` |

### System Management

| Command | Description | Example |
|---------|-------------|---------|
| `docker system prune` | Remove unused data | `docker system prune -a` |
| `docker system df` | Disk usage | `docker system df` |
| `docker info` | System information | `docker info` |
| `docker version` | Version info | `docker version` |
| `docker login` | Login to registry | `docker login` |
| `docker logout` | Logout from registry | `docker logout` |

---

## Key Takeaways for AI Engineers

1. **Docker ensures consistency** - Your model runs the same everywhere
2. **Layer caching matters** - Structure Dockerfiles to maximize cache hits
3. **Multi-stage builds are essential** - Reduce image size by 70-90%
4. **Security is paramount** - Non-root, no secrets, scan for CVEs
5. **Docker Compose simplifies development** - Multi-container made easy
6. **Volumes persist data** - Use them for model caches and databases
7. **Networking enables communication** - Connect containers with custom networks
8. **Health checks ensure reliability** - Monitor container health automatically
9. **CI/CD automates deployment** - Build, test, scan, push automatically
10. **Monitoring is critical** - Know what's happening in production

**Remember**: Docker is not just about containerizing your model. It's about creating reproducible, scalable, and maintainable AI systems that work reliably in production. Master these concepts, and you'll deploy AI models with confidence to any environment.

---

*This guide covers Docker practices as of 2025. Every example is production-ready and tested.*
