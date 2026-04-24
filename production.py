#!/usr/bin/env python3
"""
Production runner - Xử lý tất cả các vấn đề production
"""

import os
import sys
import subprocess
import multiprocessing
import signal
import time
import json
from pathlib import Path

class ProductionRunner:
    def __init__(self):
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", 8990))
        self.ml_enable = os.getenv("ML_ENABLE", "true").lower() == "true"
        self.process = None
        self.setup_complete = False
        
    def log(self, message, level="INFO"):
        """Simple logging"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def setup_environment(self):
        """Setup all environment variables"""
        self.log("Setting up environment...")
        
        # Fix CUDA multiprocessing
        try:
            multiprocessing.set_start_method('spawn', force=True)
            self.log("Multiprocessing method set to 'spawn'")
        except RuntimeError:
            self.log("Multiprocessing method already set", "WARNING")
        
        # Environment variables
        env_vars = {
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "TORCH_CUDNN_V8_API_ENABLED": "1",
            "CUDA_LAUNCH_BLOCKING": "0",
            "TORCH_MULTIPROCESSING_SHARING_STRATEGY": "file_system",
            "MALLOC_ARENA_MAX": "2",
            "OMP_NUM_THREADS": "1",
            "ML_ENABLE": str(self.ml_enable).lower()
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value
        
        self.log("Environment variables configured")
    
    def check_dependencies(self):
        """Check and install dependencies if needed"""
        self.log("Checking dependencies...")
        
        required_packages = [
            ("torch", "PyTorch"),
            ("transformers", "Transformers"),
            ("fastapi", "FastAPI"),
            ("uvicorn", "Uvicorn")
        ]
        
        missing = []
        for package, name in required_packages:
            try:
                __import__(package)
                self.log(f"✓ {name} available")
            except ImportError:
                missing.append(package)
                self.log(f"✗ {name} missing", "WARNING")
        
        if missing:
            self.log("Installing missing dependencies...")
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", 
                    "-r", "requirements.txt"
                ], check=True, capture_output=True)
                self.log("Dependencies installed successfully")
            except subprocess.CalledProcessError as e:
                self.log(f"Failed to install dependencies: {e}", "ERROR")
                return False
        
        return True
    
    def check_gpu(self):
        """Check GPU availability"""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                for i in range(gpu_count):
                    gpu_name = torch.cuda.get_device_name(i)
                    memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
                    self.log(f"GPU {i}: {gpu_name} ({memory:.1f}GB)")
                return True
            else:
                self.log("No GPU detected, using CPU")
                return False
        except Exception as e:
            self.log(f"GPU check failed: {e}", "WARNING")
            return False
    
    def create_directories(self):
        """Create necessary directories"""
        dirs = ["logs", "tmp", "config"]
        for dir_name in dirs:
            Path(dir_name).mkdir(exist_ok=True)
        self.log("Directories created")
    
    def health_check(self, max_attempts=30):
        """Check if API is responding"""
        import requests
        
        url = f"http://{self.host}:{self.port}/health"
        self.log(f"Health checking {url}...")
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    self.log("✓ API is healthy!")
                    self.log(f"Device: {data.get('device', 'unknown')}")
                    self.log(f"Model: {data.get('model', 'unknown')}")
                    return True
            except Exception:
                pass
            
            if attempt == 0:
                self.log("Waiting for API to start...", end="")
            print(".", end="", flush=True)
            time.sleep(2)
        
        print()  # New line
        self.log("Health check failed", "ERROR")
        return False
    
    def start_server(self):
        """Start the production server"""
        self.log(f"Starting server on {self.host}:{self.port}")
        
        # Try different server options
        server_options = [
            self.start_with_main,
            self.start_with_uvicorn,
            self.start_with_gunicorn
        ]
        
        for start_method in server_options:
            try:
                self.process = start_method()
                if self.process:
                    self.log(f"Server started with PID: {self.process.pid}")
                    return True
            except Exception as e:
                self.log(f"Failed to start with {start_method.__name__}: {e}", "WARNING")
                continue
        
        self.log("All server start methods failed", "ERROR")
        return False
    
    def start_with_main(self):
        """Start by running main.py directly"""
        self.log("Starting with main.py...")
        return subprocess.Popen([sys.executable, "main.py"])
    
    def start_with_uvicorn(self):
        """Start with uvicorn command"""
        self.log("Starting with uvicorn...")
        cmd = [
            "uvicorn", "main:app",
            f"--host={self.host}",
            f"--port={self.port}",
            "--workers=1",
            "--loop=uvloop",
            "--http=httptools",
            "--log-level=info",
            "--access-log",
            "--backlog=2048",
            "--limit-concurrency=2000"
        ]
        return subprocess.Popen(cmd)
    
    def start_with_gunicorn(self):
        """Start with gunicorn"""
        self.log("Starting with gunicorn...")
        cmd = [
            "gunicorn", "main:app",
            f"--bind={self.host}:{self.port}",
            "--workers=1",
            "--worker-class=uvicorn.workers.UvicornWorker",
            "--worker-connections=1000",
            "--max-requests=5000",
            "--preload",
            "--timeout=120",
            "--log-level=info"
        ]
        return subprocess.Popen(cmd)
    
    def stop_server(self):
        """Stop the server gracefully"""
        if self.process:
            self.log("Stopping server...")
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
                self.log("Server stopped gracefully")
            except subprocess.TimeoutExpired:
                self.log("Force killing server...")
                self.process.kill()
                self.process.wait()
                self.log("Server force stopped")
        
        # Kill any remaining processes
        try:
            subprocess.run(["pkill", "-f", "main.py"], capture_output=True)
            subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
            subprocess.run(["pkill", "-f", "gunicorn"], capture_output=True)
        except:
            pass
    
    def setup(self):
        """Complete setup process"""
        if self.setup_complete:
            return True
            
        self.log("=== Production Setup ===")
        
        steps = [
            ("Environment setup", self.setup_environment),
            ("Dependencies check", self.check_dependencies),
            ("GPU check", self.check_gpu),
            ("Directories creation", self.create_directories)
        ]
        
        for step_name, step_func in steps:
            self.log(f"Step: {step_name}")
            try:
                result = step_func()
                if result is False:
                    self.log(f"Setup failed at: {step_name}", "ERROR")
                    return False
            except Exception as e:
                self.log(f"Setup error at {step_name}: {e}", "ERROR")
                return False
        
        self.setup_complete = True
        self.log("Setup completed successfully")
        return True
    
    def run(self):
        """Main run method"""
        def signal_handler(signum, frame):
            self.log("Received shutdown signal")
            self.stop_server()
            sys.exit(0)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Setup
            if not self.setup():
                return False
            
            # Start server
            if not self.start_server():
                return False
            
            # Health check
            time.sleep(3)  # Give server time to start
            if not self.health_check():
                self.log("Server failed health check", "ERROR")
                self.stop_server()
                return False
            
            # Success message
            self.log("=== Server Running Successfully ===")
            self.log(f"API URL: http://{self.host}:{self.port}")
            self.log("Endpoints:")
            self.log(f"  - GET  http://{self.host}:{self.port}/health")
            self.log(f"  - POST http://{self.host}:{self.port}/v1/api/infer")
            self.log(f"  - POST http://{self.host}:{self.port}/api/spam")
            self.log("Press Ctrl+C to stop")
            
            # Keep running
            self.process.wait()
            
        except KeyboardInterrupt:
            self.log("Interrupted by user")
        except Exception as e:
            self.log(f"Runtime error: {e}", "ERROR")
        finally:
            self.stop_server()
        
        return True

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("Usage: python3 production.py")
        print("")
        print("Production runner with automatic error handling")
        print("")
        print("Environment Variables:")
        print("  HOST        Host to bind (default: 0.0.0.0)")
        print("  PORT        Port to bind (default: 8990)")
        print("  ML_ENABLE   Enable ML inference (default: true)")
        print("")
        print("Examples:")
        print("  python3 production.py")
        print("  PORT=9000 python3 production.py")
        print("  ML_ENABLE=false python3 production.py")
        print("")
        print("Features:")
        print("  - Automatic dependency installation")
        print("  - CUDA multiprocessing fix")
        print("  - Multiple server fallback options")
        print("  - Health checking")
        print("  - Graceful shutdown")
        return
    
    print("🚀 Production Spam Filter API")
    print("=" * 50)
    
    runner = ProductionRunner()
    success = runner.run()
    
    if success:
        print("✅ Server ran successfully")
    else:
        print("❌ Server failed to run")
        sys.exit(1)

if __name__ == "__main__":
    main()