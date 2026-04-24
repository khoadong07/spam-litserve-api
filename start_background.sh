#!/bin/bash

# Start production server in background with logging
set -e

echo "🚀 Starting Spam Filter API in Background"

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

# Configuration
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-8990}
ML_ENABLE=${ML_ENABLE:-"true"}
VENV_PATH=${VENV_PATH:-".venv"}
SERVER=${SERVER:-"python"}

# Create logs directory
mkdir -p logs

# Log files
LOG_FILE="logs/spam-filter-api.log"
ERROR_LOG="logs/spam-filter-error.log"
PID_FILE="logs/spam-filter-api.pid"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        print_warning "Server already running with PID: $PID"
        print_info "To stop: ./stop_server.sh"
        print_info "To restart: ./restart_server.sh"
        exit 1
    else
        print_info "Removing stale PID file"
        rm -f "$PID_FILE"
    fi
fi

# Check and activate venv
if [ ! -d "$VENV_PATH" ]; then
    print_error "Virtual environment not found at $VENV_PATH"
    exit 1
fi

print_info "Activating virtual environment: $VENV_PATH"
source "$VENV_PATH/bin/activate"

# Set environment variables
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export ML_ENABLE=$ML_ENABLE
export TOKENIZERS_PARALLELISM=false
export TORCH_MULTIPROCESSING_SHARING_STRATEGY=file_system
export CUDA_LAUNCH_BLOCKING=0
export TORCH_CUDNN_V8_API_ENABLED=1

print_info "Configuration:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Server: $SERVER"
echo "  ML Enabled: $ML_ENABLE"
echo "  Log File: $LOG_FILE"
echo "  Error Log: $ERROR_LOG"
echo "  PID File: $PID_FILE"

# Check dependencies
python -c "import torch, transformers, fastapi" 2>/dev/null || {
    print_error "Missing dependencies!"
    exit 1
}

# Show GPU info
if command -v nvidia-smi &> /dev/null && nvidia-smi > /dev/null 2>&1; then
    print_info "GPU detected - using single worker for CUDA safety"
    nvidia-smi --query-gpu=name,memory.free --format=csv,noheader >> "$LOG_FILE"
fi

# Start server in background
print_info "🚀 Starting server in background..."

case "$SERVER" in
    "python")
        nohup python main.py > "$LOG_FILE" 2> "$ERROR_LOG" &
        SERVER_PID=$!
        ;;
    "uvicorn")
        nohup uvicorn main:app \
            --host "$HOST" \
            --port "$PORT" \
            --workers 1 \
            --loop uvloop \
            --http httptools \
            --log-level info \
            --access-log \
            --backlog 2048 \
            --limit-concurrency 2000 \
            --timeout-keep-alive 10 \
            > "$LOG_FILE" 2> "$ERROR_LOG" &
        SERVER_PID=$!
        ;;
    "gunicorn")
        nohup gunicorn main:app \
            --bind="$HOST:$PORT" \
            --workers=1 \
            --worker-class=uvicorn.workers.UvicornWorker \
            --worker-connections=1000 \
            --max-requests=5000 \
            --preload \
            --timeout=120 \
            --keep-alive=5 \
            --log-level=info \
            --access-logfile="logs/access.log" \
            --error-logfile="$ERROR_LOG" \
            > "$LOG_FILE" 2>&1 &
        SERVER_PID=$!
        ;;
    *)
        print_error "Unknown server: $SERVER"
        exit 1
        ;;
esac

# Save PID
echo $SERVER_PID > "$PID_FILE"

print_success "Server started in background!"
print_info "PID: $SERVER_PID"
print_info "Logs: $LOG_FILE"
print_info "Errors: $ERROR_LOG"

# Wait a moment and check if server started successfully
sleep 3

if ps -p "$SERVER_PID" > /dev/null 2>&1; then
    print_success "✅ Server is running (PID: $SERVER_PID)"
    
    # Try health check
    print_info "Checking server health..."
    for i in {1..10}; do
        if curl -f -s "http://$HOST:$PORT/health" > /dev/null 2>&1; then
            print_success "✅ Server is healthy and responding!"
            print_info "🌐 API URL: http://$HOST:$PORT"
            break
        fi
        echo -n "."
        sleep 2
    done
    echo
    
    print_info "📋 Management commands:"
    echo "  View logs:    tail -f $LOG_FILE"
    echo "  View errors:  tail -f $ERROR_LOG"
    echo "  Stop server:  ./stop_server.sh"
    echo "  Restart:      ./restart_server.sh"
    echo "  Test API:     python3 test_production.py"
    
else
    print_error "❌ Server failed to start"
    print_info "Check error log: cat $ERROR_LOG"
    rm -f "$PID_FILE"
    exit 1
fi