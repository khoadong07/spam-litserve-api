# Production Deployment Guide - Spam Filter API

Hướng dẫn chi tiết để deploy Spam Filter API trong môi trường production **không sử dụng Docker**.

## 🚀 Quick Start

### 1. Setup môi trường (chỉ chạy 1 lần)
```bash
# Cấp quyền thực thi
chmod +x setup_production.sh run_production.sh

# Setup toàn bộ môi trường production
./setup_production.sh
```

### 2. Chạy server
```bash
# Chạy với cấu hình mặc định
./run_production.sh

# Hoặc chạy với health check
./run_production.sh --with-health-check
```

### 3. Kiểm tra API
```bash
# Health check
curl http://localhost/health

# Test API
python3 benchmark.py --url http://localhost
```

## 📋 Các Cách Deploy

### Option 1: Manual Start (Đơn giản nhất)
```bash
# Setup lần đầu
./setup_production.sh

# Chạy server
./run_production.sh
```

### Option 2: Systemd Service (Khuyến nghị cho production)
```bash
# Setup và tạo systemd service
./setup_production.sh

# Quản lý service
sudo systemctl start spam-filter-api
sudo systemctl status spam-filter-api
sudo systemctl enable spam-filter-api  # Auto-start on boot
sudo systemctl stop spam-filter-api
```

### Option 3: Supervisor (Alternative)
```bash
# Setup với supervisor
./setup_production.sh

# Quản lý với supervisor
sudo supervisorctl start spam-filter-api
sudo supervisorctl status spam-filter-api
sudo supervisorctl restart spam-filter-api
sudo supervisorctl stop spam-filter-api
```

## ⚙️ Cấu Hình

### Environment Variables
```bash
# Server configuration
export HOST="0.0.0.0"          # Host to bind
export PORT="8990"             # Port to bind
export WORKERS="auto"          # Number of workers (auto-detect)
export SERVER="gunicorn"       # Server type: gunicorn|uvicorn|hypercorn
export ML_ENABLE="true"        # Enable/disable ML inference

# Advanced settings
export VENV_PATH="venv"        # Virtual environment path
```

### Server Types

#### 1. Gunicorn (Khuyến nghị cho production)
```bash
SERVER=gunicorn ./run_production.sh
```
- **Ưu điểm**: Ổn định, mature, tốt cho production
- **Workers**: Auto-detect (GPU: 2 workers, CPU: 2*cores+1)
- **Concurrency**: 1000 connections/worker

#### 2. Uvicorn (Tốt cho development/single worker)
```bash
SERVER=uvicorn WORKERS=1 ./run_production.sh
```
- **Ưu điểm**: Nhanh, lightweight
- **Workers**: Thường dùng 1 worker cho GPU workload
- **Concurrency**: 2000 connections

#### 3. Hypercorn (HTTP/2 support)
```bash
SERVER=hypercorn ./run_production.sh
```
- **Ưu điểm**: HTTP/2, WebSocket support
- **Workers**: Auto-detect
- **Features**: Advanced protocol support

## 🔧 Performance Tuning

### 1. GPU Optimization
```bash
# Chỉ định GPU cụ thể
export CUDA_VISIBLE_DEVICES=0

# Multiple GPUs
export CUDA_VISIBLE_DEVICES=0,1

# Disable GPU
export CUDA_VISIBLE_DEVICES=""
```

### 2. Worker Configuration
```bash
# GPU workload (khuyến nghị)
WORKERS=2 ./run_production.sh

# CPU workload
WORKERS=8 ./run_production.sh

# Single worker (development)
WORKERS=1 ./run_production.sh
```

### 3. Memory Optimization
```bash
# Giảm memory usage
export MALLOC_ARENA_MAX=2
export OMP_NUM_THREADS=1

# PyTorch optimizations
export TORCH_CUDNN_BENCHMARK=1
export TOKENIZERS_PARALLELISM=false
```

## 📊 Monitoring & Logging

### 1. Logs
```bash
# Application logs
tail -f logs/spam-filter-api.log
tail -f logs/spam-filter-api-error.log

# Access logs (nếu dùng Nginx)
tail -f /var/log/nginx/access.log

# System logs
journalctl -u spam-filter-api -f
```

### 2. Health Monitoring
```bash
# Manual health check
curl http://localhost:8990/health

# Automated monitoring (đã setup trong setup_production.sh)
./monitor.sh

# Crontab monitoring (tự động chạy mỗi 5 phút)
crontab -l | grep monitor.sh
```

### 3. Performance Monitoring
```bash
# System resources
htop
nvidia-smi  # GPU usage

# API performance
python3 benchmark.py --requests 1000 --concurrency 50

# Network connections
netstat -an | grep :8990
```

## 🔒 Security & Production Best Practices

### 1. Nginx Reverse Proxy
- Rate limiting: 100 requests/second
- Security headers
- Load balancing
- SSL termination (thêm certificate)

### 2. System Security
```bash
# Firewall (example)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8990/tcp  # Block direct access to app

# Process limits
ulimit -n 65536  # File descriptors
```

### 3. Log Rotation
- Automatic log rotation (30 days)
- Compression
- Service restart on rotation

## 🚨 Troubleshooting

### 1. Common Issues

#### API không start được
```bash
# Check logs
tail -f logs/spam-filter-api-error.log

# Check port conflicts
netstat -tulpn | grep :8990

# Check virtual environment
source venv/bin/activate
python -c "import torch, transformers, fastapi"
```

#### GPU memory issues
```bash
# Reduce workers
WORKERS=1 ./run_production.sh

# Check GPU memory
nvidia-smi

# Clear GPU cache
python -c "import torch; torch.cuda.empty_cache()"
```

#### High CPU usage
```bash
# Reduce workers
WORKERS=2 ./run_production.sh

# Check system load
htop
iostat -x 1
```

### 2. Performance Issues

#### Slow response times
```bash
# Check model loading
curl -w "@curl-format.txt" http://localhost:8990/health

# Increase workers (if CPU bound)
WORKERS=4 ./run_production.sh

# Check system resources
free -h
df -h
```

#### High memory usage
```bash
# Monitor memory
watch -n 1 'free -h'

# Reduce batch size (modify main.py)
# batch_size=16 instead of 32

# Restart service periodically
sudo systemctl restart spam-filter-api
```

## 📈 Scaling

### 1. Vertical Scaling
```bash
# Increase workers
WORKERS=8 ./run_production.sh

# Use multiple GPUs
export CUDA_VISIBLE_DEVICES=0,1,2,3
```

### 2. Horizontal Scaling
```bash
# Multiple instances with different ports
PORT=8990 ./run_production.sh &
PORT=8991 ./run_production.sh &
PORT=8992 ./run_production.sh &

# Update Nginx config for load balancing
# (xem nginx.conf)
```

### 3. Load Testing
```bash
# Basic load test
python3 benchmark.py --requests 1000 --concurrency 100

# Advanced load test với custom data
python3 benchmark.py \
  --url http://localhost \
  --endpoint both \
  --requests 5000 \
  --concurrency 200 \
  --items 20
```

## 📝 Maintenance

### 1. Regular Tasks
```bash
# Update dependencies
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Clean logs
find logs/ -name "*.log" -mtime +30 -delete

# Restart service
sudo systemctl restart spam-filter-api
```

### 2. Backup
```bash
# Backup configuration
tar -czf backup-$(date +%Y%m%d).tar.gz \
  config/ common/ logs/ requirements.txt main.py

# Backup model cache (if needed)
tar -czf model-cache-$(date +%Y%m%d).tar.gz ~/.cache/huggingface/
```

### 3. Updates
```bash
# Update code
git pull

# Restart service
sudo systemctl restart spam-filter-api

# Verify
curl http://localhost/health
```

## 🎯 Production Checklist

- [ ] ✅ Setup completed với `./setup_production.sh`
- [ ] ✅ Service running với systemd hoặc supervisor
- [ ] ✅ Nginx reverse proxy configured
- [ ] ✅ SSL certificate installed (nếu cần HTTPS)
- [ ] ✅ Monitoring script active
- [ ] ✅ Log rotation configured
- [ ] ✅ Firewall rules applied
- [ ] ✅ Performance tuning applied
- [ ] ✅ Health check passing
- [ ] ✅ Load testing completed
- [ ] ✅ Backup strategy in place

## 📞 Support Commands

```bash
# Quick status check
curl -s http://localhost/health | python -m json.tool

# Performance check
python3 benchmark.py --requests 100 --concurrency 10

# Resource usage
ps aux | grep -E "(gunicorn|uvicorn|hypercorn)"
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv

# Service status
sudo systemctl status spam-filter-api
# hoặc
sudo supervisorctl status spam-filter-api
```

Với setup này, bạn sẽ có một production-ready API server có thể handle hàng nghìn requests đồng thời với performance tối ưu!