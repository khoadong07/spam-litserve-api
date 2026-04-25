#!/bin/bash

# Health Check Manager Script
# Quản lý health checker với các chức năng: start, stop, status, log

SCRIPT_NAME="test.py"
LOG_FILE="health_check.log"
PID_FILE="health_check.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}📊 Health Check Status${NC}"
    echo "====================="
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "${GREEN}✅ Process is running (PID: $PID)${NC}"
            echo "📝 Log file: $LOG_FILE"
            echo "🔢 PID file: $PID_FILE"
        else
            echo -e "${RED}❌ Process is not running (PID file exists but process dead)${NC}"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${RED}❌ No PID file found - process not running${NC}"
    fi
}

start_health_check() {
    echo -e "${BLUE}🚀 Starting Health Checker...${NC}"
    
    # Check if already running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  Health checker is already running (PID: $PID)${NC}"
            return 1
        else
            echo "🧹 Cleaning up stale PID file..."
            rm -f "$PID_FILE"
        fi
    fi
    
    # Check if Python script exists
    if [ ! -f "$SCRIPT_NAME" ]; then
        echo -e "${RED}❌ Error: $SCRIPT_NAME not found${NC}"
        return 1
    fi
    
    echo "📝 Log file: $LOG_FILE"
    echo "🔢 PID file: $PID_FILE"
    
    # Start the health checker with nohup
    nohup python3 -u "$SCRIPT_NAME" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 2
    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo -e "${GREEN}✅ Health checker started successfully!${NC}"
        echo "📊 PID: $(cat "$PID_FILE")"
        echo ""
        echo "Commands:"
        echo "  View log: tail -f $LOG_FILE"
        echo "  Check status: $0 status"
        echo "  Stop: $0 stop"
    else
        echo -e "${RED}❌ Failed to start health checker${NC}"
        echo "📄 Error log:"
        cat "$LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_health_check() {
    echo -e "${BLUE}🛑 Stopping Health Checker...${NC}"
    
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}⚠️  No PID file found - process may not be running${NC}"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping process (PID: $PID)..."
        kill "$PID"
        
        # Wait for process to stop
        for i in {1..10}; do
            if ! kill -0 "$PID" 2>/dev/null; then
                break
            fi
            sleep 1
        done
        
        # Force kill if still running
        if kill -0 "$PID" 2>/dev/null; then
            echo "Force killing process..."
            kill -9 "$PID"
        fi
        
        rm -f "$PID_FILE"
        echo -e "${GREEN}✅ Health checker stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  Process not running, cleaning up PID file${NC}"
        rm -f "$PID_FILE"
    fi
}

restart_health_check() {
    echo -e "${BLUE}🔄 Restarting Health Checker...${NC}"
    stop_health_check
    sleep 2
    start_health_check
}

show_log() {
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${RED}❌ Log file not found: $LOG_FILE${NC}"
        return 1
    fi
    
    echo -e "${BLUE}📄 Health Check Log${NC}"
    echo "=================="
    echo "File: $LOG_FILE"
    echo "Size: $(wc -c < "$LOG_FILE") bytes"
    echo "Last modified: $(stat -f "%Sm" "$LOG_FILE" 2>/dev/null || stat -c "%y" "$LOG_FILE" 2>/dev/null)"
    echo ""
    
    if [ "$1" = "tail" ]; then
        echo "📝 Following log (Ctrl+C to exit):"
        tail -f "$LOG_FILE"
    else
        echo "📝 Last 20 lines:"
        tail -20 "$LOG_FILE"
    fi
}

show_help() {
    echo -e "${BLUE}Health Check Manager${NC}"
    echo "==================="
    echo ""
    echo "Usage: $0 {start|stop|restart|status|log|tail|help}"
    echo ""
    echo "Commands:"
    echo "  start    - Start health checker in background"
    echo "  stop     - Stop health checker"
    echo "  restart  - Restart health checker"
    echo "  status   - Show current status"
    echo "  log      - Show last 20 lines of log"
    echo "  tail     - Follow log in real-time"
    echo "  help     - Show this help message"
    echo ""
    echo "Files:"
    echo "  Script: $SCRIPT_NAME"
    echo "  Log: $LOG_FILE"
    echo "  PID: $PID_FILE"
}

# Main script logic
case "$1" in
    start)
        start_health_check
        ;;
    stop)
        stop_health_check
        ;;
    restart)
        restart_health_check
        ;;
    status)
        print_status
        ;;
    log)
        show_log
        ;;
    tail)
        show_log tail
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Invalid command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac