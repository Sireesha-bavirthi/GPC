# ── Stage 1: Build ───────────────────────────────────────────────────────────
# Use Node.js to install dependencies and compile the React/Vite app
FROM node:20-alpine as build

WORKDIR /app

# Copy dependency files and install packages
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source code
COPY . .

# Build the production-ready static files (outputs to /app/dist)
RUN npm run build

# ── Stage 2: Serve ───────────────────────────────────────────────────────────
# Use tiny NGINX container to serve the compiled static files
FROM nginx:alpine

# Copy the compiled React app into NGINX's web root
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom NGINX config so API calls are proxied correctly
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
