# AWS EKS + Step Functions Orchestration Guide

To handle **massive concurrency** (multiple users running scans at the exact same time) and **automated monthly scheduling** (emailing reports automatically), we are moving away from a single server to an **AWS Serverless Orchestration** model using EKS.

## Architecture Overview

1. **Frontend (React)**: Hosted statically on AWS S3 + CloudFront (infinite scale, nearly free).
2. **API Gateway**: Receives a scan request from the frontend and triggers the Step Function.
3. **EventBridge (Cron scheduling)**: Runs on the 1st of every month, pulling website URLs from your database and triggering the Step Function for each URL automatically.
4. **AWS Step Functions (The Brain)**: Orchestrates the 3-Tier APO workflow.
5. **AWS EKS (The Muscle)**: Runs massive fleets of Kubernetes Pods on demand. When Step Functions needs to run a Playwright web crawler, it tells EKS to spin up a temporary Docker Pod, run the Python code, save the JSON to S3, and immediately terminate the Pod.

---

## Phase 1: Containerizing the Code
EKS requires your code to be packaged as a Docker container. 

1. We have provided a `Dockerfile` in the root of the repository.
2. Build and push this Docker image to **AWS ECR (Elastic Container Registry)**.

```bash
# Authenticate Docker to AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build the APO Docker Image
docker build -t apo-agents .

# Tag and Push to ECR
docker tag apo-agents:latest YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/apo-agents:latest
docker push YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/apo-agents:latest
```

---

## Phase 2: Create the EKS Cluster
You need a Kubernetes cluster to run the massive amount of headless Playwright browsers.

```bash
eksctl create cluster \
  --name apo-cluster \
  --region us-east-1 \
  --nodegroup-name crawler-nodes \
  --node-type r5.large \
  --nodes-min 1 \
  --nodes-max 100 \
  --managed
```
*(Note: We use `r5.large` because Chromium uses a lot of memory. The `--nodes-max 100` allows the cluster to automatically add physical servers if 500 users trigger scans simultaneously, preventing crashes).*

---

## Phase 3: The AWS Step Function Workflow

AWS Step Functions define state machines using Amazon States Language (JSON). 
When a user requests a scan for `https://example.com`, the Step Function executes the following exact workflow:

### Step 1: Discovery Job (EKS RunTask)
Step Functions tells EKS to launch a Pod using your Docker image.
It overrides the container's command to run: `python agents/tier1_discovery.py https://example.com`
The container explores the website, saves `interaction_graph.json` to an S3 bucket, and deletes itself.

### Step 2: Interaction Job (EKS RunTask)
Once Step 1 succeeds, Step Functions launches a *new* Pod.
Command: `python agents/tier2_interaction.py s3://bucket/interaction_graph.json`
It opens Playwright, simulates GPC-ON/OFF sessions, saves network traffic to S3, and deletes itself.

### Step 3: Observability & Emailing (AWS Lambda OR EKS)
Command: `python agents/tier3_observability.py s3://bucket/traffic...`
The agent analyzes the data using LLMs, generates the final compliance report, and uses **Amazon SES (Simple Email Service)** natively to email the PDF to the user!

---

## Phase 4: EventBridge Monthly Scheduling

To fulfill your requirement of running this every month for all clients:

1. Open **AWS EventBridge** in the AWS Console.
2. Create a new **Rule** -> Schedule -> `cron(0 0 1 * ? *)` (Run on the 1st of every month).
3. Set the **Target** as your Step Function state machine.
4. Provide the list of client URLs as the JSON Input payload. 

EventBridge will trigger the Step Function for every single client at once. EKS will automatically scale up 50+ background servers to handle the load, run all the Playwright browser sessions simultaneously, email everyone their compliance report, and immediately scale back down to 1 server so you don't pay for idle time!
