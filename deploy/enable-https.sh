#!/usr/bin/env bash
# Obtain a Let's Encrypt certificate and reload Nginx with HTTPS.
# Usage (on EC2, from project root):
#   chmod +x deploy/enable-https.sh && ./deploy/enable-https.sh
#
# Prerequisites:
#   1. A domain whose A record points to this EC2 public IP
#   2. Security group allows inbound TCP 80 and 443
#   3. In .env.prod: DOMAIN=... and CERTBOT_EMAIL=...

set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env.prod ]]; then
  echo "Missing .env.prod"
  exit 1
fi

get_env() {
  local key="$1"
  grep -E "^${key}=" .env.prod | head -n1 | cut -d= -f2- | tr -d '"' | tr -d "'" | tr -d '\r'
}

DOMAIN="$(get_env DOMAIN)"
CERTBOT_EMAIL="$(get_env CERTBOT_EMAIL)"

if [[ -z "$DOMAIN" || -z "$CERTBOT_EMAIL" ]]; then
  echo "Set DOMAIN and CERTBOT_EMAIL in .env.prod first."
  exit 1
fi

echo "=== 1/3 Ensure stack is up (HTTP needed for ACME) ==="
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d
sleep 5

echo "=== 2/3 Request Let's Encrypt certificate for ${DOMAIN} ==="
docker compose --profile certbot --env-file .env.prod -f docker-compose.prod.yml run --rm certbot \
  certonly --webroot -w /var/www/certbot \
  -d "$DOMAIN" \
  --email "$CERTBOT_EMAIL" \
  --agree-tos \
  --no-eff-email \
  --non-interactive

echo "=== 3/3 Reload nginx + web with TLS (DOMAIN=${DOMAIN}) ==="
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build nginx web

echo
echo "HTTPS should be live at: https://${DOMAIN}"
echo
echo "Confirm .env.prod has:"
echo "  DJANGO_ALLOWED_HOSTS=${DOMAIN},YOUR_EC2_IP,localhost,127.0.0.1"
echo "  CORS_ALLOWED_ORIGINS=https://${DOMAIN}"
echo "Then: docker compose --env-file .env.prod -f docker-compose.prod.yml up -d web worker"
