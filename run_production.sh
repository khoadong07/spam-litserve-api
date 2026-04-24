#!/bin/bash

# Production deployment script for Spam Filter API (CUDA-Safe)
set -e

echo "🚀 Starting Production Spam Filter API (CUDA-Safe)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-8990}
WORKERS=${WORKERS:-"1"}  # Default 1 for GPU safety
SERVER=${SERVER:-"uvicorn"}  # Changed default to uvicorn for better CUDA support
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
        print_warning "Virtual environment not found at $VENV_PATH"
        print_status "Creating virtual environment..."
        python3 -m venv "$VENV_PATH"
        source "$VENV_PATH/bin/activate"
        pip install --upgrade pip
        pip install -r requirements.txt
        pip install gunicorn uvicorn[standard]
        print_success "Virtual environment created and dependencies installed"
    else
        print_success "Virtual environment found at $VENV_PATH"
        source "$VENV_PATH/bin/activate"
    fi
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
        # Force single worker for GPU safety
        if [ "$WORKERS" != "1" ] && [ "$SERVER" != "python" ]; then
            print_warning "GPU detected: Forcing WORKERS=1 for CUDA safety"
            WORKERS=1
        fi
    else
        print_warning "No NVIDIA GPU detected, using CPU"
        # Can use more workers for CPU
        if [ "$WORKERS" = "1" ] && [ "$SERVER" != "python" ]; then
            CPU_CORES=$(nproc)
            WORKERS=$((CPU_CORES > 4 ? 4 : CPU_CORES))
            print_status "CPU workload: Using $WORKERS workers"
        fi
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
    python -c "import torch; print(f'PyTorch: {torch.__version__}')" 2>/dev/null || {
        print_warning "PyTorch not found. Installing dependencies..."
        pip install -r requirements.txt
    }
    
    python -c "import transformers; print(f'Transformers: {transformers.__version__}')" 2>/dev/null || {
        print_warning "Transformers not found. Installing dependencies..."
        pip install -r requirements.txt
    }
    
    python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')" 2>/dev/null || {
        print_warning "FastAPI not found. Installing dependencies..."
        pip install -r requirements.txt
    }
    
    # Check server dependencies
    if [ "$SERVER" = "gunicorn" ]; then
        python -c "import gunicorn" 2>/dev/null || pip install gunicorn
    elif [ "$SERVER" = "uvicorn" ]; then
        python -c "import uvicorn" 2>/dev/null || pip install uvicorn[standard]
    fi
    
    print_success "Dependencies checked"
}

# Optimize system settings (CUDA-safe)
optimize_system() {
    print_status "Applying CUDA-safe system optimizations..."
    
    # Set environment variables for CUDA safety
    export PYTHONUNBUFFERED=1
    export PYTHONDONTWRITEBYTECODE=1
    export ML_ENABLE=$ML_ENABLE
    export TOKENIZERS_PARALLELISM=false
    export TORCH_CUDNN_V8_API_ENABLED=1
    export CUDA_LAUNCH_BLOCKING=0
    export TORCH_MULTIPROCESSING_SHARING_STRATEGY=file_system
    
    # Memory optimizations
    export MALLOC_ARENA_MAX=2
    export OMP_NUM_THREADS=1  # Prevent oversubscription
    
    # PyTorch optimizations
    export TORCH_CUDNN_BENCHMARK=1
    
    # Increase file descriptor limits (if possible)
    ulimit -n 65536 2>/dev/null || print_warning "Could not increase file descriptor limit"
    
    print_success "CUDA-safe system optimizations applied"
    print_status "Multiprocessing will use 'spawn' method for CUDA compatibility"
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
            API_INFO=$(curl -s "http://$HOST:$PORT/health" 2>/dev/null | python -m json.tool 2>/dev/null || echo "API responding")
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

# Start server function (CUDA-safe)
start_server() {
    print_status "Starting CUDA-safe production server..."
    print_status "Configuration:"
    echo "  Host: $HOST"
    echo "  Port: $PORT"
    echo "  Workers: $WORKERS"
    echo "  Server: $SERVER"
    echo "  ML Enabled: $ML_ENABLE"
    echo "  Virtual Env: $VENV_PATH"
    echo "  CUDA Safe: Yes (spawn method)"
    
    case "$SERVER" in
        "gunicorn")
            print_status "Starting Gunicorn with CUDA-safe configuration..."
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
            print_status "Starting Uvicorn with CUDA-safe configuration..."
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
                --limit-max-requests 10000 \
                --timeout-keep-alive 10
            ;;
        "python")
            print_status "Starting with Python (CUDA-safe)..."
            exec python main.py
            ;;
        *)
            print_error "Unknown server: $SERVER"
            print_status "Available servers: gunicorn, uvicorn, python"
            exit 1
            ;;
    esac
}

# Show usage information
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "CUDA-safe production deployment script for Spam Filter API"
    echo ""
    echo "Options:"
    echo "  --with-health-check    Perform health check after startup"
    echo "  --setup               Run setup first (install deps, create venv)"
    echo "  --help, -h            Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  HOST                  Host to bind to (default: 0.0.0.0)"
    echo "  PORT                  Port to bind to (default: 8990)"
    echo "  WORKERS               Number of workers (default: 1 for GPU safety)"
    echo "  SERVER                Server type: gunicorn|uvicorn|python (default: uvicorn)"
    echo "  ML_ENABLE             Enable ML inference (default: true)"
    echo "  VENV_PATH             Virtual environment path (default: venv)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Start with CUDA-safe defaults"
    echo "  $0 --setup                           # Setup environment first, then start"
    echo "  SERVER=python $0                     # Use Python directly (simplest)"
    echo "  WORKERS=2 SERVER=gunicorn $0         # Gunicorn with 2 workers (CPU only)"
    echo "  ML_ENABLE=false $0                   # Start with ML disabled"
    echo "  HOST=127.0.0.1 PORT=9000 $0         # Custom host and port"
    echo ""
    echo "CUDA Safety Features:"
    echo "  - Automatic spawn multiprocessing method"
    echo "  - Single worker default for GPU workloads"
    echo "  - Optimized environment variables"
    echo "  - Memory management optimizations"
    echo ""
    echo "Quick Start:"
    echo "  1. $0 --setup                        # One-time setup"
    echo "  2. $0                                # Start server"
    echo ""
    echo "Simple Alternative:"
    echo "  python3 run.py                       # Ultra-simple runner"
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
    pip install gunicorn uvicorn[standard]
    
    print_success "Quick setup completed"
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    # Kill any remaining processes
    pkill -f "gunicorn\|uvicorn\|main.py" 2>/dev/null || true
}

# Signal handlers
trap cleanup EXIT
trap 'print_error "Interrupted"; exit 1' INT TERM

# Main execution
main() {
    print_status "Production Spam Filter API (CUDA-Safe)"
    print_status "======================================"
    
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
            print_status "🌐 API URL: http://$HOST:$PORT"
            print_status "📋 Available endpoints:"
            echo "   - GET  http://$HOST:$PORT/health"
            echo "   - GET  http://$HOST:$PORT/"
            echo "   - POST http://$HOST:$PORT/v1/api/infer"
            echo "   - POST http://$HOST:$PORT/api/spam"
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