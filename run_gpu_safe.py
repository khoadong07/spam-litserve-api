#!/usr/bin/env python3
"""
GPU-safe production runner - Fix CUDA multiprocessing issues
"""

import os
import sys
import multiprocessing

def setup_cuda_environment():
    """Setup CUDA environment for multiprocessing"""
    # Fix CUDA multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    
    # CUDA environment variables
    os.environ["CUDA_LAUNCH_BLOCKING"] = "0"
    os.environ["TORCH_CUDNN_V8_API_ENABLED"] = "1"
    os.environ["CUDA_VISIBLE_DEVICES"] = os.getenv("CUDA_VISIBLE_DEVICES", "0")
    
    # PyTorch multiprocessing settings
    os.environ["TORCH_MULTIPROCESSING_SHARING_STRATEGY"] = "file_system"
    
    # Other optimizations
    os.environ["PYTHONUNBUFFERED"] = "1"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["ML_ENABLE"] = os.getenv("ML_ENABLE", "true")
    
    print("✅ CUDA environment configured for multiprocessing")

def run_single_worker():
    """Run with single worker (recommended for GPU)"""
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8990))
    
    print(f"🚀 Starting GPU-safe server on {host}:{port}")
    print("📊 Configuration:")
    print(f"   Workers: 1 (GPU-safe)")
    print(f"   Multiprocessing: spawn")
    print(f"   CUDA Device: {os.getenv('CUDA_VISIBLE_DEVICES', '0')}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=1,  # Single worker for GPU safety
        loop="uvloop",
        http="httptools",
        access_log=True,
        log_level="info",
        reload=False,
        # High performance settings
        backlog=2048,
        limit_concurrency=2000,
        limit_max_requests=20000,
        timeout_keep_alive=10,
        timeout_graceful_shutdown=30,
    )

def run_gunicorn_safe():
    """Run with Gunicorn using spawn method"""
    import subprocess
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8990))
    workers = int(os.getenv("WORKERS", 1))  # Default 1 for GPU
    
    print(f"🚀 Starting Gunicorn with spawn method")
    print(f"📊 Configuration:")
    print(f"   Workers: {workers}")
    print(f"   Multiprocessing: spawn")
    
    cmd = [
        "gunicorn", "main:app",
        f"--bind={host}:{port}",
        f"--workers={workers}",
        "--worker-class=uvicorn.workers.UvicornWorker",
        "--worker-connections=1000",
        "--max-requests=5000",  # Lower for GPU memory management
        "--max-requests-jitter=500",
        "--preload",  # Important for GPU model sharing
        "--timeout=120",
        "--keep-alive=5",
        "--log-level=info",
        # Use spawn method for CUDA compatibility
        "--worker-tmp-dir=/tmp",
    ]
    
    # Set environment for subprocess
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    subprocess.run(cmd, env=env)

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("Usage: python3 run_gpu_safe.py [OPTIONS]")
        print("")
        print("GPU-safe production runner with CUDA multiprocessing fix")
        print("")
        print("Options:")
        print("  --gunicorn    Use Gunicorn instead of Uvicorn")
        print("  --help, -h    Show this help")
        print("")
        print("Environment Variables:")
        print("  HOST                  Host to bind (default: 0.0.0.0)")
        print("  PORT                  Port to bind (default: 8990)")
        print("  WORKERS               Number of workers for Gunicorn (default: 1)")
        print("  CUDA_VISIBLE_DEVICES  GPU devices (default: 0)")
        print("  ML_ENABLE             Enable ML inference (default: true)")
        print("")
        print("Examples:")
        print("  python3 run_gpu_safe.py")
        print("  python3 run_gpu_safe.py --gunicorn")
        print("  WORKERS=2 python3 run_gpu_safe.py --gunicorn")
        print("  CUDA_VISIBLE_DEVICES=0,1 python3 run_gpu_safe.py")
        return
    
    print("🎮 GPU-Safe Production Runner")
    print("=" * 40)
    
    # Setup CUDA environment
    setup_cuda_environment()
    
    # Check GPU availability
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                print(f"🎮 GPU {i}: {gpu_name}")
        else:
            print("💻 No GPU detected, using CPU")
    except ImportError:
        print("⚠️ PyTorch not available")
    
    # Choose server type
    if "--gunicorn" in sys.argv:
        run_gunicorn_safe()
    else:
        run_single_worker()

if __name__ == "__main__":
    main()