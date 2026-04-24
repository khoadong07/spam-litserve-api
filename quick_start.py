#!/usr/bin/env python3
"""
Quick start script for production deployment
Chạy trực tiếp qua port 8990 với tối ưu cao nhất
"""

import os
import sys
import subprocess
import multiprocessing
import signal
import time
import requests
from pathlib import Path

class ProductionServer:
    def __init__(self):
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", 8990))
        self.workers = os.getenv("WORKERS", "auto")
        self.server_type = os.getenv("SERVER", "gunicorn")
        self.ml_enable = os.getenv("ML_ENABLE", "true")
        self.process = None
        
    def setup_environment(self):
        """Setup environment variables for optimal performance"""
        env_vars = {
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "ML_ENABLE": self.ml_enable,
            "TOKENIZERS_PARALLELISM": "false",
            "TORCH_CUDNN_V8_API_ENABLED": "1",
            "CUDA_LAUNCH_BLOCKING": "0",
            "MALLOC_ARENA_MAX": "2",
            "OMP_NUM_THREADS": "1"
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value
            
        print(f"✅ Environment variables set")
    
    def calculate_workers(self):
        """Calculate optimal number of workers"""
        if self.workers == "auto":
            # Check for GPU
            try:
                subprocess.run(["nvidia-smi"], capture_output=True, check=True)
                self.workers = 2  # GPU workload
                print(f"🎮 GPU detected: Using {self.workers} workers")
            except (subprocess.CalledProcessError, FileNotFoundError):
                # CPU workload
                cpu_count = multiprocessing.cpu_count()
                self.workers = min(cpu_count * 2 + 1, 8)
                print(f"💻 CPU workload: Using {self.workers} workers")
        else:
            self.workers = int(self.workers)
            
    def check_dependencies(self):
        """Check if required packages are installed"""
        try:
            import torch
            import transformers
            import fastapi
            import uvicorn
            print(f"✅ Dependencies OK - PyTorch: {torch.__version__}")
            return True
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            print("Installing requirements...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            return True
    
    def create_directories(self):
        """Create necessary directories"""
        Path("logs").mkdir(exist_ok=True)
        Path("tmp").mkdir(exist_ok=True)
        print("✅ Directories created")
    
    def start_gunicorn(self):
        """Start with Gunicorn"""
        cmd = [
            "gunicorn", "main:app",
            f"--bind={self.host}:{self.port}",
            f"--workers={self.workers}",
            "--worker-class=uvicorn.workers.UvicornWorker",
            "--worker-connections=1000",
            "--max-requests=10000",
            "--max-requests-jitter=1000",
            "--preload",
            "--timeout=120",
            "--keep-alive=5",
            "--access-logfile=logs/access.log",
            "--error-logfile=logs/error.log",
            "--log-level=info",
            "--capture-output"
        ]
        
        print(f"🚀 Starting Gunicorn with {self.workers} workers...")
        return subprocess.Popen(cmd)
    
    def start_uvicorn(self):
        """Start with Uvicorn"""
        cmd = [
            "uvicorn", "main:app",
            f"--host={self.host}",
            f"--port={self.port}",
            f"--workers={self.workers}",
            "--loop=uvloop",
            "--http=httptools",
            "--access-log",
            "--log-level=info",
            "--backlog=2048",
            "--limit-concurrency=2000"
        ]
        
        print(f"🚀 Starting Uvicorn with {self.workers} workers...")
        return subprocess.Popen(cmd)
    
    def start_python(self):
        """Start with Python directly"""
        print("🚀 Starting with Python...")
        return subprocess.Popen([sys.executable, "main.py"])
    
    def health_check(self, max_attempts=30):
        """Check if API is healthy"""
        url = f"http://{self.host}:{self.port}/health"
        
        print("🔍 Waiting for API to be ready...")
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print("✅ API is healthy and ready!")
                    print(f"🌐 API URL: http://{self.host}:{self.port}")
                    print("📋 Available endpoints:")
                    print(f"   - GET  http://{self.host}:{self.port}/health")
                    print(f"   - GET  http://{self.host}:{self.port}/")
                    print(f"   - POST http://{self.host}:{self.port}/v1/api/infer")
                    print(f"   - POST http://{self.host}:{self.port}/api/spam")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            print(".", end="", flush=True)
            time.sleep(2)
        
        print(f"\n❌ API failed to start within {max_attempts * 2} seconds")
        return False
    
    def start(self):
        """Start the production server"""
        print("🚀 Starting Production Spam Filter API")
        print("=" * 50)
        
        # Setup
        self.setup_environment()
        self.check_dependencies()
        self.create_directories()
        self.calculate_workers()
        
        print(f"📊 Configuration:")
        print(f"   Host: {self.host}")
        print(f"   Port: {self.port}")
        print(f"   Workers: {self.workers}")
        print(f"   Server: {self.server_type}")
        print(f"   ML Enabled: {self.ml_enable}")
        
        # Start server
        try:
            if self.server_type == "gunicorn":
                self.process = self.start_gunicorn()
            elif self.server_type == "uvicorn":
                self.process = self.start_uvicorn()
            elif self.server_type == "python":
                self.process = self.start_python()
            else:
                print(f"❌ Unknown server type: {self.server_type}")
                return False
            
            # Wait a bit for server to start
            time.sleep(3)
            
            # Health check
            if self.health_check():
                print("🎉 Server started successfully!")
                print("Press Ctrl+C to stop the server")
                return True
            else:
                print("❌ Server failed to start")
                self.stop()
                return False
                
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False
    
    def stop(self):
        """Stop the server"""
        if self.process:
            print("\n🛑 Stopping server...")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
            print("✅ Server stopped")
    
    def run(self):
        """Run the server with signal handling"""
        def signal_handler(signum, frame):
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        if self.start():
            try:
                self.process.wait()
            except KeyboardInterrupt:
                pass
            finally:
                self.stop()

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("Usage: python3 quick_start.py")
        print("")
        print("Environment Variables:")
        print("  HOST        Host to bind (default: 0.0.0.0)")
        print("  PORT        Port to bind (default: 8990)")
        print("  WORKERS     Number of workers (default: auto)")
        print("  SERVER      Server type: gunicorn|uvicorn|python (default: gunicorn)")
        print("  ML_ENABLE   Enable ML inference (default: true)")
        print("")
        print("Examples:")
        print("  python3 quick_start.py")
        print("  PORT=9000 python3 quick_start.py")
        print("  SERVER=uvicorn WORKERS=1 python3 quick_start.py")
        print("  ML_ENABLE=false python3 quick_start.py")
        print("")
        print("Quick test:")
        print("  curl http://localhost:8990/health")
        return
    
    server = ProductionServer()
    server.run()

if __name__ == "__main__":
    main()