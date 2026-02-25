# ============================================================
# Dockerfile — AI Financial Research Agent (Render-optimised)
# ============================================================
# Strategy:
#   Stage 1 (frontend-builder) → Build Next.js standalone output
#   Stage 2 (backend)          → Python 3.11-slim + Node.js runtime
#                                Copies only the tiny standalone bundle
# ============================================================

# ─────────────────────────────────────────────────────────────
# Stage 1 — Build the Next.js frontend (standalone mode)
# ─────────────────────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install deps first (better layer caching)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy source and build standalone bundle
COPY frontend/ ./
ARG NEXT_PUBLIC_API_URL="http://127.0.0.1:8000"
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build


# ─────────────────────────────────────────────────────────────
# Stage 2 — Python backend + minimal Node.js runtime
# ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS backend

# ── 1. System dependencies & Node.js ──────────────────────────
# We install build-essential only to compile Python C-extensions,
# then REMOVE it in the same layer to keep the image lean.
# Node.js is fetched from NodeSource so we avoid the heavy
# nodejs/npm apt packages.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends \
    nodejs \
    && apt-get purge -y --auto-remove gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── 2. Python dependencies ─────────────────────────────────────

# Install PyTorch CPU-only FIRST (separate layer for better caching
# and to use the dedicated CPU wheel index).
RUN pip install --no-cache-dir \
    torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── 3. Application source code ─────────────────────────────────
COPY backend/ ./backend/
COPY .env.example .env.example

# ── 4. Next.js standalone bundle (tiny — no node_modules!) ─────
# standalone/ already contains its own server.js + bundled deps
COPY --from=frontend-builder /app/frontend/.next/standalone ./frontend/
# Static assets must live at <standalone>/frontend/.next/static
COPY --from=frontend-builder /app/frontend/.next/static ./frontend/.next/static
# public/ folder (if it exists) must live at <standalone>/frontend/public
# Uncomment the next line if you add a public/ folder to the frontend
# COPY --from=frontend-builder /app/frontend/public ./frontend/public

# ── 5. Data directory ──────────────────────────────────────────
RUN mkdir -p /app/data

# ── 6. Entrypoint ──────────────────────────────────────────────
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Render assigns PORT dynamically; expose both internal ports for docs
ARG BACKEND_PORT=8000
ARG FRONTEND_PORT=3000
EXPOSE $BACKEND_PORT $FRONTEND_PORT

ENTRYPOINT ["docker-entrypoint.sh"]