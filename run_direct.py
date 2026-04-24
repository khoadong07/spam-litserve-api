#!/usr/bin/env python3
"""
Direct production runner - chạy trực tiếp main.py với tối ưu production
"""

import os
import sys
import multiprocessing

def setup_production_env():
    """Setup environment cho production"""
    # Performance optimizations
    os.environ["PYTHONUNBUFFERED"] = "1"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["TORCH_CUDNN_V8_API_ENABLED"] = "1"
    os.environ["CUDA_LAUNCH_BLOCKING"] = "0"
    os.environ["MALLOC_ARENA_MAX"] = "2"
    os.environ["OMP_NUM_THREADS"] = "1"
    
    # ML settings
    os.environ["ML_ENABLE"] = os.getenv("ML_ENABLE", "true")
    
    print("✅ Production environment configured")

def check_system():
    """Check system resources"""
    cpu_count = multiprocessing.cpu_count()
    print(f"💻 CPU cores: {cpu_count}")
    
    # Check GPU
    try:
        import subprocess
        result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], 
                              capture_output=True, text=True, check=True)
        print(f"🎮 GPU: {result.stdout.strip()}")
    except:
        print("💻 No GPU detected, using CPU")
    
    # Check memory
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if 'MemTotal' in line:
                    mem_total = int(line.split()[1]) // 1024 // 1024  # GB
                    print(f"💾 Memory: {mem_total}GB")
                    break
    except:
        print("💾 Memory info not available")

def main():
    print("🚀 Direct Production Runner for Spam Filter API")
    print("=" * 55)
    
    # Setup
    setup_production_env()
    check_system()
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8990))
    
    print(f"📊 Configuration:")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   ML Enabled: {os.getenv('ML_ENABLE', 'true')}")
    
    # Import and run main
    try:
        print("🔄 Loading main application...")
        
        # Modify main.py uvicorn config for production
        import main
        
        # Override the uvicorn config in main.py
        print("🚀 Starting production server...")
        
        import uvicorn
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            workers=1,  # Single worker for GPU sharing
            loop="uvloop",
            http="httptools",
            access_log=True,
            log_level="info",
            reload=False,
            # Production optimizations
            backlog=2048,
            limit_concurrency=2000,
            limit_max_requests=20000,
            timeout_keep_alive=10,
            timeout_graceful_shutdown=30,
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("Usage: python3 run_direct.py")
        print("")
        print("Direct production runner - chạy main.py với tối ưu production")
        print("")
        print("Environment Variables:")
        print("  HOST        Host to bind (default: 0.0.0.0)")
        print("  PORT        Port to bind (default: 8990)")
        print("  ML_ENABLE   Enable ML inference (default: true)")
        print("")
        print("Examples:")
        print("  python3 run_direct.py")
        print("  PORT=9000 python3 run_direct.py")
        print("  ML_ENABLE=false python3 run_direct.py")
        print("")
        print("Test:")
        print("  curl http://localhost:8990/health")
    else:
        main()