#!/bin/sh
set -e

DOMAIN="${DOMAIN:-}"
SSL_CONF="/etc/nginx/conf.d/ssl-enabled.conf"
DEFAULT_CONF="/etc/nginx/conf.d/default.conf"

if [ -n "$DOMAIN" ] && [ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
  echo "TLS cert found for ${DOMAIN} — enabling HTTPS"
  envsubst '${DOMAIN}' < /etc/nginx/templates/ssl.conf.template > "$SSL_CONF"
  # Avoid two server blocks fighting on :80 — SSL template owns port 80 redirect.
  rm -f "$DEFAULT_CONF"
else
  echo "No TLS cert yet — serving HTTP only (run deploy/enable-https.sh)"
  rm -f "$SSL_CONF"
fi

nginx -t
exec nginx -g "daemon off;"
