# AWS EKS Deployment & CI/CD Guide

This guide explains how to orchestrate the entire APO v2 project on AWS Elastic Kubernetes Service (EKS) using a CI/CD pipeline via GitHub Actions and Docker Hub.

---

## 1. CI/CD Pipeline Setup (GitHub Actions)

We have created a GitHub Actions workflow `.github/workflows/docker-publish.yml` that automatically builds your Docker images and pushes them to Docker Hub whenever you push code to GitHub.

### Prerequisites in GitHub
Before pushing your code, you need to add your Docker Hub credentials into GitHub so the pipeline has permission to push the images.

1. Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions**.
2. Click **New repository secret** and add the following two secrets:
   - `DOCKER_USERNAME`: Your Docker Hub username.
   - `DOCKER_PASSWORD`: Your Docker Hub password (or Access Token).

### Triggering the Pipeline
1. Commit all your latest code, including the new `Dockerfile` and `apo/Dockerfile`.
2. Push your code to the `main` or `apo-v2` branch.
3. Go to the **Actions** tab in GitHub to watch the pipeline build the backend and frontend Docker images and upload them to Docker Hub.

---

## 2. Orchestrating on AWS EKS

Once your Docker images are hosted on Docker Hub (e.g., `your-username/apo-backend:latest` and `your-username/apo-frontend:latest`), you can deploy them to AWS EKS.

### 2.1 Prerequisites
You need the following tools installed on your local machine:
- **AWS CLI**: To securely communicate with AWS.
- **eksctl**: The official CLI tool for Amazon EKS.
- **kubectl**: For controlling Kubernetes clusters.

Ensure you have configured your AWS CLI with valid credentials using `aws configure`.

### 2.2 Create the EKS Cluster
Run the following command to provision a managed EKS cluster. This process takes about 15-20 minutes on AWS.

```bash
eksctl create cluster \
  --name apo-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 3 \
  --managed
```

Once complete, `eksctl` will automatically configure your local `kubectl` context to connect to your new cluster.

### 2.3 Kubernetes Deployment Manifests

To deploy the application, you need to explicitly tell Kubernetes to spin up your containers and expose them to the internet. Create a file named `k8s-deployment.yaml`.

*Make sure to replace `YOUR_DOCKER_USERNAME` with your actual Docker Hub username.*

```yaml
---
# BACKEND DEPLOYMENT & SERVICE
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apo-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: apo-backend
  template:
    metadata:
      labels:
        app: apo-backend
    spec:
      containers:
      - name: apo-backend
        image: YOUR_DOCKER_USERNAME/apo-backend:latest
        ports:
        - containerPort: 8000
        env:
        # Example environment variables required by your backend
        - name: SUPABASE_URL
          value: "your_supabase_url"
        - name: SUPABASE_KEY
          value: "your_supabase_key"
---
apiVersion: v1
kind: Service
metadata:
  name: apo-backend-service
spec:
  type: LoadBalancer
  selector:
    app: apo-backend
  ports:
    - protocol: TCP
      port: 8000
      targetPort: 8000

---
# FRONTEND DEPLOYMENT & SERVICE
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apo-frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: apo-frontend
  template:
    metadata:
      labels:
        app: apo-frontend
    spec:
      containers:
      - name: apo-frontend
        image: YOUR_DOCKER_USERNAME/apo-frontend:latest
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: apo-frontend-service
spec:
  type: LoadBalancer
  selector:
    app: apo-frontend
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
```

> **Note on Frontend/Backend Connection**: Because you've pushed this to a LoadBalancer, your frontend application React code (which runs in the user's browser) must know the external load balancer IP of the backend. You may need to update `BASE_URL` in your frontend `api.ts` file or handle it dynamically before building your frontend image.

### 2.4 Apply Deployments to EKS

From your terminal, run:

```bash
kubectl apply -f k8s-deployment.yaml
```

Kubernetes will now pull your images from Docker Hub, start the containers, and create AWS Load Balancers to serve traffic.

### 2.5 Accessing Your App

You can check the status of your deployments and get the public URLs (LoadBalancer IPs/DNS) with the following commands:

```bash
# Check if pods are running
kubectl get pods

# Get the external URLs created by AWS LoadBalancers
kubectl get services
```

Look for the `EXTERNAL-IP` of the `apo-frontend-service` and `apo-backend-service`. Note that AWS classic load balancers may take 2-3 minutes to provision DNS before they respond in your browser.

- **Frontend**: Access it via `http://<FRONTEND_EXTERNAL_IP>`
- **Backend API**: Accessible via `http://<BACKEND_EXTERNAL_IP>:8000`

### 2.6 Cleaning Up Resources

EKS clusters incur hourly charges. If you no longer need the cluster, you must cleanly delete it to avoid AWS bills:

```bash
eksctl delete cluster --name apo-cluster --region us-east-1
```
