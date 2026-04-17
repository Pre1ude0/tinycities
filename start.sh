#!/bin/bash

set -e

# Read preferred ports from environment variables (with defaults)
BACKEND_PORT="${BACKEND_PORT:-8001}"
FRONTEND_PORT="${FRONTEND_PORT:-8000}"

echo $BACKEND_PORT
echo $FRONTEND_PORT

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"


# Store PIDs
UVICORN_PID=""
NODE_PID=""

# Graceful shutdown handler
shutdown() {
    echo "Shutting down services..."

    if [ -n "$UVICORN_PID" ]; then
        kill -TERM "$UVICORN_PID"
    fi

    if [ -n "$NODE_PID" ]; then
        kill -TERM "$NODE_PID"
    fi

    wait "$UVICORN_PID"
    wait "$NODE_PID"

    echo "Shutdown complete"
    exit 0
}

trap shutdown SIGTERM SIGINT

# Start backend
source venv/bin/activate
cd $SCRIPT_DIR/backend
uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT &
UVICORN_PID=$!

# Start frontend
cd $SCRIPT_DIR/frontend
PORT=$FRONTEND_PORT node build  &
NODE_PID=$!

# Wait for processes
wait -n

# If one crashes, shut down the other
shutdown
