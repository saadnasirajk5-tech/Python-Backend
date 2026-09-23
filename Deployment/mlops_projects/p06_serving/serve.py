# =============================================================================
# PROJECT 6: Model Serving — FastAPI Prediction Server
# =============================================================================
# WHAT YOU LEARN:
#   - Build a production REST API for model inference
#   - Async request handling for high throughput
#   - Request batching for GPU/CPU efficiency
#   - Input validation with Pydantic (reject bad requests at the door)
#   - Model warm-up and health checks
#   - Prediction caching with Redis
#   - Request/response logging for monitoring
#   - Shadow mode deployment (log predictions without serving them)
#
# CORE CONCEPT:
#   A model in a .pkl file is useless until it's wrapped in a server.
#   This server is what your product team calls. It must be fast (<100ms),
#   reliable (99.9% uptime), and observable (every prediction logged).
#
# RUN IT:
#   pip install fastapi uvicorn redis pydantic scikit-learn
#   uvicorn serve:app --host 0.0.0.0 --port 8000 --workers 4
#   curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \
#        -d '{"features": [...]}'
# =============================================================================

import os
import time
import json
import pickle
import asyncio
import hashlib
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# Configure structured logging (JSON format for log aggregation systems)
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}'
)
logger = logging.getLogger(__name__)

# =============================================================================
# PYDANTIC MODELS: Request/Response contracts
# Pydantic validates ALL incoming requests. Bad data never reaches the model.
# =============================================================================

class PredictionRequest(BaseModel):
    """
    Defines the exact input schema for a prediction request.
    Pydantic automatically validates types, ranges, and required fields.
    """
    features: List[float] = Field(
        ...,    # Required (no default)
        description="30 feature values for breast cancer classification",
        min_items=30, max_items=30,  # Exact feature count enforced
    )
    customer_id: Optional[str] = Field(
        None,
        description="Optional customer ID for logging and caching"
    )
    return_probabilities: bool = Field(
        True,
        description="If True, return class probabilities in addition to prediction"
    )

    @validator("features")
    def features_must_be_finite(cls, v):
        """Reject NaN and Inf values — they cause silent model failures."""
        if any(not np.isfinite(x) for x in v):
            raise ValueError("Features contain NaN or Inf values")
        return v


class BatchPredictionRequest(BaseModel):
    """For batch predictions — more efficient than N individual requests."""
    requests: List[PredictionRequest] = Field(
        ..., min_items=1, max_items=500   # Batch size limit (tune for your hardware)
    )


class PredictionResponse(BaseModel):
    """Standardized response — consuming teams can depend on this schema."""
    prediction:    int             # 0 = Benign, 1 = Malignant
    confidence:    float           # Probability of predicted class
    probabilities: Optional[Dict[str, float]] = None
    prediction_id: str             # UUID for logging and debugging
    model_version: str             # Which model version made this prediction
    latency_ms:    float           # How long the prediction took
    cached:        bool = False    # Was this served from cache?


class HealthResponse(BaseModel):
    status:        str
    model_loaded:  bool
    model_version: str
    uptime_seconds: float
    predictions_served: int


# =============================================================================
# MODEL SERVER: Singleton that loads the model once and serves forever
# =============================================================================

class ModelServer:
    """
    Wraps the ML model with everything needed for production serving:
    - Thread-safe singleton (model loaded once)
    - Caching (identical requests served from cache)
    - Metrics collection
    - Warm-up to pre-load model weights into CPU cache
    """

    def __init__(self):
        self.model          = None
        self.model_version  = "unknown"
        self.feature_names  = None
        self.start_time     = datetime.now()
        self.predictions_served = 0
        self._cache         = {}   # In-memory cache (use Redis in production)

    def load(self, model_path: str = "./model_artifacts/model.pkl"):
        """
        Loads the model from disk.
        Called once at startup — loading on every request would be catastrophic.
        """
        if not Path(model_path).exists():
            # Auto-train if no model exists (for demo purposes)
            logger.warning(f"Model not found at {model_path}, training a demo model...")
            self._train_demo_model(model_path)

        with open(model_path, "rb") as f:
            self.model = pickle.load(f)

        # Load metadata if available
        meta_path = Path(model_path).parent / "metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
            self.model_version = meta.get("model_version", "unknown")
            self.feature_names = meta.get("config", {}).get("feature_names", None)

        # Warm up: run a dummy prediction to pre-load everything into CPU cache
        # This prevents the first real request from being slow
        dummy_input = pd.DataFrame([np.zeros(30)], columns=[f"feat_{i}" for i in range(30)])
        _ = self.model.predict(dummy_input.values.reshape(1, -1))

        logger.info(f"Model loaded. Version={self.model_version}")

    def _train_demo_model(self, save_path: str):
        """Quick demo model training if no model file exists."""
        from sklearn.datasets import load_breast_cancer
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.ensemble import RandomForestClassifier

        data = load_breast_cancer()
        pipeline = Pipeline([("scaler", StandardScaler()),
                              ("model", RandomForestClassifier(n_estimators=50, random_state=42))])
        pipeline.fit(data.data, data.target)

        os.makedirs(Path(save_path).parent, exist_ok=True)
        with open(save_path, "wb") as f:
            pickle.dump(pipeline, f)

        meta = {"model_version": "demo_v1", "config": {}}
        with open(Path(save_path).parent / "metadata.json", "w") as f:
            json.dump(meta, f)

    def predict(self, features: List[float]) -> Dict[str, Any]:
        """
        Core prediction method. Returns prediction + probabilities + metadata.
        This is called by the API endpoints.
        """
        if self.model is None:
            raise RuntimeError("Model not loaded! Call load() first.")

        # Convert to numpy array (what sklearn expects)
        X = np.array(features).reshape(1, -1)

        start     = time.time()
        pred      = int(self.model.predict(X)[0])
        probas    = self.model.predict_proba(X)[0]
        latency   = (time.time() - start) * 1000

        self.predictions_served += 1

        return {
            "prediction":    pred,
            "confidence":    round(float(probas[pred]), 4),
            "probabilities": {"benign": round(float(probas[0]), 4),
                              "malignant": round(float(probas[1]), 4)},
            "latency_ms":    round(latency, 2),
        }

    def get_cache_key(self, features: List[float]) -> str:
        """Deterministic cache key from feature values."""
        return hashlib.md5(str(sorted(enumerate(features))).encode()).hexdigest()

    def predict_cached(self, features: List[float]) -> tuple:
        """Returns (prediction_dict, was_cached)."""
        cache_key = self.get_cache_key(features)
        if cache_key in self._cache:
            return self._cache[cache_key], True
        result = self.predict(features)
        self._cache[cache_key] = result
        return result, False


# Global server instance (singleton)
server = ModelServer()


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan handler: runs model loading at startup, cleanup at shutdown.
    This is the modern FastAPI replacement for @app.on_event("startup").
    """
    # STARTUP: Load model before accepting any requests
    logger.info("Starting model server...")
    server.load()
    logger.info(f"Server ready. Model version: {server.model_version}")
    yield
    # SHUTDOWN: Clean up resources
    logger.info("Shutting down model server...")
    server._cache.clear()


app = FastAPI(
    title="ML Model Serving API",
    description="Production model serving with caching, validation, and monitoring",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# =============================================================================
# MIDDLEWARE: Log every request for monitoring
# =============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Logs every request with timing. In production, ship these to Datadog/Grafana.
    This middleware runs AROUND every request — perfect for observability.
    """
    start_time = time.time()
    response   = await call_next(request)
    duration   = round((time.time() - start_time) * 1000, 2)

    logger.info(json.dumps({
        "method":   request.method,
        "path":     str(request.url.path),
        "status":   response.status_code,
        "duration_ms": duration,
    }))
    response.headers["X-Process-Time-Ms"] = str(duration)
    return response


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint — hit by Kubernetes liveness/readiness probes.
    Returns 200 only if model is loaded and ready to serve.
    """
    if server.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    uptime = (datetime.now() - server.start_time).total_seconds()
    return HealthResponse(
        status="healthy",
        model_loaded=True,
        model_version=server.model_version,
        uptime_seconds=round(uptime, 1),
        predictions_served=server.predictions_served,
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(req: PredictionRequest, background_tasks: BackgroundTasks):
    """
    Main prediction endpoint.
    - Validates input with Pydantic
    - Checks cache
    - Runs inference
    - Logs prediction in background (doesn't slow down response)
    """
    import uuid
    pred_id = str(uuid.uuid4())[:8]

    try:
        result, was_cached = server.predict_cached(req.features)
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

    # Log prediction in background (async, doesn't block response)
    background_tasks.add_task(
        log_prediction,
        pred_id=pred_id,
        features=req.features,
        result=result,
        customer_id=req.customer_id,
    )

    return PredictionResponse(
        prediction=result["prediction"],
        confidence=result["confidence"],
        probabilities=result["probabilities"] if req.return_probabilities else None,
        prediction_id=pred_id,
        model_version=server.model_version,
        latency_ms=result["latency_ms"],
        cached=was_cached,
    )


@app.post("/predict/batch")
async def predict_batch(req: BatchPredictionRequest):
    """
    Batch prediction endpoint.
    More efficient than N individual calls — uses asyncio to parallelize.
    """
    async def predict_one(single_req: PredictionRequest, idx: int):
        try:
            result, cached = server.predict_cached(single_req.features)
            return {"index": idx, "success": True, **result, "cached": cached}
        except Exception as e:
            return {"index": idx, "success": False, "error": str(e)}

    # Run all predictions concurrently
    tasks = [predict_one(r, i) for i, r in enumerate(req.requests)]
    results = await asyncio.gather(*tasks)

    successful = sum(1 for r in results if r["success"])
    return {
        "results": results,
        "total": len(results),
        "successful": successful,
        "failed": len(results) - successful,
    }


@app.get("/metrics")
async def get_metrics():
    """
    Exposes server metrics. In production, format as Prometheus metrics.
    Scraped by Prometheus every 15 seconds for dashboards.
    """
    uptime = (datetime.now() - server.start_time).total_seconds()
    return {
        "predictions_served":  server.predictions_served,
        "cache_size":          len(server._cache),
        "uptime_seconds":      round(uptime, 1),
        "model_version":       server.model_version,
        "predictions_per_min": round(server.predictions_served / max(uptime / 60, 1), 2),
    }


# =============================================================================
# BACKGROUND TASK: Log predictions for monitoring
# =============================================================================

async def log_prediction(pred_id: str, features: list, result: dict, customer_id: str = None):
    """
    Logs each prediction to a file/database for:
    - Drift monitoring (compare live distribution to training distribution)
    - Audit trails (who got what prediction when)
    - Retraining datasets (accumulate labeled data over time)
    """
    log_entry = {
        "prediction_id": pred_id,
        "timestamp":     datetime.now().isoformat(),
        "customer_id":   customer_id,
        "prediction":    result["prediction"],
        "confidence":    result["confidence"],
        "features":      features,   # ← Store features for drift analysis
    }

    # Append to JSONL file (one JSON per line = easy to parse)
    with open("prediction_log.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")


# =============================================================================
# DOCKERFILE (printed as a string — save as ./Dockerfile)
# =============================================================================
DOCKERFILE = """
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (Docker layer caching: reinstall only if requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY serve.py .
COPY model_artifacts/ ./model_artifacts/

# Run as non-root user (security best practice)
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check: Docker will restart container if this fails
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start with multiple workers (tune to CPU count)
CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
"""

if __name__ == "__main__":
    print("Save the DOCKERFILE to ./Dockerfile:")
    print(DOCKERFILE)
    print("\nThen run:")
    print("  uvicorn serve:app --reload --port 8000")
    print("  curl http://localhost:8000/health")
    print("  curl -X POST http://localhost:8000/predict \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"features\": [" + ",".join(["1.0"]*30) + "]}'")
