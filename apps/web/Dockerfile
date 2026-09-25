# ADDMAI Web Frontend Dockerfile (Stage 1)
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY apps/web/package.json ./
RUN npm install

# Copy frontend source code
COPY apps/web/ ./

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
