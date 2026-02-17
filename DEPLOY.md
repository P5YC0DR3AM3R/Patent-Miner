# Deployment Guide — Patent Miner

This document shows how to deploy the `Patent Miner` Streamlit app from the GitLab repository.

Contents
- Requirements and architecture
- GitLab CI variables to configure
- Server preparation (Ubuntu example)
- Nginx reverse-proxy + TLS (Let's Encrypt)
- Optional `docker-compose` production example
- Rolling updates and rollback

---

## 1. Architecture & Requirements

This deployment approach builds a Docker image in GitLab CI, pushes it to the GitLab Container Registry, and deploys to a single Linux server via SSH using Docker. It is simple, repeatable, and suitable for small/medium workloads.

Requirements
- A server/VM with public IP (Ubuntu 20.04+ recommended)
- SSH access and a non-root deploy user
- Docker installed on the server
- GitLab project with Container Registry enabled

---

## 2. GitLab CI Variables (Project → Settings → CI/CD → Variables)

Set these variables in your GitLab project (protect them for `main` branch):

- `SSH_PRIVATE_KEY` — Private key for the deploy user (value only)
- `DEPLOY_HOST` — Server IP or hostname (e.g. `203.0.113.4`)
- `DEPLOY_USER` — Deploy username on the server (e.g. `deploy`)
- `CI_REGISTRY_USER` and `CI_REGISTRY_PASSWORD` — usually provided by GitLab; if not, set your registry credentials

Optional (if you want to use a custom image tag):
- `IMAGE_TAG` — e.g. `latest` or a semantic version

Security notes
- Mark `SSH_PRIVATE_KEY` as **Protected** and **Masked**.
- Do not store application secrets in the repo. Use environment variables or mount a `.env` file on the host.

---

## 3. Server Preparation (Ubuntu example)

Run these once on the target server (replace `deploy` with your user):

```bash
# create deploy user
sudo adduser --disabled-password --gecos "" deploy
sudo usermod -aG sudo deploy

# add your public key to deploy user's authorized_keys (on your machine):
ssh-copy-id deploy@YOUR_SERVER_IP

# install docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker deploy

# optional: install docker-compose
sudo apt-get update
sudo apt-get install -y docker-compose

# prepare folder for persistent data
sudo -u deploy mkdir -p /srv/patent-miner
sudo chown -R deploy:deploy /srv/patent-miner
```

If you prefer to use systemd for the `docker run` or `docker-compose` process, create appropriate unit files.

---

## 4. Nginx Reverse Proxy + TLS (Let's Encrypt)

1. Install nginx on the server:

```bash
sudo apt-get update
sudo apt-get install -y nginx
```

2. Create an nginx site config (`/etc/nginx/sites-available/patent-miner`):

```nginx
server {
    listen 80;
    server_name your.domain.example;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. Enable and test nginx:

```bash
sudo ln -s /etc/nginx/sites-available/patent-miner /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

4. Obtain TLS cert with Certbot:

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your.domain.example
```

After TLS, nginx will forward HTTPS to the Streamlit container on `127.0.0.1:8501`.

---

## 5. `docker-compose` Production Example

Place a `docker-compose.prod.yml` in `/srv/patent-miner` on the server (or in the repo) and use it for `docker-compose` deployment.

Example `docker-compose.prod.yml`:

```yaml
version: '3.8'
services:
  patent-miner:
    image: registry.gitlab.com/<your-group>/<your-project>:latest
    restart: always
    ports:
      - "127.0.0.1:8501:8501"
    volumes:
      - ./patent_intelligence_vault:/app/patent_intelligence_vault
    environment:
      - PORT=8501
      # Add other environment vars here or mount a .env file
```

Deploy on the server:

```bash
cd /srv/patent-miner
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

---

## 6. GitLab CI Flow (what `.gitlab-ci.yml` does)

- `build` stage: builds Docker image and tags with `$CI_COMMIT_SHORT_SHA` and `latest`
- `push` stage: pushes both tags to GitLab Container Registry
- `deploy` stage: connects over SSH and executes Docker commands to pull and run the `latest` image on the server

When you push to `main`, CI will run and the `deploy` step will attempt to SSH to the server and update the running container.

---

## 7. Rolling Updates and Rollback

- CI deploys `latest`. If a deployment fails, you can roll back by pulling a previous image tag and restarting the container, e.g.:

```bash
# on server
docker pull registry.gitlab.com/<group>/<project>:<previous-tag>
docker stop patent-miner || true
docker rm patent-miner || true
docker run -d --name patent-miner -p 8501:8501 registry.gitlab.com/<group>/<project>:<previous-tag>
```

- For safer deployments, tag releases and update `.gitlab-ci.yml` to deploy by tag instead of `latest`.

---

## 8. Environment Variables & Secrets

- Keep runtime secrets out of the repo. Options:
  - Use Docker environment variables set in `docker-compose` on the host (not committed)
  - Mount a host `.env` file into the container (make sure `.env` is not in Git)

Example `docker run` with `.env`:

```bash
docker run --env-file /srv/patent-miner/.env -d --name patent-miner -p 8501:8501 registry.gitlab.com/<group>/<project>:latest
```

---

## 9. Post-deploy Verification

1. Confirm container is running: `docker ps`
2. Confirm Streamlit responds: `curl -I http://127.0.0.1:8501` (on server)
3. Confirm nginx proxy + TLS: open `https://your.domain.example`

---

## 10. Optional: Use Managed Hosts

If you prefer not to maintain a server, consider:
- Render, Fly.io, Railway, or Heroku — they accept Docker images
- Streamlit Community Cloud (easy but favors GitHub)

---

If you want, I can:
- commit this `DEPLOY.md` (done) and push it (I'll push now),
- add a `docker-compose.prod.yml` and sample nginx config into the repo,
- or walk you through adding the CI variables in GitLab.

## 11. Deploying to Render (recommended for managed hosting)

Render can build and deploy directly from your GitLab repository. Below are exact steps to connect and configure the service.

1. Sign in to Render (https://render.com) and select "New" → "Web Service".
2. Connect your GitLab account and authorize access to `micahreadmgmt-group/micahreadmgmt-Patent_Miner`.
3. Configure the service:
  - **Name:** Patent Miner
  - **Environment:** `Docker`
  - **Branch:** `main`
  - **Auto Deploy:** enabled (recommended)
  - **Disk:** enable persistent disk and mount to `/app/patent_intelligence_vault` if you want discovery artifacts persisted (the repo includes `render.yaml` which can preconfigure this)
4. Add environment variables in Render dashboard (Settings → Environment):
  - `PATENTSVIEW_API_KEY` (secret) — your API key
  - Any other runtime config such as `PATENT_SEARCH_API_KEY_ENV` if needed
5. Save and create the service. Render will build the Docker image using the `Dockerfile` in the repo and run the container, with `$PORT` injected into the container. The `Dockerfile` has been updated to honor `$PORT`.

Notes and best-practices:
- You do not need the GitLab `deploy` job if Render will handle deployment. I recommend disabling or removing the `deploy` job from `.gitlab-ci.yml` to avoid duplicate deploys.
- Keep secret values in Render's environment settings, not in your repo or `.env` committed files.
- Confirm persistent disk is enabled if you want `patent_intelligence_vault/` to survive restarts. Otherwise, use external storage or S3 for long-term artifact storage.

If you'd like, I will remove the `deploy` job from `.gitlab-ci.yml` so GitLab only builds (or runs tests) and Render handles deployments — say "Yes, remove GitLab deploy" and I will commit that change.

