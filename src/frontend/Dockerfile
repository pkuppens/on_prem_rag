FROM node:18-alpine

WORKDIR /app/frontend

# Copy package files first for better caching
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend code
COPY frontend/ .

# Set environment variables
ENV NODE_ENV=development
ENV VITE_BACKEND_URL=http://localhost:8001

# Start development server
CMD ["npm", "run", "dev", "--", "--host"]
