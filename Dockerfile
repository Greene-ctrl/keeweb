# Stage 1: Build KeeWeb
FROM node:20 AS builder
WORKDIR /app
COPY . .
RUN npm install --ignore-scripts
RUN export NODE_OPTIONS=--openssl-legacy-provider && ./node_modules/.bin/grunt build-web-app --skip-sign

# Stage 2: Python Backend
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv via pip
RUN pip install uv

# Create a non-root user
RUN useradd -m -u 1000 user

# Set up work directory
WORKDIR /home/user/app

# Install python dependencies using uv
RUN uv pip install --system fastapi uvicorn pykeepass pydantic python-multipart

# Copy built frontend
COPY --from=builder /app/dist ./dist

# Copy backend code
COPY backend/ ./backend/

# Change ownership to non-root user
RUN chown -R user:user /home/user/app

# Switch to non-root user
USER user
ENV HOME=/home/user
ENV PATH="/home/user/.local/bin:${PATH}"

# Expose port 7860
EXPOSE 7860

# Command to run the app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
