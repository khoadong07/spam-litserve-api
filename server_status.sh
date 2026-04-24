#!/bin/bash

# Check server status and show logs
set -e

echo "📊 Spam Filter API Server Status"

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
LOG_FILE="logs/spam-filter-api.log"
ERROR_LOG="logs/spam-filter-error.log"

echo "=" * 50

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    print_error "❌ Server not running (no PID file)"
    exit 1
fi

# Read PID
PID=$(cat "$PID_FILE")

# Check if process is running
if ps -p "$PID" > /dev/null 2>&1; then
    print_success "✅ Server is running (PID: $PID)"
    
    # Show process info
    print_info "Process info:"
    ps -p "$PID" -o pid,ppid,cmd,etime,pcpu,pmem
    
    # Check if server is responding
    print_info "Health check:"
    if curl -f -s "http://localhost:8990/health" > /dev/null 2>&1; then
        print_success "✅ Server is healthy and responding"
        
        # Show API info
        API_INFO=$(curl -s "http://localhost:8990/health" 2>/dev/null)
        echo "$API_INFO" | python3 -m json.tool 2>/dev/null || echo "$API_INFO"
    else
        print_error "❌ Server not responding to health check"
    fi
    
else
    print_error "❌ Process $PID not found. Server may have crashed."
    rm -f "$PID_FILE"
fi

echo
print_info "📋 Log files:"
echo "  Main log: $LOG_FILE"
echo "  Error log: $ERROR_LOG"

# Show recent logs
if [ -f "$LOG_FILE" ]; then
    echo
    print_info "📄 Recent logs (last 10 lines):"
    tail -n 10 "$LOG_FILE"
fi

if [ -f "$ERROR_LOG" ] && [ -s "$ERROR_LOG" ]; then
    echo
    print_warning "⚠️ Recent errors (last 5 lines):"
    tail -n 5 "$ERROR_LOG"
fi

echo
print_info "📋 Management commands:"
echo "  View live logs:   tail -f $LOG_FILE"
echo "  View live errors: tail -f $ERROR_LOG"
echo "  Stop server:      ./stop_server.sh"
echo "  Restart server:   ./restart_server.sh"
echo "  Test API:         python3 test_production.py"