#!/bin/bash

# Setup script for production deployment without Docker
set -e

echo "🚀 Setting up Production Environment for Spam Filter API"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root. Consider using a non-root user for security."
    fi
}

# Install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        sudo apt-get update
        sudo apt-get install -y \
            python3 \
            python3-pip \
            python3-venv \
            python3-dev \
            build-essential \
            curl \
            htop \
            nginx \
            supervisor \
            git
        print_success "System dependencies installed (Ubuntu/Debian)"
        
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum update -y
        sudo yum install -y \
            python3 \
            python3-pip \
            python3-devel \
            gcc \
            gcc-c++ \
            curl \
            htop \
            nginx \
            supervisor \
            git
        print_success "System dependencies installed (CentOS/RHEL)"
        
    elif command -v brew &> /dev/null; then
        # macOS
        brew install python3 curl htop nginx supervisor
        print_success "System dependencies installed (macOS)"
        
    else
        print_error "Unsupported package manager. Please install dependencies manually."
        exit 1
    fi
}

# Create virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel
    
    # Install production dependencies
    if [ -f "requirements.production.txt" ]; then
        pip install -r requirements.production.txt
    else
        pip install -r requirements.txt
    fi
    
    # Install additional production servers
    pip install gunicorn hypercorn uvicorn[standard]
    
    print_success "Python dependencies installed"
}

# Setup directories
setup_directories() {
    print_status "Setting up directories..."
    
    mkdir -p logs
    mkdir -p tmp
    mkdir -p config
    
    # Set permissions
    chmod 755 logs tmp config
    
    print_success "Directories created"
}

# Create systemd service
create_systemd_service() {
    print_status "Creating systemd service..."
    
    local service_file="/etc/systemd/system/spam-filter-api.service"
    local current_dir=$(pwd)
    local user=$(whoami)
    
    sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=Spam Filter API Service
After=network.target

[Service]
Type=exec
User=$user
Group=$user
WorkingDirectory=$current_dir
Environment=PATH=$current_dir/venv/bin
Environment=PYTHONPATH=$current_dir
Environment=ML_ENABLE=true
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=$current_dir/venv/bin/python production_server.py --server gunicorn --workers auto
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=append:$current_dir/logs/spam-filter-api.log
StandardError=append:$current_dir/logs/spam-filter-api-error.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$current_dir/logs $current_dir/tmp
ProtectHome=true

# Resource limits
LimitNOFILE=65536
MemoryMax=8G

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable spam-filter-api
    
    print_success "Systemd service created and enabled"
}

# Create supervisor config (alternative to systemd)
create_supervisor_config() {
    print_status "Creating supervisor configuration..."
    
    local config_file="/etc/supervisor/conf.d/spam-filter-api.conf"
    local current_dir=$(pwd)
    local user=$(whoami)
    
    sudo tee "$config_file" > /dev/null << EOF
[program:spam-filter-api]
command=$current_dir/venv/bin/python production_server.py --server gunicorn --workers auto
directory=$current_dir
user=$user
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$current_dir/logs/spam-filter-api.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
environment=PYTHONPATH="$current_dir",ML_ENABLE="true",PYTHONUNBUFFERED="1"
EOF

    sudo supervisorctl reread
    sudo supervisorctl update
    
    print_success "Supervisor configuration created"
}

# Setup nginx reverse proxy (optional)
setup_nginx() {
    read -p "Do you want to setup Nginx reverse proxy? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Skipping Nginx setup - API will run directly on port 8990"
        return 0
    fi
    
    print_status "Setting up Nginx reverse proxy..."
    
    local nginx_config="/etc/nginx/sites-available/spam-filter-api"
    local nginx_enabled="/etc/nginx/sites-enabled/spam-filter-api"
    
    sudo tee "$nginx_config" > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/s;
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8990;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 5s;
        proxy_send_timeout 5s;
        proxy_read_timeout 5s;
    }
    
    # API endpoints
    location / {
        limit_req zone=api burst=200 nodelay;
        
        proxy_pass http://127.0.0.1:8990;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings for ML inference
        proxy_connect_timeout 10s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        
        # Keep-alive
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
    
    # Static files (if any)
    location /static/ {
        alias /path/to/static/files/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    # Enable the site
    sudo ln -sf "$nginx_config" "$nginx_enabled"
    
    # Remove default site if exists
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx configuration
    sudo nginx -t
    
    # Reload nginx
    sudo systemctl reload nginx
    
    print_success "Nginx reverse proxy configured"
}

# Setup log rotation
setup_logrotate() {
    print_status "Setting up log rotation..."
    
    local logrotate_config="/etc/logrotate.d/spam-filter-api"
    local current_dir=$(pwd)
    
    sudo tee "$logrotate_config" > /dev/null << EOF
$current_dir/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $(whoami) $(whoami)
    postrotate
        systemctl reload spam-filter-api || supervisorctl restart spam-filter-api
    endscript
}
EOF

    print_success "Log rotation configured"
}

# Create monitoring script
create_monitoring_script() {
    print_status "Creating monitoring script..."
    
    cat > monitor.sh << 'EOF'
#!/bin/bash

# Simple monitoring script for Spam Filter API
API_URL="http://localhost:8990/health"
LOG_FILE="logs/monitor.log"

check_api() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    if curl -f -s "$API_URL" > /dev/null 2>&1; then
        echo "[$timestamp] API is healthy" >> "$LOG_FILE"
        return 0
    else
        echo "[$timestamp] API is DOWN!" >> "$LOG_FILE"
        # Send alert (customize as needed)
        echo "ALERT: Spam Filter API is down at $timestamp" | logger -t spam-filter-api
        return 1
    fi
}

# Run check
check_api

# If API is down, try to restart
if [ $? -ne 0 ]; then
    echo "Attempting to restart service..."
    if command -v systemctl &> /dev/null; then
        sudo systemctl restart spam-filter-api
    elif command -v supervisorctl &> /dev/null; then
        sudo supervisorctl restart spam-filter-api
    fi
fi
EOF

    chmod +x monitor.sh
    
    # Add to crontab for regular monitoring
    (crontab -l 2>/dev/null; echo "*/5 * * * * $(pwd)/monitor.sh") | crontab -
    
    print_success "Monitoring script created and scheduled"
}

# Performance tuning
apply_performance_tuning() {
    print_status "Applying performance tuning..."
    
    # Increase file descriptor limits
    echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
    echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
    
    # Kernel parameters for high performance
    sudo tee -a /etc/sysctl.conf << EOF

# Spam Filter API Performance Tuning
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 60
net.ipv4.tcp_keepalive_probes = 10
vm.swappiness = 10
EOF

    sudo sysctl -p
    
    print_success "Performance tuning applied"
}

# Main setup function
main() {
    print_status "Production Setup for Spam Filter API"
    print_status "====================================="
    
    check_root
    install_system_deps
    setup_venv
    setup_directories
    
    # Choose service manager
    if command -v systemctl &> /dev/null; then
        create_systemd_service
    elif command -v supervisorctl &> /dev/null; then
        create_supervisor_config
    else
        print_warning "No service manager found. You'll need to start the service manually."
    fi
    
    setup_nginx
    setup_logrotate
    create_monitoring_script
    apply_performance_tuning
    
    print_success "Production setup completed!"
    print_status "Next steps:"
    echo ""
    echo "🚀 Start the API server:"
    echo "   ./run_production.sh"
    echo ""
    echo "🔍 Check API directly:"
    echo "   curl http://localhost:8990/health"
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🌐 Check via Nginx (if configured):"
        echo "   curl http://localhost/health"
        echo ""
    fi
    echo "📊 Run performance test:"
    echo "   python3 benchmark.py --url http://localhost:8990"
    echo ""
    echo "⚙️ Service management (if systemd configured):"
    echo "   sudo systemctl start spam-filter-api"
    echo "   sudo systemctl status spam-filter-api"
    echo "   sudo systemctl stop spam-filter-api"
    echo ""
    echo "📋 View logs:"
    echo "   tail -f logs/spam-filter-api.log"
    echo ""
    echo "🎯 API will be available at: http://localhost:8990"
}

# Parse arguments
case "$1" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Setup production environment for Spam Filter API"
        echo ""
        echo "Options:"
        echo "  --help, -h    Show this help message"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac