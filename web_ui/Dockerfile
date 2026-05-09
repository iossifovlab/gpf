# CI image for the Angular frontend (web_ui).
#
# Build from the repo root:
#     docker build -f web_ui/Dockerfile -t gpf-web-ui-ci .

# syntax=docker/dockerfile:1.7
ARG NODE_VERSION=22.14.0-alpine
FROM node:${NODE_VERSION}

WORKDIR /app

# Deps layer first so source-only edits hit the cache.
COPY web_ui/package.json web_ui/package-lock.json ./

RUN --mount=type=cache,target=/root/.npm npm ci

COPY web_ui/ ./

CMD ["npx", "jest", "--ci"]
