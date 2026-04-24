#!/bin/bash

# Production deployment script for Spam Filter API (Non-Docker)
set -e

echo "🚀 Starting Production Spam Filter API (Non-Docker)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-8990}
WORKERS=${WORKERS:-"auto"}
SERVER=${SERVER:-"gunicorn"}
ML_ENABLE=${ML_ENABLE:-"true"}
VENV_PATH=${VENV_PATH:-"venv"}

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment exists
check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Virtual environment not found at $VENV_PATH"
        print_status "Please run setup_production.sh first or create virtual environment:"
        echo "  python3 -m venv $VENV_PATH"
        echo "  source $VENV_PATH/bin/activate"
        echo "  pip install -r requirements.txt"
        exit 1
    fi
    
    print_success "Virtual environment found at $VENV_PATH"
}

# Activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
    print_success "Virtual environment activated"
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Python version
    PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
    print_success "Python version: $PYTHON_VERSION"
    
    # Check CUDA availability
    if command -v nvidia-smi &> /dev/null; then
        print_success "NVIDIA GPU detected"
        nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits | while read line; do
            echo "  GPU: $line"
        done
    else
        print_warning "No NVIDIA GPU detected, using CPU"
    fi
    
    # Check memory
    TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
    FREE_MEM=$(free -g | awk '/^Mem:/{print $7}')
    print_success "Memory: ${FREE_MEM}GB free / ${TOTAL_MEM}GB total"
    
    if [ "$TOTAL_MEM" -lt 8 ]; then
        print_warning "Less than 8GB RAM detected. Performance may be limited."
    fi
    
    # Check CPU cores
    CPU_CORES=$(nproc)
    print_success "CPU cores: $CPU_CORES"
    
    # Check disk space
    DISK_SPACE=$(df -h . | awk 'NR==2{print $4}')
    print_success "Available disk space: $DISK_SPACE"
}

# Install/check dependencies
check_dependencies() {
    print_status "Checking Python dependencies..."
    
    # Check if required packages are installed
    python -c "import torch; print(f'PyTorch: {torch.__version__}')" || {
        print_error "PyTorch not found. Installing dependencies..."
        pip install -r requirements.txt
    }
    
    python -c "import transformers; print(f'Transformers: {transformers.__version__}')" || {
        print_error "Transformers not found. Installing dependencies..."
        pip install -r requirements.txt
    }
    
    python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')" || {
        print_error "FastAPI not found. Installing dependencies..."
        pip install -r requirements.txt
    }
    
    # Check server dependencies
    if [ "$SERVER" = "gunicorn" ]; then
        python -c "import gunicorn" || pip install gunicorn
    elif [ "$SERVER" = "hypercorn" ]; then
        python -c "import hypercorn" || pip install hypercorn
    fi
    
    print_success "Dependencies checked"
}

# Optimize system settings
optimize_system() {
    print_status "Applying system optimizations..."
    
    # Set environment variables
    export PYTHONUNBUFFERED=1
    export PYTHONDONTWRITEBYTECODE=1
    export TORCH_CUDNN_V8_API_ENABLED=1
    export CUDA_LAUNCH_BLOCKING=0
    export TOKENIZERS_PARALLELISM=false
    export ML_ENABLE=$ML_ENABLE
    
    # Memory optimizations
    export MALLOC_ARENA_MAX=2
    export OMP_NUM_THREADS=1  # Prevent oversubscription
    
    # PyTorch optimizations
    export TORCH_CUDNN_BENCHMARK=1
    
    # Increase file descriptor limits (if possible)
    ulimit -n 65536 2>/dev/null || print_warning "Could not increase file descriptor limit"
    
    print_success "System optimizations applied"
}

# Create necessary directories
setup_directories() {
    print_status "Setting up directories..."
    
    mkdir -p logs
    mkdir -p tmp
    mkdir -p config
    
    print_success "Directories ready"
}

# Health check function
health_check() {
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for API to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "http://$HOST:$PORT/health" > /dev/null 2>&1; then
            print_success "API is healthy and ready!"
            
            # Show API info
            API_INFO=$(curl -s "http://$HOST:$PORT/health" | python -m json.tool 2>/dev/null || echo "API responding")
            echo "$API_INFO"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "API failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Calculate optimal workers
calculate_workers() {
    if [ "$WORKERS" = "auto" ]; then
        if [ -n "$CUDA_VISIBLE_DEVICES" ] || command -v nvidia-smi &> /dev/null; then
            # GPU workload - limit workers to prevent GPU memory issues
            WORKERS=2
            print_status "GPU detected: Using $WORKERS workers"
        else
            # CPU workload
            WORKERS=$(($(nproc) * 2 + 1))
            if [ $WORKERS -gt 8 ]; then
                WORKERS=8
            fi
            print_status "CPU workload: Using $WORKERS workers"
        fi
    fi
}

# Start server function
start_server() {
    print_status "Starting production server..."
    print_status "Configuration:"
    echo "  Host: $HOST"
    echo "  Port: $PORT"
    echo "  Workers: $WORKERS"
    echo "  Server: $SERVER"
    echo "  ML Enabled: $ML_ENABLE"
    echo "  Virtual Env: $VENV_PATH"
    
    calculate_workers
    
    if [ "$SERVER" = "gunicorn" ]; then
        print_status "Starting Gunicorn with $WORKERS workers..."
        exec gunicorn main:app \
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
            --worker-tmp-dir=/tmp \
            --enable-stdio-inheritance \
            --capture-output
            
    elif [ "$SERVER" = "uvicorn" ]; then
        print_status "Starting Uvicorn with $WORKERS workers..."
        exec uvicorn main:app \
            --host "$HOST" \
            --port "$PORT" \
            --workers "$WORKERS" \
            --loop uvloop \
            --http httptools \
            --access-log \
            --log-level info \
            --no-use-colors \
            --backlog 2048 \
            --limit-concurrency 2000 \
            --limit-max-requests 20000 \
            --timeout-keep-alive 10
            
    elif [ "$SERVER" = "hypercorn" ]; then
        print_status "Starting Hypercorn with $WORKERS workers..."
        exec hypercorn main:app \
            --bind "$HOST:$PORT" \
            --workers "$WORKERS" \
            --worker-class asyncio \
            --backlog 2048 \
            --max-requests 10000 \
            --keep-alive-timeout 10 \
            --graceful-timeout 30 \
            --access-log logs/access.log \
            --error-log logs/error.log
            
    elif [ "$SERVER" = "python" ]; then
        print_status "Starting with Python production server..."
        exec python production_server.py \
            --server gunicorn \
            --host "$HOST" \
            --port "$PORT" \
            --workers "$WORKERS"
    else
        print_error "Unknown server: $SERVER"
        print_status "Available servers: gunicorn, uvicorn, hypercorn, python"
        exit 1
    fi
}

# Show usage information
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Production deployment script for Spam Filter API (Non-Docker)"
    echo ""
    echo "Options:"
    echo "  --with-health-check    Perform health check after startup"
    echo "  --setup               Run setup first (install deps, create venv)"
    echo "  --help, -h            Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  HOST                  Host to bind to (default: 0.0.0.0)"
    echo "  PORT                  Port to bind to (default: 8990)"
    echo "  WORKERS               Number of workers (default: auto)"
    echo "  SERVER                Server type: gunicorn|uvicorn|hypercorn|python (default: gunicorn)"
    echo "  ML_ENABLE             Enable ML inference (default: true)"
    echo "  VENV_PATH             Virtual environment path (default: venv)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Start with default settings"
    echo "  $0 --setup                           # Setup environment first, then start"
    echo "  SERVER=uvicorn WORKERS=1 $0          # Start with Uvicorn, 1 worker"
    echo "  ML_ENABLE=false $0                   # Start with ML disabled"
    echo "  HOST=127.0.0.1 PORT=9000 $0         # Custom host and port"
    echo ""
    echo "Quick Setup:"
    echo "  1. ./setup_production.sh             # One-time setup"
    echo "  2. $0                                # Start server"
    echo ""
    echo "Service Management:"
    echo "  sudo systemctl start spam-filter-api    # Start as service"
    echo "  sudo systemctl status spam-filter-api   # Check status"
    echo "  sudo systemctl stop spam-filter-api     # Stop service"
}

# Setup function
run_setup() {
    print_status "Running quick setup..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_PATH" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv "$VENV_PATH"
    fi
    
    # Activate and install dependencies
    source "$VENV_PATH/bin/activate"
    pip install --upgrade pip setuptools wheel
    
    if [ -f "requirements.production.txt" ]; then
        pip install -r requirements.production.txt
    else
        pip install -r requirements.txt
    fi
    
    # Install production servers
    pip install gunicorn hypercorn uvicorn[standard]
    
    print_success "Quick setup completed"
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    # Kill any remaining processes
    pkill -f "gunicorn\|uvicorn\|hypercorn" 2>/dev/null || true
}

# Signal handlers
trap cleanup EXIT
trap 'print_error "Interrupted"; exit 1' INT TERM

# Main execution
main() {
    print_status "Production Spam Filter API (Non-Docker)"
    print_status "======================================="
    
    # Handle setup option
    if [ "$1" = "--setup" ]; then
        run_setup
        shift
    fi
    
    check_venv
    activate_venv
    check_requirements
    check_dependencies
    optimize_system
    setup_directories
    
    # Start server with or without health check
    if [ "$1" = "--with-health-check" ]; then
        start_server &
        SERVER_PID=$!
        
        # Wait a bit for server to start
        sleep 5
        
        # Wait for health check
        if health_check; then
            print_success "Server started successfully (PID: $SERVER_PID)"
            print_status "Server is running. Press Ctrl+C to stop."
            wait $SERVER_PID
        else
            print_error "Server failed to start"
            kill $SERVER_PID 2>/dev/null || true
            exit 1
        fi
    else
        start_server
    fi
}

# Parse command line arguments
case "$1" in
    --help|-h)
        show_usage
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac