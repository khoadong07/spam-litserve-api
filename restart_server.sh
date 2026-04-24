#!/bin/bash

# Restart background server
set -e

echo "🔄 Restarting Spam Filter API Server"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

print_info "Stopping existing server..."
./stop_server.sh

print_info "Waiting 3 seconds..."
sleep 3

print_info "Starting server..."
./start_background.sh

print_success "🎉 Server restarted successfully"