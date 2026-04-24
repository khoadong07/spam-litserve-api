#!/bin/bash

# Simple production start script - chạy trực tiếp qua port 8990
set -e

echo "🚀 Starting Spam Filter API on port 8990"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-8990}
WORKERS=${WORKERS:-"auto"}
SERVER=${SERVER:-"gunicorn"}
ML_ENABLE=${ML_ENABLE:-"true"}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found!"
    print_info "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install gunicorn uvicorn[standard]
    print_success "Virtual environment created and dependencies installed"
else
    print_success "Virtual environment found"
    source venv/bin/activate
fi

# Set environment variables
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export ML_ENABLE=$ML_ENABLE
export TOKENIZERS_PARALLELISM=false

# Create logs directory
mkdir -p logs

# Calculate workers
if [ "$WORKERS" = "auto" ]; then
    if command -v nvidia-smi &> /dev/null; then
        WORKERS=2  # GPU workload
        print_info "GPU detected: Using $WORKERS workers"
    else
        WORKERS=$(($(nproc) * 2 + 1))
        if [ $WORKERS -gt 8 ]; then
            WORKERS=8
        fi
        print_info "CPU workload: Using $WORKERS workers"
    fi
fi

print_info "Configuration:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Workers: $WORKERS"
echo "  Server: $SERVER"
echo "  ML Enabled: $ML_ENABLE"

# Health check function
health_check() {
    local max_attempts=30
    local attempt=1
    
    print_info "Waiting for API to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "http://$HOST:$PORT/health" > /dev/null 2>&1; then
            print_success "✅ API is healthy and ready!"
            print_success "🌐 API URL: http://$HOST:$PORT"
            print_info "📋 Available endpoints:"
            echo "   - GET  http://$HOST:$PORT/health"
            echo "   - GET  http://$HOST:$PORT/"
            echo "   - POST http://$HOST:$PORT/v1/api/infer"
            echo "   - POST http://$HOST:$PORT/api/spam"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "API failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Start server based on type
start_server() {
    case "$SERVER" in
        "gunicorn")
            print_info "🚀 Starting Gunicorn server..."
            gunicorn main:app \
                --bind="$HOST:$PORT" \
                --workers="$WORKERS" \
                --worker-class=uvicorn.workers.UvicornWorker \
                --worker-connections=1000 \
                --max-requests=10000 \
                --max-requests-jitter=1000 \
                --preload \
                --timeout=120 \
                --keep-alive=5 \
                --access-logfile=logs/access.log \
                --error-logfile=logs/error.log \
                --log-level=info \
                --capture-output &
            ;;
        "uvicorn")
            print_info "🚀 Starting Uvicorn server..."
            uvicorn main:app \
                --host "$HOST" \
                --port "$PORT" \
                --workers "$WORKERS" \
                --loop uvloop \
                --http httptools \
                --access-log \
                --log-level info \
                --backlog 2048 \
                --limit-concurrency 2000 &
            ;;
        "python")
            print_info "🚀 Starting Python server..."
            python main.py &
            ;;
        *)
            print_error "Unknown server type: $SERVER"
            print_info "Available servers: gunicorn, uvicorn, python"
            exit 1
            ;;
    esac
    
    SERVER_PID=$!
    echo $SERVER_PID > server.pid
    print_success "Server started with PID: $SERVER_PID"
}

# Cleanup function
cleanup() {
    print_info "Shutting down server..."
    if [ -f server.pid ]; then
        PID=$(cat server.pid)
        kill $PID 2>/dev/null || true
        rm -f server.pid
    fi
    pkill -f "gunicorn\|uvicorn" 2>/dev/null || true
    print_success "Server stopped"
}

# Signal handlers
trap cleanup EXIT
trap 'print_error "Interrupted"; exit 1' INT TERM

# Main execution
main() {
    # Check for help
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Simple production start script for Spam Filter API"
        echo ""
        echo "Environment Variables:"
        echo "  HOST        Host to bind (default: 0.0.0.0)"
        echo "  PORT        Port to bind (default: 8990)"
        echo "  WORKERS     Number of workers (default: auto)"
        echo "  SERVER      Server type: gunicorn|uvicorn|python (default: gunicorn)"
        echo "  ML_ENABLE   Enable ML inference (default: true)"
        echo ""
        echo "Examples:"
        echo "  $0                           # Start with defaults"
        echo "  PORT=9000 $0                # Custom port"
        echo "  SERVER=uvicorn WORKERS=1 $0  # Uvicorn with 1 worker"
        echo "  ML_ENABLE=false $0          # Disable ML"
        echo ""
        echo "Quick test:"
        echo "  curl http://localhost:8990/health"
        exit 0
    fi
    
    # Start server
    start_server
    
    # Wait a bit then health check
    sleep 3
    if health_check; then
        print_success "🎉 Server is running successfully!"
        print_info "Press Ctrl+C to stop the server"
        
        # Keep running
        wait $SERVER_PID
    else
        print_error "❌ Server failed to start properly"
        cleanup
        exit 1
    fi
}

# Run main function
main "$@"