
Docker is a containerization platform that packages applications with all their dependencies into standardized units called containers. For AI engineers, Docker is essential because it ensures your ML/NLP models run consistently across different environments—from your laptop to production servers—solving the notorious "it works on my machine" problem.[](https://www.britannica.com/technology/artificial-intelligence)​

## Why Docker Matters for AI/ML Engineering

Docker solves critical challenges in ML deployment:[](https://www.kdnuggets.com/step-by-step-guide-to-deploying-ml-models-with-docker)​

**Consistency**: Your model and all dependencies are packaged together, eliminating environment mismatches.[](https://dev.to/docker/getting-started-with-docker-for-aiml-a-beginners-guide-4k6j)​

**Reproducibility**: Anyone can run your exact model configuration by pulling your Docker image.[](https://www.docker.com/blog/how-ikea-retail-standardizes-docker-images-for-efficient-machine-learning-model-deployment/)​

**Portability**: Deploy seamlessly to any cloud provider or on-premise infrastructure.[](https://www.docker.com/blog/how-ikea-retail-standardizes-docker-images-for-efficient-machine-learning-model-deployment/)​

**Isolation**: Each container runs independently without affecting other applications.[](https://docs.docker.com/get-started/docker-overview/)​

**Scalability**: Easily replicate containers to handle increased traffic.[](https://www.docker.com/blog/how-ikea-retail-standardizes-docker-images-for-efficient-machine-learning-model-deployment/)​

## Docker Architecture: How It Works

Docker uses a client-server architecture with three main components:[](https://www.nxp.com/docs/en/supporting-information/DOCKER-CONTAINER-FUNDAMENTALS.pdf)​

1. **Docker Daemon** (dockerd): The background service that manages containers, images, networks, and volumes[](https://docs.docker.com/get-started/docker-overview/)​
    
2. **Docker Client**: The command-line tool you use to interact with Docker[](https://docs.docker.com/get-started/docker-overview/)​
    
3. **Docker Registry** (Docker Hub): A repository for storing and distributing Docker images[](https://www.geeksforgeeks.org/devops/introduction-to-docker/)​
    

## Images vs Containers

Understanding the distinction is crucial:[](https://www.geeksforgeeks.org/devops/introduction-to-docker/)​

- **Docker Image**: A read-only template containing the application code, runtime, libraries, and dependencies. Think of it as a blueprint or class.[](https://mapattacker.github.io/ai-engineer/docker/)​
    
- **Docker Container**: A runnable instance of an image—the actual running application. Think of it as an object created from a class.[](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/)​
    

## Layers and Caching

Docker images are built in layers, which is key to understanding build optimization:[](https://docs.gitlab.com/ci/docker/docker_layer_caching/)​

text

`Base Image Layer (FROM python:3.9)     ↓ System Dependencies Layer (RUN apt-get install...)     ↓ Python Dependencies Layer (RUN pip install...)     ↓ Application Code Layer (COPY . /app)     ↓ Final Image`

Each instruction in a Dockerfile creates a new layer. Docker caches these layers, so unchanged layers don't need to be rebuilt. This is why you should copy `requirements.txt` and install dependencies before copying your application code—code changes won't invalidate the dependency cache.[](https://docs.docker.com/get-started/docker-concepts/building-images/using-the-build-cache/)​​

## Dockerfile: Building Your Container Blueprint

A Dockerfile is a text file with instructions for building a Docker image. Here's a comprehensive breakdown:[](https://docs.docker.com/reference/dockerfile/)​

## Essential Dockerfile Instructions

**FROM**: Specifies the base image—must be the first instruction:[](https://docs.docker.com/reference/dockerfile/)​

text

`FROM python:3.9-slim  # Use slim version for smaller image`

**WORKDIR**: Sets the working directory for subsequent instructions:[](https://docs.docker.com/reference/dockerfile/)​

text

`WORKDIR /app  # All commands execute from /app`

**COPY**: Copies files from your build context into the image:[](https://stackoverflow.com/questions/24958140/what-is-the-difference-between-the-copy-and-add-commands-in-a-dockerfile)​

text

`COPY requirements.txt .  # Copy requirements first for caching COPY . .  # Copy all application code`

**ADD**: Like COPY but can handle URLs and auto-extract tar archives:[](https://www.geeksforgeeks.org/devops/difference-between-the-copy-and-add-commands-in-a-dockerfile/)​

text

`ADD https://example.com/model.tar.gz /models/  # Download and extract`

**Best practice**: Use COPY unless you specifically need ADD's features.[](https://www.docker.com/blog/docker-best-practices-understanding-the-differences-between-add-and-copy-instructions-in-dockerfiles/)​

**RUN**: Executes commands during build time, creating new layers:[](https://docs.docker.com/reference/dockerfile/)​

text

`# Install dependencies RUN pip install --no-cache-dir -r requirements.txt # Chain commands to reduce layers RUN apt-get update && \     apt-get install -y curl && \    rm -rf /var/lib/apt/lists/*  # Clean up in same layer`

**ENV**: Sets environment variables that persist in the container:[](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/)​

text

`ENV PYTHONUNBUFFERED=1 \     MODEL_NAME=distilbert-base-uncased \    LOG_LEVEL=info`

**ARG**: Defines build-time variables that don't persist in the final image:[](https://docs.docker.com/reference/dockerfile/)​

text

`ARG PYTHON_VERSION=3.9 FROM python:${PYTHON_VERSION}  # Use ARG in FROM`

**EXPOSE**: Documents which ports the container uses (doesn't actually publish them):[](https://docs.docker.com/reference/dockerfile/)​

text

`EXPOSE 8000  # Application listens on port 8000`

**USER**: Sets the user for running the container (security best practice):[](https://docs.docker.com/engine/security/)​

text

`RUN useradd -m -u 1000 appuser USER appuser  # Run as non-root user`

**CMD**: Specifies the default command when container starts:[](https://docs.docker.com/reference/dockerfile/)​

text

`# Exec form (preferred for better signal handling) CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"] # Shell form CMD uvicorn app:app --host 0.0.0.0 --port 8000`

**ENTRYPOINT**: Configures the container as an executable:[](https://docs.docker.com/reference/dockerfile/)​

text

`ENTRYPOINT ["python", "app.py"] # CMD can provide default arguments to ENTRYPOINT CMD ["--port", "8000"]`

**HEALTHCHECK**: Defines a command to check container health:[](https://dev.to/ciscoemerge/building-secure-docker-images-for-production-best-practices-5d0f)​

text

`HEALTHCHECK --interval=30s --timeout=10s --retries=3 \     CMD curl -f http://localhost:8000/health || exit 1`

## Multi-Stage Builds: Production Optimization

Multi-stage builds dramatically reduce image size by separating build dependencies from runtime dependencies:[](https://docs.docker.com/get-started/docker-concepts/building-images/multi-stage-builds/)​

text

`# Stage 1: Builder (contains build tools) FROM python:3.9 AS builder WORKDIR /app COPY requirements.txt . RUN pip install --prefix=/install -r requirements.txt # Stage 2: Runtime (minimal, production-ready) FROM python:3.9-slim AS runtime WORKDIR /app # Copy only installed packages from builder stage COPY --from=builder /install /usr/local COPY app.py . CMD ["python", "app.py"]`

Benefits:[](https://labs.iximiuz.com/tutorials/docker-multi-stage-builds)​

- **Smaller images**: Final stage doesn't include build tools (gcc, make, etc.)
    
- **Security**: Fewer packages = smaller attack surface
    
- **Faster deployments**: Smaller images push/pull faster
    

## Docker Networking: Container Communication

Docker provides several network types:[](https://www.serveradminz.com/blog/docker-volumes-networking-compose-guide/)​

## Bridge Network (Default)

Containers on the same bridge network can communicate using container names:[](https://docs.docker.com/engine/network/)​

bash

`# Create custom bridge network docker network create my-network # Run containers on the network docker run -d --name app1 --network my-network myapp docker run -d --name app2 --network my-network myapp # app1 can reach app2 using the name "app2"`

## Host Network

Container uses the host's network directly—no isolation:[](https://techblog.flaviusdinu.com/docker-nautical-leader-3-docker-networks-and-volumes-32410557f7af)​

bash

`docker run --network host myapp`

## None Network

Complete network isolation:[](https://docs.docker.com/engine/network/)​

bash

`docker run --network none myapp`

## Docker Volumes: Data Persistence

Containers are ephemeral—data inside them is lost when they're removed. Volumes persist data:[](https://docs.docker.com/get-started/workshop/08_using_compose/)​

## Named Volumes (Recommended)

bash

`# Create volume docker volume create model-cache # Use in container docker run -v model-cache:/app/cache myapp # Inspect volume docker volume inspect model-cache`

## Bind Mounts

Mount host directories directly:[](https://www.serveradminz.com/blog/docker-volumes-networking-compose-guide/)​

bash

`# Mount current directory to /app in container docker run -v $(pwd):/app myapp`

## Volume Best Practices

- Use named volumes for production data persistence[](https://techblog.flaviusdinu.com/docker-nautical-leader-3-docker-networks-and-volumes-32410557f7af)​
    
- Use bind mounts for development (hot reload)[](https://www.serveradminz.com/blog/docker-volumes-networking-compose-guide/)​
    
- Never store sensitive data in container layers[](https://docs.docker.com/get-started/workshop/08_using_compose/)​
    

## Docker Compose: Multi-Container Applications

Docker Compose manages multi-container applications with a single YAML file:[](https://www.geeksforgeeks.org/devops/docker-compose-yaml-explained-a-deep-dive-into-configuration/)​

text

`version: '3.8' services:   web:    build: .    ports:      - "8000:8000"    environment:      - DB_HOST=postgres    volumes:      - ./:/app    networks:      - app-network    depends_on:      - postgres   postgres:    image: postgres:14    environment:      - POSTGRES_PASSWORD=secret    volumes:      - db-data:/var/lib/postgresql/data    networks:      - app-network volumes:   db-data: networks:   app-network:    driver: bridge`

## Essential Compose Commands

bash

`# Start services in background docker-compose up -d # Build and start docker-compose up -d --build # View logs docker-compose logs -f # Stop and remove containers docker-compose down # Stop and remove volumes docker-compose down -v # Execute command in service docker-compose exec web bash`

## Docker Commands Reference

## Deploying ML/NLP Models with Docker and FastAPI

Here's a complete, production-ready workflow for deploying NLP models:[](https://www.foundingminds.ai/blogs/ml-deployment-using-fastapi-docker)​

## Build and Run Workflow

bash

`# 1. Build the image docker build -t nlp-api:v1 -f Dockerfile.basic . # 2. Run the container docker run -d \     -p 8000:8000 \    --name nlp-api \    -e MODEL_NAME=distilbert-base-uncased \    -v model-cache:/app/cache \    nlp-api:v1 # 3. Test the API curl http://localhost:8000/health curl -X POST http://localhost:8000/predict \     -H "Content-Type: application/json" \    -d '{"text": "This is amazing!"}' # 4. View logs docker logs -f nlp-api # 5. Access interactive docs # Open browser: http://localhost:8000/docs`

## Using Docker Compose for Development

bash

`# Start development environment with hot reload docker-compose -f docker-compose.dev.yml up -d # Make code changes (they reload automatically) # View logs docker-compose logs -f # Stop when done docker-compose down`

## Environment Variables and Secrets

## Using .env Files

Load environment variables in docker-compose:[](https://forums.docker.com/t/understanding-security-implications-of-secrets-vs-env-vars-in-docker-compose/145903)​

text

`services:   web:    env_file:      - .env`

## Docker Secrets (Swarm Mode)

For production secrets, use Docker secrets:[](https://stackoverflow.com/questions/52492359/docker-secrets-passing-as-environment-variable)​

text

`# In Dockerfile RUN --mount=type=secret,id=api_key \     API_KEY=$(cat /run/secrets/api_key) && \    some-command --key $API_KEY`

bash

`# Build with secret docker buildx build --secret id=api_key,src=./api_key.txt .`

**Security best practice**: Never put secrets in Dockerfiles or images. Use runtime injection via environment variables or Docker secrets.[](https://bell-sw.com/blog/docker-image-security-best-practices-for-production/)​

## Docker Registry and Docker Hub

## Pushing Images to Docker Hub

bash

`# 1. Login to Docker Hub docker login # 2. Tag your image with your username docker tag nlp-api:v1 yourusername/nlp-api:v1 # 3. Push to Docker Hub docker push yourusername/nlp-api:v1 # 4. Pull from anywhere docker pull yourusername/nlp-api:v1`

## Private Registry

Set up a local registry:[](https://www.docker.com/blog/how-to-use-your-own-registry-2/)​

bash

`# Run registry container docker run -d -p 5000:5000 --name registry registry:2 # Tag for local registry docker tag nlp-api:v1 localhost:5000/nlp-api:v1 # Push to local registry docker push localhost:5000/nlp-api:v1`

## Debugging and Troubleshooting

## Essential Debugging Commands

bash

`# View container logs docker logs -f <container-name> docker logs --tail 100 <container-name>  # Last 100 lines # Execute commands in running container docker exec -it <container-name> bash # Inspect container details (JSON output) docker inspect <container-name> # View running processes docker top <container-name> # Monitor resource usage in real-time docker stats <container-name> # Check container health docker ps  # Shows health status`

## Common Issues and Solutions

**Container won't start**:[](https://dev.to/yash_sonawane25/docker-series-episode-25-docker-troubleshooting-debugging-common-issues-fixes-3i8i)​

bash

`# Check logs for errors docker logs <container-name> # Inspect configuration docker inspect <container-name> # Run interactively to debug docker run -it --rm <image> /bin/bash`

**Port already in use**:[](https://dev.to/yash_sonawane25/docker-series-episode-25-docker-troubleshooting-debugging-common-issues-fixes-3i8i)​

bash

`# Change host port mapping docker run -p 8001:8000 myapp  # Use 8001 instead of 8000`

**Permission errors**:[](https://techbloomeracademy.com/docs/Docker/17-troubleshooting-common-docker-issues/lesson/)​

bash

`# Enter as root to fix permissions docker exec -u root -it <container-name> bash chown -R appuser:appuser /app`

**Out of disk space**:[](https://dev.to/yash_sonawane25/docker-series-episode-25-docker-troubleshooting-debugging-common-issues-fixes-3i8i)​

bash

`# Remove unused data docker system prune -a --volumes # Check disk usage docker system df`

**Network connectivity issues**:[](https://lumigo.io/container-monitoring/docker-debugging-common-scenarios-and-7-practical-tips/)​

bash

`# Check network configuration docker network inspect <network-name> # Test connectivity between containers docker exec <container1> ping <container2>`

## Best Practices for Production

## 1. Image Optimization

**Use slim/alpine base images**:[](https://www.ulam.io/blog/mastering-docker-container-optimization-and-security-advanced-techniques-for-production-environments)​

text

`FROM python:3.9-slim  # ~120MB instead of ~900MB`

**Multi-stage builds**:[](https://docs.docker.com/build/building/multi-stage/)​

- Separate build and runtime environments
    
- Reduces final image size by 50-90%
    

**Minimize layers**:[](https://mapattacker.github.io/ai-engineer/docker/)​

text

`# Bad: Multiple RUN commands RUN apt-get update RUN apt-get install -y curl RUN rm -rf /var/lib/apt/lists/* # Good: Single RUN with cleanup RUN apt-get update && \     apt-get install -y curl && \    rm -rf /var/lib/apt/lists/*`

**Use .dockerignore**:​  
Exclude unnecessary files from build context to speed up builds and reduce image size.

## 2. Security

**Run as non-root user**:[](https://www.tigera.io/learn/guides/container-security-best-practices/docker-security/)​

text

`RUN useradd -m appuser USER appuser`

**Don't store secrets in images**:[](https://docs.docker.com/engine/security/)​

- Use environment variables at runtime
    
- Use Docker secrets for production
    
- Never commit .env files to Git
    

**Scan images for vulnerabilities**:[](https://bell-sw.com/blog/docker-image-security-best-practices-for-production/)​

bash

`docker scan myimage:v1`

**Use specific image tags**:[](https://docs.docker.com/engine/security/)​

text

`FROM python:3.9.18-slim  # Not :latest`

**Keep base images updated**:[](https://bell-sw.com/blog/docker-image-security-best-practices-for-production/)​  
Regularly rebuild images with updated base images to get security patches.

## 3. Resource Management

**Set resource limits**:

text

`# In docker-compose.yml services:   web:    deploy:      resources:        limits:          cpus: '2.0'          memory: 4G        reservations:          cpus: '1.0'          memory: 2G`

Or with docker run:

bash

`docker run --cpus="2.0" --memory="4g" myapp`

## 4. Monitoring and Health Checks

**Implement health checks**:[](https://dev.to/ciscoemerge/building-secure-docker-images-for-production-best-practices-5d0f)​

text

`HEALTHCHECK --interval=30s --timeout=10s --retries=3 \     CMD curl -f http://localhost:8000/health || exit 1`

**Use restart policies**:[](https://spacelift.io/blog/docker-commands-cheat-sheet)​

bash

`docker run --restart unless-stopped myapp`

## 5. Logging

**Configure proper logging**:[](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Inspecting-a-Container)​

bash

`# View logs with timestamps docker logs -t <container-name> # Follow logs docker logs -f <container-name> # Use logging driver docker run --log-driver json-file \     --log-opt max-size=10m \    --log-opt max-file=3 \    myapp`

## Complete Practical Example

## Advanced Topics

## Build Cache Optimization

Docker caches layers to speed up builds:[](https://developer.harness.io/docs/continuous-integration/use-ci/caching-ci-data/docker-layer-caching)​

1. **Order matters**: Put frequently changing instructions last
    
2. **Copy dependencies first**: `COPY requirements.txt` before `COPY . .`
    
3. **Use cache mounts**:
    

text

`RUN --mount=type=cache,target=/root/.cache/pip \     pip install -r requirements.txt ``` ### Docker Contexts Switch between different Docker environments[72]: ``````bash # Create context for remote server docker context create remote --docker "host=ssh://user@server" # Use context docker context use remote # List contexts docker context ls ``` ### Container Orchestration For production at scale, use orchestration platforms:[51][5] - **Kubernetes**: Industry standard for container orchestration - **Docker Swarm**: Simpler alternative built into Docker - **Cloud services**: AWS ECS, Azure Container Instances, Google Cloud Run ## Key Takeaways for AI Engineers 1. **Docker ensures consistency**: Your model runs the same everywhere—local, staging, production[2][3][5] 2. **Layer caching matters**: Structure Dockerfiles to maximize cache hits[12][10][11] 3. **Multi-stage builds are essential**: Reduce image size and improve security[21][22][23] 4. **Security is paramount**: Run as non-root, never embed secrets, scan for vulnerabilities[19][18][39] 5. **Docker Compose simplifies development**: Manage multi-container apps easily[31][30][29] 6. **Volumes persist data**: Use them for model caches and databases[27][29][25] 7. **Networking enables communication**: Connect containers with custom networks[28][26][27] 8. **Health checks ensure reliability**: Monitor container health automatically[20][13] Docker is the foundation of modern ML deployment. Master these concepts, and you'll be able to deploy your AI models confidently to any environment. The examples provided give you production-ready templates—adapt them to your specific NLP/ML projects and you'll have robust, scalable deployments. Remember: the goal isn't just to containerize your model, but to create reproducible, scalable, and maintainable AI systems that work reliably in production. Docker is your tool to achieve this.`

| Category             | Command                   | Description                                         | Example                                            |
| -------------------- | ------------------------- | --------------------------------------------------- | -------------------------------------------------- |
| Container Management | docker run                | Create and start a container from an image          | docker run -d -p 8000:8000 --name myapp python:3.9 |
| Container Management | docker start              | Start one or more stopped containers                | docker start myapp                                 |
| Container Management | docker stop               | Stop one or more running containers                 | docker stop myapp                                  |
| Container Management | docker restart            | Restart one or more containers                      | docker restart myapp                               |
| Container Management | docker pause              | Pause all processes within one or more containers   | docker pause myapp                                 |
| Container Management | docker unpause            | Unpause all processes within one or more containers | docker unpause myapp                               |
| Container Management | docker rm                 | Remove one or more containers                       | docker rm myapp                                    |
| Container Management | docker ps                 | List running containers                             | docker ps -a (shows all including stopped)         |
| Container Management | docker kill               | Kill one or more running containers                 | docker kill myapp                                  |
| Image Management     | docker build              | Build an image from a Dockerfile                    | docker build -t myimage:v1 .                       |
| Image Management     | docker pull               | Pull an image from a registry                       | docker pull python:3.9                             |
| Image Management     | docker push               | Push an image to a registry                         | docker push myusername/myimage:v1                  |
| Image Management     | docker images             | List images                                         | docker images                                      |
| Image Management     | docker rmi                | Remove one or more images                           | docker rmi myimage:v1                              |
| Image Management     | docker tag                | Create a tag for an image                           | docker tag myimage:v1 myimage:latest               |
| Image Management     | docker save               | Save image to tar archive                           | docker save -o myimage.tar myimage:v1              |
| Image Management     | docker load               | Load image from tar archive                         | docker load -i myimage.tar                         |
| Container Inspection | docker logs               | Fetch logs of a container                           | docker logs -f myapp (follow logs)                 |
| Container Inspection | docker inspect            | Return low-level information on Docker objects      | docker inspect myapp                               |
| Container Inspection | docker top                | Display running processes of a container            | docker top myapp                                   |
| Container Inspection | docker stats              | Display live stream of resource usage statistics    | docker stats myapp                                 |
| Container Inspection | docker exec               | Run a command in a running container                | docker exec -it myapp /bin/bash                    |
| Container Inspection | docker attach             | Attach to a running container's stdin/stdout        | docker attach myapp                                |
| Container Inspection | docker cp                 | Copy files between container and host               | docker cp myapp:/app/file.txt ./                   |
| Network Management   | docker network create     | Create a network                                    | docker network create my-network                   |
| Network Management   | docker network ls         | List networks                                       | docker network ls                                  |
| Network Management   | docker network inspect    | Display detailed information on networks            | docker network inspect my-network                  |
| Network Management   | docker network connect    | Connect a container to a network                    | docker network connect my-network myapp            |
| Network Management   | docker network disconnect | Disconnect a container from a network               | docker network disconnect my-network myapp         |
| Network Management   | docker network rm         | Remove one or more networks                         | docker network rm my-network                       |
| Volume Management    | docker volume create      | Create a volume                                     | docker volume create mydata                        |
| Volume Management    | docker volume ls          | List volumes                                        | docker volume ls                                   |
| Volume Management    | docker volume inspect     | Display detailed information on volumes             | docker volume inspect mydata                       |
| Volume Management    | docker volume rm          | Remove one or more volumes                          | docker volume rm mydata                            |
| Volume Management    | docker volume prune       | Remove all unused local volumes                     | docker volume prune                                |
| Docker Compose       | docker-compose up         | Create and start containers                         | docker-compose up -d (detached mode)               |
| Docker Compose       | docker-compose down       | Stop and remove containers, networks                | docker-compose down                                |
| Docker Compose       | docker-compose ps         | List containers                                     | docker-compose ps                                  |
| Docker Compose       | docker-compose logs       | View output from containers                         | docker-compose logs -f                             |
| Docker Compose       | docker-compose build      | Build or rebuild services                           | docker-compose build                               |
| Docker Compose       | docker-compose restart    | Restart services                                    | docker-compose restart                             |
| Docker Compose       | docker-compose exec       | Execute a command in a running container            | docker-compose exec web bash                       |
| System Management    | docker system prune       | Remove unused data                                  | docker system prune -a (remove all)                |
| System Management    | docker system df          | Show docker disk usage                              | docker system df                                   |
| System Management    | docker info               | Display system-wide information                     | docker info                                        |
| System Management    | docker version            | Show Docker version information                     | docker version                                     |
| Registry & Hub       | docker login              | Log in to a Docker registry                         | docker login                                       |
| Registry & Hub       | docker logout             | Log out from a Docker registry                      | docker logout                                      |
| Registry & Hub       | docker search             | Search Docker Hub for images                        | docker search python                               |


`""" FastAPI Application for NLP Model Serving This is a complete, production-ready example for deploying an NLP model Author: AI Engineering Guide """ from fastapi import FastAPI, HTTPException from pydantic import BaseModel from typing import List, Dict, Optional import logging from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer import torch from functools import lru_cache # ============================================ # LOGGING CONFIGURATION # ============================================ # Set up logging to track requests and errors logging.basicConfig( level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' ) logger = logging.getLogger(__name__) # ============================================ # FASTAPI APP INITIALIZATION # ============================================ # Create the FastAPI application instance app = FastAPI( title="NLP Model API", description="Production-ready API for NLP text classification", version="1.0.0" ) # ============================================ # DATA MODELS (Pydantic Schemas) # ============================================ # These define the structure of input/output data class TextInput(BaseModel): """Input schema for text classification""" text: str class Config: # Example for API documentation schema_extra = { "example": { "text": "This movie was absolutely amazing! I loved every minute of it." } } class PredictionOutput(BaseModel): """Output schema for predictions""" label: str score: float text: str class BatchTextInput(BaseModel): """Input schema for batch predictions""" texts: List[str] class HealthResponse(BaseModel): """Health check response schema""" status: str model_loaded: bool # ============================================ # MODEL LOADING (with caching) # ============================================ # Use lru_cache to load model only once at startup @lru_cache() def load_model(): """ Load the NLP model and tokenizer This function is cached, so it only runs once Returns: tuple: (model, tokenizer) """ logger.info("Loading NLP model...") try: # Load a pre-trained sentiment analysis model model_name = "distilbert-base-uncased-finetuned-sst-2-english" # Load tokenizer and model tokenizer = AutoTokenizer.from_pretrained(model_name) model = AutoModelForSequenceClassification.from_pretrained(model_name) # Create pipeline for easy inference classifier = pipeline( "sentiment-analysis", model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1 # Use GPU if available ) logger.info("Model loaded successfully!") return classifier except Exception as e: logger.error(f"Error loading model: {str(e)}") raise # ============================================ # STARTUP EVENT # ============================================ # This runs when the application starts @app.on_event("startup") async def startup_event(): """ Initialize the model when the application starts This ensures the model is ready before accepting requests """ logger.info("Starting up the API...") try: # Load the model during startup load_model() logger.info("API is ready to serve requests!") except Exception as e: logger.error(f"Failed to start API: {str(e)}") raise # ============================================ # API ENDPOINTS # ============================================ @app.get("/", response_model=Dict[str, str]) async def root(): """ Root endpoint - provides basic API information """ return { "message": "Welcome to NLP Model API", "docs": "/docs", "health": "/health" } @app.get("/health", response_model=HealthResponse) async def health_check(): """ Health check endpoint - verifies API and model status This is useful for container orchestration systems """ try: classifier = load_model() return { "status": "healthy", "model_loaded": classifier is not None } except Exception as e: logger.error(f"Health check failed: {str(e)}") raise HTTPException(status_code=503, detail="Service unavailable") @app.post("/predict", response_model=PredictionOutput) async def predict(input_data: TextInput): """ Single text prediction endpoint Args: input_data: TextInput object containing the text to classify Returns: PredictionOutput: Contains label, confidence score, and original text """ try: logger.info(f"Received prediction request for text: {input_data.text[:50]}...") # Load the model classifier = load_model() # Make prediction result = classifier(input_data.text)[0] # Log the result logger.info(f"Prediction: {result['label']} (score: {result['score']:.4f})") return PredictionOutput( label=result['label'], score=result['score'], text=input_data.text ) except Exception as e: logger.error(f"Prediction error: {str(e)}") raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}") @app.post("/predict/batch", response_model=List[PredictionOutput]) async def predict_batch(input_data: BatchTextInput): """ Batch prediction endpoint for multiple texts More efficient for processing multiple texts at once Args: input_data: BatchTextInput containing list of texts Returns: List[PredictionOutput]: List of predictions for each text """ try: logger.info(f"Received batch prediction request for {len(input_data.texts)} texts") # Load the model classifier = load_model() # Make batch predictions results = classifier(input_data.texts) # Format results predictions = [ PredictionOutput( label=result['label'], score=result['score'], text=text ) for result, text in zip(results, input_data.texts) ] logger.info(f"Batch prediction completed for {len(predictions)} texts") return predictions except Exception as e: logger.error(f"Batch prediction error: {str(e)}") raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}") # ============================================ # MAIN ENTRY POINT # ============================================ # This allows running the app directly with Python if __name__ == "__main__": import uvicorn # Run the application # host="0.0.0.0" makes it accessible from outside the container # port=8000 is the standard port for this app uvicorn.run( app, host="0.0.0.0", port=8000, log_level="info" )`
