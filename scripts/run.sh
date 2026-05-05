#!/bin/bash

# JARVIS Quick Start Script
# Usage: ./run.sh

# Kill any existing JARVIS processes
echo "Cleaning up..."
pkill -f uvicorn 2>/dev/null
sleep 1

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating environment..."
source .venv/bin/activate

# Install dependencies if needed
if [ ! -f ".venv/lib/python*/site-packages/fastapi" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Start backend
echo "Starting backend..."
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check backend health
if curl -s http://127.0.0.1:8765/health > /dev/null 2>&1; then
    echo "Backend running on http://127.0.0.1:8765"
else
    echo "Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start Electron
echo "Starting JARVIS GUI..."
npx electron . 

# Cleanup on exit
echo "Cleaning up..."
kill $BACKEND_PID 2>/dev/null
deactivate 2>/dev/null
echo "Goodbye!"