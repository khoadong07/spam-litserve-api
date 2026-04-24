#!/bin/bash

# GPU-safe production starter - ALWAYS single worker for GPU
set -e

echo "🎮 Starting GPU-Safe Spam Filter API"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Configuration - FORCE single worker for GPU safety
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-8990}
WORKERS=1  # ALWAYS 1 for GPU safety
ML_ENABLE=${ML_ENABLE:-"true"}
VENV_PATH=${VENV_PATH:-".venv"}
SERVER=${SERVER:-"python"}  # Default to Python for simplicity

# Check and activate venv
if [ ! -d "$VENV_PATH" ]; then
    print_error "Virtual environment not found at $VENV_PATH"
    exit 1
fi

print_success "Activating virtual environment: $VENV_PATH"
source "$VENV_PATH/bin/activate"

# Set CUDA-safe environment variables
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export ML_ENABLE=$ML_ENABLE
export TOKENIZERS_PARALLELISM=false
export TORCH_MULTIPROCESSING_SHARING_STRATEGY=file_system
export CUDA_LAUNCH_BLOCKING=0
export TORCH_CUDNN_V8_API_ENABLED=1

# Create logs directory
mkdir -p logs

print_info "GPU-Safe Configuration:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Workers: $WORKERS (FORCED for GPU safety)"
echo "  Server: $SERVER"
echo "  ML Enabled: $ML_ENABLE"
echo "  Virtual Env: $VENV_PATH"

# Check dependencies
python -c "import torch, transformers, fastapi, accelerate" 2>/dev/null || {
    print_error "Missing dependencies!"
    print_info "Run: ./fix_deps.sh"
    exit 1
}

print_success "Dependencies OK"

# Show GPU info
if command -v nvidia-smi &> /dev/null && nvidia-smi > /dev/null 2>&1; then
    print_info "GPU Information:"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader | while read line; do
        echo "  $line"
    done
    print_warning "Using SINGLE WORKER for CUDA multiprocessing safety"
else
    print_info "No GPU detected, using CPU"
fi

# Start server - ALWAYS single process for GPU
print_info "🚀 Starting GPU-safe server (single worker)..."

case "$SERVER" in
    "python")
        print_info "Starting with Python directly (GPU-safe)..."
        exec python main.py
        ;;
    "uvicorn")
        print_info "Starting Uvicorn with 1 worker (GPU-safe)..."
        exec uvicorn main:app \
            --host "$HOST" \
            --port "$PORT" \
            --workers 1 \
            --loop uvloop \
            --http httptools \
            --access-log \
            --log-level info \
            --backlog 2048 \
            --limit-concurrency 2000 \
            --timeout-keep-alive 10
        ;;
    "gunicorn")
        print_warning "Gunicorn with 1 worker (not recommended for GPU, use python instead)"
        exec gunicorn main:app \
            --bind="$HOST:$PORT" \
            --workers=1 \
            --worker-class=uvicorn.workers.UvicornWorker \
            --worker-connections=1000 \
            --max-requests=5000 \
            --preload \
            --timeout=120 \
            --keep-alive=5 \
            --log-level=info \
            --worker-tmp-dir=/tmp
        ;;
    *)
        print_error "Unknown server: $SERVER"
        print_info "Available servers: python (recommended), uvicorn, gunicorn"
        exit 1
        ;;
esac