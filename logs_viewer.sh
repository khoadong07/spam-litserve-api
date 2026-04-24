#!/bin/bash

# Interactive log viewer
set -e

echo "📄 Spam Filter API Logs Viewer"

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

LOG_FILE="logs/spam-filter-api.log"
ERROR_LOG="logs/spam-filter-error.log"
ACCESS_LOG="logs/access.log"

# Create logs directory if not exists
mkdir -p logs

echo "Available log files:"
echo "1. Main log (spam-filter-api.log)"
echo "2. Error log (spam-filter-error.log)"
echo "3. Access log (access.log)"
echo "4. Live tail main log"
echo "5. Live tail error log"
echo "6. Show all logs summary"
echo "7. Clear all logs"

read -p "Choose option (1-7): " choice

case $choice in
    1)
        if [ -f "$LOG_FILE" ]; then
            print_info "📄 Main log file:"
            cat "$LOG_FILE"
        else
            print_warning "Main log file not found"
        fi
        ;;
    2)
        if [ -f "$ERROR_LOG" ]; then
            print_info "📄 Error log file:"
            cat "$ERROR_LOG"
        else
            print_warning "Error log file not found"
        fi
        ;;
    3)
        if [ -f "$ACCESS_LOG" ]; then
            print_info "📄 Access log file:"
            cat "$ACCESS_LOG"
        else
            print_warning "Access log file not found"
        fi
        ;;
    4)
        if [ -f "$LOG_FILE" ]; then
            print_info "📄 Live tail main log (Ctrl+C to exit):"
            tail -f "$LOG_FILE"
        else
            print_warning "Main log file not found"
        fi
        ;;
    5)
        if [ -f "$ERROR_LOG" ]; then
            print_info "📄 Live tail error log (Ctrl+C to exit):"
            tail -f "$ERROR_LOG"
        else
            print_warning "Error log file not found"
        fi
        ;;
    6)
        print_info "📊 Logs Summary:"
        echo
        
        if [ -f "$LOG_FILE" ]; then
            MAIN_LINES=$(wc -l < "$LOG_FILE")
            MAIN_SIZE=$(du -h "$LOG_FILE" | cut -f1)
            print_success "Main log: $MAIN_LINES lines, $MAIN_SIZE"
            echo "Last 3 lines:"
            tail -n 3 "$LOG_FILE" | sed 's/^/  /'
        else
            print_warning "Main log: Not found"
        fi
        
        echo
        if [ -f "$ERROR_LOG" ]; then
            ERROR_LINES=$(wc -l < "$ERROR_LOG")
            ERROR_SIZE=$(du -h "$ERROR_LOG" | cut -f1)
            if [ "$ERROR_LINES" -gt 0 ]; then
                print_error "Error log: $ERROR_LINES lines, $ERROR_SIZE"
                echo "Last 3 lines:"
                tail -n 3 "$ERROR_LOG" | sed 's/^/  /'
            else
                print_success "Error log: Empty (no errors)"
            fi
        else
            print_warning "Error log: Not found"
        fi
        
        echo
        if [ -f "$ACCESS_LOG" ]; then
            ACCESS_LINES=$(wc -l < "$ACCESS_LOG")
            ACCESS_SIZE=$(du -h "$ACCESS_LOG" | cut -f1)
            print_success "Access log: $ACCESS_LINES lines, $ACCESS_SIZE"
        else
            print_warning "Access log: Not found"
        fi
        ;;
    7)
        read -p "Are you sure you want to clear all logs? (y/N): " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            rm -f logs/*.log
            print_success "✅ All logs cleared"
        else
            print_info "Operation cancelled"
        fi
        ;;
    *)
        print_error "Invalid option"
        exit 1
        ;;
esac