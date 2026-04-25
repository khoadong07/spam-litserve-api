#!/bin/bash

# Health Check Manager Script - All in one bash
# Tích hợp health checker và quản lý process

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "Loading configuration from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    echo "Warning: .env file not found, using default values"
fi

# Configuration (with fallback defaults)
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"
URLS=(
    "${URL:-http://localhost:8990/health}"
)
CHECK_INTERVAL="${CHECK_INTERVAL:-60}"
REQUEST_TIMEOUT="${REQUEST_TIMEOUT:-10}"

# Validate required environment variables
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env file"
    echo "Create .env file with:"
    echo "TELEGRAM_BOT_TOKEN=your_bot_token"
    echo "TELEGRAM_CHAT_ID=your_chat_id"
    echo "URL=http://localhost:8990/health"
    echo "CHECK_INTERVAL=60"
    echo "REQUEST_TIMEOUT=10"
    exit 1
fi

LOG_FILE="health_check.log"
PID_FILE="health_check.pid"
STATUS_FILE="health_status.tmp"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Initialize status file
init_status_file() {
    > "$STATUS_FILE"
    for url in "${URLS[@]}"; do
        echo "$url:unknown" >> "$STATUS_FILE"
    done
}

# Get current time in GMT+7
get_time_gmt7() {
    TZ='Asia/Bangkok' date '+%Y-%m-%d %H:%M:%S'
}

# Send message to Telegram
send_telegram() {
    local message="$1"
    local url="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage"
    
    echo "[$(get_time_gmt7)] [Telegram] Sending message: ${message:0:100}..." >> "$LOG_FILE"
    
    response=$(curl -s -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "{\"chat_id\":\"$TELEGRAM_CHAT_ID\",\"text\":\"$message\",\"parse_mode\":\"HTML\"}" \
        --connect-timeout 10 --max-time 10)
    
    if echo "$response" | grep -q '"ok":true'; then
        echo "[$(get_time_gmt7)] [Telegram] ✅ Message sent successfully" >> "$LOG_FILE"
    else
        echo "[$(get_time_gmt7)] [Telegram] ❌ Failed to send message: $response" >> "$LOG_FILE"
    fi
}

# Check health of a URL
check_health() {
    local url="$1"
    local response
    local http_code
    
    response=$(curl -s -w "%{http_code}" --connect-timeout "$REQUEST_TIMEOUT" --max-time "$REQUEST_TIMEOUT" "$url" 2>/dev/null)
    http_code="${response: -3}"
    
    if [ "$http_code" = "200" ]; then
        echo "true:$http_code"
    else
        echo "false:$http_code"
    fi
}

# Get last status for URL
get_last_status() {
    local url="$1"
    grep "^$url:" "$STATUS_FILE" 2>/dev/null | cut -d: -f2 || echo "unknown"
}

# Update status for URL
update_status() {
    local url="$1"
    local status="$2"
    
    if [ -f "$STATUS_FILE" ]; then
        sed -i.bak "s|^$url:.*|$url:$status|" "$STATUS_FILE" 2>/dev/null || {
            # Fallback for systems without sed -i
            grep -v "^$url:" "$STATUS_FILE" > "${STATUS_FILE}.tmp" 2>/dev/null || true
            echo "$url:$status" >> "${STATUS_FILE}.tmp"
            mv "${STATUS_FILE}.tmp" "$STATUS_FILE"
        }
    fi
}

# Manual health check
manual_health_check() {
    local now=$(get_time_gmt7)
    local results=()
    
    echo "[$(get_time_gmt7)] [Manual Check] Received check command from user" >> "$LOG_FILE"
    
    for url in "${URLS[@]}"; do
        local result=$(check_health "$url")
        local ok=$(echo "$result" | cut -d: -f1)
        local status_code=$(echo "$result" | cut -d: -f2)
        
        if [ "$ok" = "true" ]; then
            results+=("✅ $url")
        else
            results+=("❌ $url (Status: $status_code)")
        fi
    done
    
    local message="🔍 <b>MANUAL HEALTH CHECK</b>
Time: $now

$(printf '%s\n' "${results[@]}")"
    
    send_telegram "$message"
}

# Listen for Telegram messages
telegram_listener() {
    local last_update_id=0
    local url="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates"
    
    while true; do
        local response=$(curl -s -G "$url" \
            --data-urlencode "offset=$((last_update_id + 1))" \
            --data-urlencode "timeout=5" \
            --connect-timeout 10 --max-time 15 2>/dev/null)
        
        if echo "$response" | grep -q '"ok":true'; then
            local updates=$(echo "$response" | grep -o '"update_id":[0-9]*' | cut -d: -f2)
            
            for update_id in $updates; do
                if [ "$update_id" -gt "$last_update_id" ]; then
                    last_update_id=$update_id
                    
                    # Extract message text and chat_id
                    local message_data=$(echo "$response" | grep -A 20 "\"update_id\":$update_id")
                    local chat_id=$(echo "$message_data" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
                    local text=$(echo "$message_data" | grep -o '"text":"[^"]*"' | cut -d'"' -f4)
                    
                    if [ "$chat_id" = "$TELEGRAM_CHAT_ID" ] && [ "$text" = "check" ]; then
                        manual_health_check
                    fi
                fi
            done
        fi
        
        sleep 2
    done
}

# Main health check loop
health_check_loop() {
    local now=$(get_time_gmt7)
    
    # Send startup message
    local startup_message="🚀 <b>SPAM AI HEALTH CHECKER STARTED</b>
Time: $now
Monitoring URL: <code>${URLS[0]}</code>
Check interval: ${CHECK_INTERVAL}s

💡 Send 'check' to get manual status"
    
    send_telegram "$startup_message"
    
    # Start Telegram listener in background
    telegram_listener &
    local telegram_pid=$!
    
    echo "[$(get_time_gmt7)] 🚀 Health checker started..." >> "$LOG_FILE"
    echo "[$(get_time_gmt7)] [Telegram Listener] Started (PID: $telegram_pid)" >> "$LOG_FILE"
    
    while true; do
        for url in "${URLS[@]}"; do
            local now=$(get_time_gmt7)
            local result=$(check_health "$url")
            local ok=$(echo "$result" | cut -d: -f1)
            local status_code=$(echo "$result" | cut -d: -f2)
            local last_status=$(get_last_status "$url")
            
            if [ "$ok" = "true" ]; then
                echo "[$now] ✅ OK $url" >> "$LOG_FILE"
                
                # Send recovery message if was previously failed
                if [ "$last_status" = "false" ]; then
                    echo "[$now] [DEBUG] Sending recovery message for $url" >> "$LOG_FILE"
                    local recovery_message="✅ <b>API RECOVERED</b>
URL: <code>$url</code>
Time: $now"
                    send_telegram "$recovery_message"
                fi
                
                update_status "$url" "true"
                
            else
                echo "[$now] ❌ ERROR $url | status=$status_code" >> "$LOG_FILE"
                
                # Send error message if was previously OK
                if [ "$last_status" = "true" ]; then
                    echo "[$now] [DEBUG] Sending error message for $url" >> "$LOG_FILE"
                    local error_message="🚨 <b>SPAM AI HEALTH CHECK FAILED</b>
URL: <code>$url</code>
Status: <code>$status_code</code>
Time: $now"
                    send_telegram "$error_message"
                fi
                
                update_status "$url" "false"
            fi
        done
        
        sleep "$CHECK_INTERVAL"
    done
}

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
    
    echo "📝 Log file: $LOG_FILE"
    echo "🔢 PID file: $PID_FILE"
    
    # Initialize status file
    init_status_file
    
    # Start the health checker function in background
    health_check_loop >> "$LOG_FILE" 2>&1 &
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
        
        # Kill the main process and all its children (including telegram listener)
        pkill -P "$PID" 2>/dev/null || true
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
            pkill -9 -P "$PID" 2>/dev/null || true
        fi
        
        rm -f "$PID_FILE" "$STATUS_FILE"
        echo -e "${GREEN}✅ Health checker stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  Process not running, cleaning up files${NC}"
        rm -f "$PID_FILE" "$STATUS_FILE"
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
    echo -e "${BLUE}Health Check Manager - All in One Bash${NC}"
    echo "======================================"
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
    echo "Features:"
    echo "  • Monitor multiple URLs with configurable interval"
    echo "  • Telegram notifications for failures and recoveries"
    echo "  • Manual check via Telegram (send 'check' message)"
    echo "  • GMT+7 timezone support"
    echo "  • Smart status tracking (no spam notifications)"
    echo ""
    echo "Files:"
    echo "  Log: $LOG_FILE"
    echo "  PID: $PID_FILE"
    echo "  Status: $STATUS_FILE"
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