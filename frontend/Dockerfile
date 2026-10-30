# ====================================================
# LabInsight AI — Frontend Dockerfile
# Node 20 alpine image with hot reload development support
# ====================================================

FROM node:20-alpine AS dev

WORKDIR /app

# Install dependencies first for layer caching
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

EXPOSE 5173

ENV HOST=0.0.0.0
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
