# Frontend (Vite) development server.
# Build context is repo root; COPY paths use src/frontend.
FROM node:18-alpine

WORKDIR /app/frontend

# Copy package files first for better caching
COPY src/frontend/package*.json ./

RUN npm install

# Copy frontend source (rest mounted as volume in dev)
COPY src/frontend/ .

ENV NODE_ENV=development
ENV VITE_BACKEND_URL=http://localhost:9000
ENV VITE_AUTH_URL=http://localhost:9100

CMD ["npm", "run", "dev", "--", "--host"]
