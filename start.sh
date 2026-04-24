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
WORKERS=${WORKERS:-"auto"}  # auto, or specific number
ML_ENABLE=${ML_ENABLE:-"true"}
VENV_PATH=${VENV_PATH:-".venv"}
SERVER=${SERVER:-"auto"}  # auto, uvicorn, gunicorn, python

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
export CUDA_LAUNCH_BLOCKING=0
export TORCH_CUDNN_V8_API_ENABLED=1

# Calculate optimal workers
calculate_workers() {
    if [ "$WORKERS" = "auto" ]; then
        # Check for GPU
        if command -v nvidia-smi &> /dev/null && nvidia-smi > /dev/null 2>&1; then
            # GPU detected - MUST use single worker for CUDA safety
            WORKERS=1
            print_info "GPU detected: Using $WORKERS worker (CUDA multiprocessing safe)"
        else
            # CPU only - can use more workers
            CPU_CORES=$(nproc)
            WORKERS=$((CPU_CORES > 8 ? 8 : CPU_CORES))
            print_info "CPU workload: Using $WORKERS workers"
        fi
    else
        # If user specified workers > 1 with GPU, warn and force to 1
        if command -v nvidia-smi &> /dev/null && nvidia-smi > /dev/null 2>&1 && [ "$WORKERS" -gt 1 ]; then
            print_warning "GPU detected but WORKERS=$WORKERS specified. Forcing WORKERS=1 for CUDA safety"
            WORKERS=1
        fi
        print_info "Using workers: $WORKERS"
    fi
}

# Choose optimal server
choose_server() {
    if [ "$SERVER" = "auto" ]; then
        if [ "$WORKERS" = "1" ]; then
            SERVER="python"
            print_info "Single worker: Using Python directly (best for GPU)"
        elif python -c "import gunicorn" 2>/dev/null; then
            SERVER="gunicorn"
            print_info "Multi-worker: Using Gunicorn"
        elif python -c "import uvicorn" 2>/dev/null; then
            SERVER="uvicorn"
            print_info "Multi-worker: Using Uvicorn"
        else
            SERVER="python"
            print_info "Fallback: Using Python directly"
        fi
    fi
}

calculate_workers
choose_server

# Create logs directory
mkdir -p logs

print_info "Configuration:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Workers: $WORKERS"
echo "  Server: $SERVER"
echo "  ML Enabled: $ML_ENABLE"
echo "  Virtual Env: $VENV_PATH"

# Check basic dependencies
python -c "import torch, transformers, fastapi" 2>/dev/null || {
    print_error "Missing dependencies!"
    print_info "Please install dependencies first:"
    echo "  ./install_pytorch.sh"
    echo "  # or manually:"
    echo "  source $VENV_PATH/bin/activate"
    echo "  pip install torch==2.5.1+cu121 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
    echo "  pip install transformers fastapi uvicorn[standard] accelerate"
    exit 1
}

# Check for accelerate (required for model loading)
python -c "import accelerate" 2>/dev/null || {
    print_error "Missing accelerate package!"
    print_info "Installing accelerate..."
    pip install accelerate
}

print_success "Dependencies OK"

# Show GPU info if available
if command -v nvidia-smi &> /dev/null && nvidia-smi > /dev/null 2>&1; then
    print_info "GPU Information:"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader | while read line; do
        echo "  $line"
    done
fi

# Start server based on configuration
print_info "🚀 Starting server with $WORKERS workers..."

case "$SERVER" in
    "gunicorn")
        if ! python -c "import gunicorn" 2>/dev/null; then
            print_error "Gunicorn not installed. Installing..."
            pip install gunicorn
        fi
        
        print_info "Starting Gunicorn with $WORKERS workers..."
        exec gunicorn main:app \
            --bind="$HOST:$PORT" \
            --workers="$WORKERS" \
            --worker-class=uvicorn.workers.UvicornWorker \
            --worker-connections=1000 \
            --max-requests=5000 \
            --max-requests-jitter=500 \
            --preload \
            --timeout=120 \
            --keep-alive=5 \
            --access-logfile=logs/access.log \
            --error-logfile=logs/error.log \
            --log-level=info \
            --worker-tmp-dir=/tmp
        ;;
    "uvicorn")
        if ! python -c "import uvicorn" 2>/dev/null; then
            print_error "Uvicorn not installed. Installing..."
            pip install uvicorn[standard]
        fi
        
        print_info "Starting Uvicorn with $WORKERS workers..."
        exec uvicorn main:app \
            --host "$HOST" \
            --port "$PORT" \
            --workers "$WORKERS" \
            --loop uvloop \
            --http httptools \
            --access-log \
            --log-level info \
            --backlog 2048 \
            --limit-concurrency 2000 \
            --timeout-keep-alive 10
        ;;
    "python")
        print_info "Starting with Python directly (single process)..."
        exec python main.py
        ;;
    *)
        print_error "Unknown server: $SERVER"
        print_info "Available servers: gunicorn, uvicorn, python"
        exit 1
        ;;
esac