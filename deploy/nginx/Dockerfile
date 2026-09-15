FROM node:20-alpine AS frontend

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./

ARG VITE_API_BASE=
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

FROM nginx:1.27-alpine

RUN apk add --no-cache gettext

COPY deploy/nginx/nginx.conf /etc/nginx/nginx.conf
COPY deploy/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY deploy/nginx/ssl.conf.template /etc/nginx/templates/ssl.conf.template
COPY deploy/nginx/docker-entrypoint.sh /docker-entrypoint-https.sh
RUN chmod +x /docker-entrypoint-https.sh

COPY --from=frontend /app/dist /usr/share/nginx/html

EXPOSE 80 443
ENTRYPOINT ["/docker-entrypoint-https.sh"]
