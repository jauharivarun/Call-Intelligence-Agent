# Deploy on a single EC2 (project / demo)

Stack on one instance: **Nginx + Gunicorn + Celery + Postgres + Redis** via Docker Compose.  
No ALB, RDS, ElastiCache, or Elastic IP required.

HTTPS options (pick one):

1. **Cloudflare (recommended for this project)** — free HTTPS at the edge; EC2 only needs port 80.
2. **HTTP only** — open `http://YOUR_EC2_IP` (fine for a quick demo).

---

## 1. Launch EC2

1. AWS Console → **EC2** → **Launch instance**.
2. Suggested settings:
   - **AMI:** Ubuntu 24.04 LTS
   - **Instance type:** `t3.small` (2 GB; safer than `t3.micro` for Postgres + Docker)
   - **Key pair:** create/download one (`.pem`) for SSH
   - **Network:** default VPC is fine; **Auto-assign public IP: Enable**
   - **Storage:** 20–30 GB gp3
3. **Security group** inbound:
   - SSH `22` from your IP
   - HTTP `80` from `0.0.0.0/0` (and `::/0` if you use IPv6)
   - Do **not** open `5432` / `6379` / `8000` to the world
4. Launch, then copy the **Public IPv4 address**.

> Tip: avoid **Stop** if you have no Elastic IP and no Cloudflare DNS yet — the public IP can change on start.

---

## 2. Install Docker on the instance

SSH in:

```bash
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

Then:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker ubuntu
```

Log out and SSH back in so the `docker` group applies.

---

## 3. Copy the project to EC2

**Option A — git** (if the repo is on GitHub):

```bash
cd ~
git clone YOUR_REPO_URL "Call Intelligence AI Agent"
cd "Call Intelligence AI Agent"
```

**Option B — from your laptop** (rsync):

```bash
rsync -avz --exclude node_modules --exclude .venv --exclude backend/media \
  -e "ssh -i /path/to/your-key.pem" \
  "/Users/jauharivarun/Documents/AI Projects/Call Intelligence AI Agent/" \
  ubuntu@YOUR_EC2_PUBLIC_IP:~/call-intelligence/
```

Then on EC2: `cd ~/call-intelligence` (or the path you used).

---

## 4. Configure environment

```bash
cp .env.prod.example .env.prod
nano .env.prod
```

Set at least:

- `DJANGO_SECRET_KEY` — long random string
- `DJANGO_ALLOWED_HOSTS` — `YOUR_EC2_PUBLIC_IP` (and domain if any)
- `CORS_ALLOWED_ORIGINS` — `http://YOUR_EC2_PUBLIC_IP` (and `https://your.domain.com` if using Cloudflare)
- `POSTGRES_PASSWORD` — strong password
- `DEMO_PASSWORD` / `DEMO_VIEWER_PASSWORD` — change both from the defaults
- `OPENAI_API_KEY` — your key (or leave placeholder to use mock AI)

Keep `SEED_DEMO=true` for the first boot so `admin` / `viewer` users are created.

---

## 5. Build and start

Always pass `--env-file .env.prod` so Compose can substitute DB passwords and related values:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

First build can take several minutes. Check status:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f web
```

Health check:

```bash
curl http://YOUR_EC2_PUBLIC_IP/api/health/
```

Open the UI: `http://YOUR_EC2_PUBLIC_IP`  
Login: `admin` / (your `DEMO_PASSWORD`).

After the first successful seed you can set `SEED_DEMO=false` in `.env.prod` (optional).

---

## 6. Enable HTTPS (requires a domain)

Browsers only get a trusted lock icon with a **domain name**. Let's Encrypt cannot issue a normal cert for a bare IP like `15.252.243.68`.

### 6a. AWS security group — open 443

1. EC2 → instance → **Security** tab → security group  
2. **Edit inbound rules** → Add: **HTTPS / TCP / 443 / Anywhere-IPv4**  
3. Save

### 6b. DNS

At your domain registrar (or Cloudflare DNS), create an **A** record:

- Name: `@` (or `app`)  
- Value: `YOUR_EC2_PUBLIC_IP` (e.g. `15.252.243.68`)  
- If using Cloudflare proxy for Let's Encrypt on the origin, set SSL mode to **Full** after certs exist, or use **DNS only** (grey cloud) while running Certbot.

Wait until `ping your.domain.com` (or DNS checker) shows your EC2 IP.

### 6c. Let's Encrypt on this stack (recommended)

1. Sync latest project code to EC2 (includes HTTPS support).
2. Edit `.env.prod`:

```env
DOMAIN=your.domain.com
CERTBOT_EMAIL=you@example.com
DJANGO_ALLOWED_HOSTS=your.domain.com,YOUR_EC2_PUBLIC_IP,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=https://your.domain.com
```

3. Run:

```bash
cd ~/call-intelligence
chmod +x deploy/enable-https.sh
./deploy/enable-https.sh
```

4. Open `https://your.domain.com`.

### 6d. Alternative: Cloudflare Flexible (no cert on EC2)

1. Add domain to Cloudflare → A record → Proxied (orange).  
2. SSL/TLS mode: **Flexible**.  
3. Set `CORS_ALLOWED_ORIGINS=https://your.domain.com` and restart web.  
Visitors get HTTPS; EC2 still speaks HTTP to Cloudflare.

---

## 7. Useful commands

```bash
# Logs
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f nginx web worker

# Restart after .env.prod edits
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d

# Shell into API
docker compose --env-file .env.prod -f docker-compose.prod.yml exec web python manage.py shell

# Stop everything
docker compose --env-file .env.prod -f docker-compose.prod.yml down
```

---

## Cost notes (≈ $75 credits)

| Resource | Approx. |
|----------|---------|
| `t3.small` 24/7 | ~$15/mo |
| 30 GB disk | ~$2–3/mo |
| Data transfer (light demo) | low |
| **Total** | **~$18–25/mo** → credits last several months |

Stop the instance when unused to stretch credits (remember: public IP may change).

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `DisallowedHost` | Add the exact Host (IP or domain) to `DJANGO_ALLOWED_HOSTS` |
| CORS errors | Match `CORS_ALLOWED_ORIGINS` to the URL in the browser bar (`http` vs `https`) |
| Upload fails / 413 | Nginx already allows 30MB; check file size ≤ 25MB |
| Pipeline stuck | `docker compose ... logs worker` — ensure OpenAI key or accept mock mode |
| Out of memory | Upgrade to `t3.small` or close other processes |
