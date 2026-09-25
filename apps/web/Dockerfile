# ADDMAI Web Frontend Dockerfile (Stage 1.1 Hardened)
# Pinned to specific Node release to eliminate environment drift
FROM node:20.12.2-alpine

WORKDIR /app

# Install dependencies
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

# Copy frontend source code
COPY apps/web/ ./

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
