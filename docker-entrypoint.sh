#!/bin/sh
# docker-entrypoint.sh
set -e

echo "========================================"
echo "  🏦 AI Financial Research Agent"
echo "========================================"

# Environment variables with defaults
BACKEND_HOST=${BACKEND_HOST:-127.0.0.1}
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_HOST=${FRONTEND_HOST:-0.0.0.0}
FRONTEND_PORT=${PORT:-3000}

# 1. Start FastAPI backend
# We bind to BACKEND_HOST so it is only reachable from Next.js via the rewrite proxy by default.
echo "▶  Starting FastAPI backend on ${BACKEND_HOST}:${BACKEND_PORT}..."
cd /app
uvicorn backend.app.main:app --host $BACKEND_HOST --port $BACKEND_PORT &
BACKEND_PID=$!

# 2. Start Next.js frontend using the standalone server.js
# Render injects $PORT (e.g. 10000); default to 3000 for local Docker runs.
echo "▶  Starting Next.js frontend on port $FRONTEND_PORT..."

# The standalone bundle was copied to /app/frontend/; server.js sits there.
cd /app/frontend
HOSTNAME=$FRONTEND_HOST PORT=$FRONTEND_PORT node server.js &
FRONTEND_PID=$!

echo "========================================"
echo "  ✅  Services started"
echo "  Backend (Internal) → http://${BACKEND_HOST}:${BACKEND_PORT}"
echo "  Frontend (Public)  → http://${FRONTEND_HOST}:${FRONTEND_PORT}"
echo "========================================"

# Wait for either process to exit (crash → container stops → Render restarts it)
wait $BACKEND_PID $FRONTEND_PID