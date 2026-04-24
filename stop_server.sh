#!/bin/bash

# Stop background server
set -e

echo "🛑 Stopping Spam Filter API Server"

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

PID_FILE="logs/spam-filter-api.pid"

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    print_warning "PID file not found. Server may not be running."
    print_info "Trying to kill any remaining processes..."
    pkill -f "main.py\|uvicorn main:app\|gunicorn main:app" 2>/dev/null || true
    print_info "Done"
    exit 0
fi

# Read PID
PID=$(cat "$PID_FILE")

# Check if process is running
if ps -p "$PID" > /dev/null 2>&1; then
    print_info "Stopping server (PID: $PID)..."
    
    # Try graceful shutdown first
    kill -TERM "$PID" 2>/dev/null || true
    
    # Wait for graceful shutdown
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            print_success "✅ Server stopped gracefully"
            break
        fi
        echo -n "."
        sleep 1
    done
    echo
    
    # Force kill if still running
    if ps -p "$PID" > /dev/null 2>&1; then
        print_warning "Forcing server shutdown..."
        kill -KILL "$PID" 2>/dev/null || true
        sleep 2
        
        if ps -p "$PID" > /dev/null 2>&1; then
            print_error "❌ Failed to stop server"
            exit 1
        else
            print_success "✅ Server force stopped"
        fi
    fi
else
    print_warning "Process $PID not found. Server may have already stopped."
fi

# Clean up PID file
rm -f "$PID_FILE"

# Kill any remaining processes
print_info "Cleaning up any remaining processes..."
pkill -f "main.py\|uvicorn main:app\|gunicorn main:app" 2>/dev/null || true

print_success "🎉 Server stopped successfully"
print_info "Logs are still available in logs/ directory"