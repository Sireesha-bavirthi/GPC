# AWS Deployment Guide — APO Framework
## Autonomous Privacy Observability (APO) v2

---

## 🏗️ High-Level Architecture

```
Developer pushes code to GitHub
          │
          ▼
  GitHub Actions (CI/CD Pipeline)
          │
          ├── Builds Docker Image
          │
          ├── Pushes to AWS ECR (Container Registry)
          │
          └── ECS deploy latest image
                    │
                    ▼
           AWS ECS Fargate (Serverless)
              runs the Python backend
            
```

---

## Step 1: CI/CD Pipeline (GitHub Actions)

### What is a CI/CD Pipeline?
A CI/CD (Continuous Integration / Continuous Deployment) pipeline is an **automated robot** that runs whenever a developer pushes new code to GitHub. It automatically runs tests, builds the application, and deploys it to the cloud — without any manual steps.

### Our Pipeline: `.github/workflows/docker-publish.yml`
Every time code is pushed to the `main` branch, the pipeline automatically:

1. **Checks out the latest code** from GitHub
2. **Logs into AWS** using stored secret credentials
3. **Builds a Docker Image** of the entire application
4. **Pushes the image to AWS ECR** (the cloud container registry)
5. **ECS to deploy** with the new image

```yaml
# Trigger: runs automatically on every push to main branch
on:
  push:
    branches: [main]
  workflow_dispatch:  # also allows manual trigger from GitHub UI
```

---

## Step 2: Docker Image

### What is a Docker Image?
A Docker Image is like a **complete, self-contained snapshot of your application** — similar to a USB drive that contains the operating system, all libraries, the Python environment, the Playwright browser (Chromium), and all your Python scripts pre-installed and ready to run.

Think of it like this:
> Without Docker: "It works on my laptop but not on the server!"  
> With Docker: "It works everywhere, because the same exact environment follows the code."

### What our Docker Image contains:
- **Python 3.13** runtime
- **All Python dependencies** (`requirements.txt`) — FastAPI, Playwright, Anthropic SDK, etc.
- **Playwright Chromium browser** — the headless browser used for web crawling
- **All application code** — `backend.py`, `agents/`, `core/` folders

### What the Docker Image does when it runs:
```dockerfile
# Start the FastAPI web server that exposes the API endpoints
CMD ["python", "backend.py"]
```
When AWS runs this image, it starts a FastAPI web server on **port 8000** that accepts scan requests from the frontend.

### Docker Image Tags
Each image is tagged twice for tracking:
- `mhk-apo:latest` — always the most recent version
- `mhk-apo:<git-commit-hash>` — specific version for rollback

---

## Step 3: AWS ECR (Elastic Container Registry)

### What is ECR?
AWS ECR is **Amazon's private Docker Hub** — a secure cloud storage specifically for Docker Images. Only authorized AWS accounts can push or pull images from it.

```
Repository: 700294801275.dkr.ecr.us-east-1.amazonaws.com/mhk-apo
```

### Why not just use Docker Hub?
- ECR is **private** — no one outside your AWS account can access your images
- ECR is **faster** — images are stored in the same data center as your ECS cluster, so deployment is instant
- ECR **integrates natively** with ECS — no credentials needed between services

### How the CI/CD pipeline pushes to ECR:
```bash
# 1. Login to ECR
aws ecr get-login-password | docker login --username AWS ...

# 2. Build the image
docker build -t mhk-apo:latest .

# 3. Push to ECR
docker push 700294801275.dkr.ecr.us-east-1.amazonaws.com/mhk-apo:latest
```

---

## Step 4: AWS ECS Fargate (Running the Application)

### What is ECS Fargate?
ECS (Elastic Container Service) Fargate is **AWS's serverless container platform**. You give it a Docker Image and it handles everything else — finding physical servers, allocating memory, networking, restarts. You pay only for the seconds the container is actually running.

> Unlike EKS (Kubernetes), Fargate needs **zero cluster management**. No EC2 instances to configure, no Kubernetes YAML to write.

### The 3 ECS Concepts:

#### 1. Task Definition (The Blueprint)
A Task Definition is the **recipe or blueprint** of how to run your container. It defines:

| Setting | Our Value |
|---------|-----------|
| Docker Image | `700294801275.dkr.ecr.us-east-1.amazonaws.com/mhk-apo:latest` |
| CPU | 2 vCPU |
| Memory | 4 GB (needed for Playwright browser) |
| Environment Variables | API keys, Supabase URL, etc. |

Think of it like a job posting: *"We need 2 CPUs and 4GB RAM, running this exact Docker image."*

#### 2. ECS Cluster (The Pool of Servers)
The Cluster is the **logical group** where your containers run. Our cluster is named `siri_cluster`.

With Fargate, the cluster is just an empty container — AWS automatically provides the physical servers in the background whenever a Task needs to run.

#### 3. Task (The Running Instance)
When a Task Definition is executed, ECS creates a **Task** — a live, running container. Each Task:
- Downloads the Docker Image from ECR
- Starts the Python FastAPI server on port 8000
- Gets a **public IP address** for external access
- Runs until stopped (or until the script finishes for one-off jobs)

### ECS Setup Order:
```
1. Create ECS Cluster (siri_cluster)
      ↓
2. Create Task Definition (apo_new)
      ↓ 
3. Run Task → ECS pulls image from ECR → Container starts → Gets public IP
      ↓
4. Access API at http://<PUBLIC_IP>:8000/docs
```

---



### Authentication
All endpoints require a Bearer Token. Add this header to every request:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc3MjQ1ODMxMX0.4R6BiFuxZvDbzZNEwr55C6FZ04pwIF920XvYkLCN3Qo
```

### Step 1: Start a Scan
**Endpoint:** `POST /api/scan`

**Request Body:**
```json
{
  "url": "https://www.livanova.com/en-us",
  "framework": "CCPA",
  "crawl_depth": 2,
  "use_llm": true,
  "claude_key": "sk-ant-your-actual-key-here",
  "openai_key": ""
}
```

**Response:**
```json
{
  "scan_id": "a3b4c5d6"
}
```

### Step 2: Stream Live Logs
**Endpoint:** `GET /api/stream/{scan_id}`  
Watch the 3 agents running in real-time as Server-Sent Events.

### Step 3: Get Final Results
**Endpoint:** `GET /api/results/{scan_id}`  
Returns the full evidence report with violations, severity, and potential fines.

### Step 4: Download Report
**Endpoint:** `GET /api/download/evidence_report.json`  
Downloads the JSON compliance report.

---

## 💰 Cost Summary

| Service | Cost |
|---------|------|
| AWS ECR | ~$0.10/GB storage |
| AWS ECS Fargate | Pay per second of scan time |

---

