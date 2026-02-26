# AWS EC2 Continuous Deployment Guide (No Docker)

This guide explains how to set up a bare-metal Ubuntu server on AWS EC2, clone your repository, and set up automatic deployments using GitHub Actions.

Whenever you push code to GitHub, GitHub will securely SSH into your AWS server, run `git pull`, install any new dependencies, and restart your services automatically!

---

## 1. Provision an AWS EC2 Instance

1. Log into your AWS Console and go to **EC2**.
2. Click **Launch Instance**.
3. **Name**: `apo-server`
4. **OS**: Choose **Ubuntu 24.04 LTS** (or 22.04 LTS).
5. **Instance Type**: `t3.medium` or `t3.large` (Playwright and React building require at least 2GB-4GB of RAM).
6. **Key Pair**: Create a new key pair (e.g., `apo-key`). **Download the `.pem` file and keep it safe!** You will need this for GitHub Actions.
7. **Network Settings**: Ensure you check:
   - Allow SSH traffic from Anywhere
   - Allow HTTP traffic from the internet
   - Allow HTTPS traffic from the internet
8. **Storage**: At least 20 GB.
9. Click **Launch**.

---

## 2. Initial Server Setup

SSH into your new server using your terminal and the `.pem` key you downloaded:
```bash
ssh -i /path/to/apo-key.pem ubuntu@<YOUR_EC2_PUBLIC_IP>
```

Run the following commands to install Node.js, Python, Nginx, and clone your code:

```bash
# 1. Update OS and install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx git curl

# 2. Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 3. Clone your GitHub Repository
# REPACE THIS URL with your actual personal repository URL!
git clone https://github.com/Sireesha-bavirthi/GPC.git
cd GPC

# 4. Set up the Python Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install --with-deps chromium

# 5. Set up the React Frontend
cd apo
npm install
npm run build
cd ..
```

---

## 3. Keep the Backend Alive (Systemd)

We will use Ubuntu's native `systemd` to keep your FastAPI backend running forever in the background, even if the server reboots.

Run this command to create a service file:
```bash
sudo nano /etc/systemd/system/apo-backend.service
```

Paste the following inside (press `Ctrl+O`, `Enter`, then `Ctrl+X` to save and exit):
```ini
[Unit]
Description=APO v2 FastAPI Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/GPC
Environment="PATH=/home/ubuntu/GPC/venv/bin"
ExecStart=/home/ubuntu/GPC/venv/bin/uvicorn backend:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable apo-backend
sudo systemctl start apo-backend
```

---

## 4. Serve the Frontend & API (NGINX)

Configure Nginx to act as the public web server. It will serve your React app directly, and cleanly forward `/api` requests to your Python backend.

```bash
sudo nano /etc/nginx/sites-available/apo
```

Paste this configuration:
```nginx
server {
    listen 80;
    server_name _; # Or replace with your domain name

    # Serve the React Frontend
    location / {
        root /home/ubuntu/GPC/apo/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to the Python Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        
        # Needed for Server-Sent Events (SSE) logs!
        proxy_set_header Connection '';
        chunked_transfer_encoding off;
        proxy_buffering off;
        proxy_cache off;
    }
}
```

Enable the site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/apo /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
```

**Your website is now LIVE!** Go to `http://<YOUR_EC2_PUBLIC_IP>` in your browser!

---

## 5. Automating the Pipeline (GitHub Actions)

So that you never have to SSH into the server manually again to update code, let's connect GitHub Actions to your server.

Go to your personal GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions**. Add these 3 "Repository Secrets":

1. `EC2_HOST`: The Public IP address of your EC2 instance (e.g. `54.123.45.67`)
2. `EC2_USERNAME`: `ubuntu`
3. `EC2_SSH_KEY`: Open your `apo-key.pem` file in a text editor on your computer, copy the *entire* contents (including `-----BEGIN RSA PRIVATE KEY-----`), and paste it here.

Now, whenever you `git push` to `main`, GitHub will automatically SSH into your server, run `git pull`, rebuild React, and restart Python!
