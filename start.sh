#!/bin/bash

# Simple production starter - uses existing .venv
set -e

echo "🚀 Starting Spam Filter API Production"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-8990}
ML_ENABLE=${ML_ENABLE:-"true"}
VENV_PATH=${VENV_PATH:-".venv"}

# Check and activate venv
if [ ! -d "$VENV_PATH" ]; then
    print_error "Virtual environment not found at $VENV_PATH"
    print_info "Please create it first:"
    echo "  python3 -m venv $VENV_PATH"
    echo "  source $VENV_PATH/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

print_success "Activating virtual environment: $VENV_PATH"
source "$VENV_PATH/bin/activate"

# Set environment variables
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export ML_ENABLE=$ML_ENABLE
export TOKENIZERS_PARALLELISM=false
export TORCH_MULTIPROCESSING_SHARING_STRATEGY=file_system

# Create logs directory
mkdir -p logs

print_info "Configuration:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  ML Enabled: $ML_ENABLE"
echo "  Virtual Env: $VENV_PATH"

# Check basic dependencies
python -c "import torch, transformers, fastapi" 2>/dev/null || {
    print_error "Missing dependencies. Please install them:"
    echo "  source $VENV_PATH/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
}

print_success "Dependencies OK"

# Start server
print_info "🚀 Starting server..."

# Try different methods
if python -c "import uvicorn" 2>/dev/null; then
    print_info "Using Uvicorn..."
    exec uvicorn main:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers 1 \
        --loop uvloop \
        --http httptools \
        --access-log \
        --log-level info
elif python -c "import gunicorn" 2>/dev/null; then
    print_info "Using Gunicorn..."
    exec gunicorn main:app \
        --bind="$HOST:$PORT" \
        --workers=1 \
        --worker-class=uvicorn.workers.UvicornWorker \
        --timeout=120 \
        --log-level=info
else
    print_info "Using Python directly..."
    exec python main.py
fi