#!/usr/bin/env python3
"""
Production-optimized server for Spam Filter API
Supports multiple deployment strategies for maximum throughput
"""

import os
import sys
import multiprocessing
import argparse
from pathlib import Path

def get_optimal_workers():
    """Calculate optimal number of workers based on system resources"""
    cpu_count = multiprocessing.cpu_count()
    
    # For GPU workloads, typically 1 worker per GPU is optimal
    # For CPU workloads, use 2 * CPU cores + 1
    if os.getenv("CUDA_VISIBLE_DEVICES"):
        gpu_count = len(os.getenv("CUDA_VISIBLE_DEVICES", "0").split(","))
        return min(gpu_count, 2)  # Max 2 workers for GPU sharing
    else:
        return min(cpu_count * 2 + 1, 8)  # Cap at 8 workers

def run_gunicorn_server(host="0.0.0.0", port=8990, workers=None):
    """Run with Gunicorn for production deployment"""
    try:
        import gunicorn.app.wsgiapp as wsgi
    except ImportError:
        print("❌ Gunicorn not installed. Install with: pip install gunicorn")
        return False
    
    if workers is None:
        # For GPU workloads, use fewer workers to avoid CUDA issues
        workers = 1 if os.getenv("CUDA_VISIBLE_DEVICES") else get_optimal_workers()
    
    # Gunicorn configuration for high performance with CUDA safety
    gunicorn_config = [
        "main:app",
        f"--bind={host}:{port}",
        f"--workers={workers}",
        "--worker-class=uvicorn.workers.UvicornWorker",
        "--worker-connections=1000",
        "--max-requests=5000",  # Lower for GPU memory management
        "--max-requests-jitter=500",
        "--preload",  # Preload app for memory sharing
        "--timeout=120",
        "--keep-alive=5",
        "--access-logfile=-",
        "--error-logfile=-",
        "--log-level=info",
        # CUDA-safe settings
        "--worker-tmp-dir=/tmp",
    ]
    
    print(f"🚀 Starting Gunicorn server with {workers} workers...")
    print(f"   Host: {host}:{port}")
    print(f"   Worker class: uvicorn.workers.UvicornWorker")
    print(f"   CUDA-safe configuration enabled")
    
    # Set multiprocessing method before starting
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    
    os.execvp("gunicorn", ["gunicorn"] + gunicorn_config)

def run_uvicorn_server(host="0.0.0.0", port=8990, workers=None):
    """Run with Uvicorn for development/single-worker deployment"""
    import uvicorn
    
    if workers is None:
        workers = 1  # Uvicorn single worker for GPU sharing
    
    print(f"🚀 Starting Uvicorn server...")
    print(f"   Host: {host}:{port}")
    print(f"   Workers: {workers}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        loop="uvloop",
        http="httptools",
        access_log=False,
        log_level="info",
        reload=False,
        # High-performance settings
        backlog=2048,
        limit_concurrency=2000,
        limit_max_requests=20000,
        timeout_keep_alive=10,
        timeout_graceful_shutdown=30,
    )

def run_hypercorn_server(host="0.0.0.0", port=8990, workers=None):
    """Run with Hypercorn for HTTP/2 and WebSocket support"""
    try:
        import hypercorn.app
        from hypercorn.config import Config
    except ImportError:
        print("❌ Hypercorn not installed. Install with: pip install hypercorn")
        return False
    
    if workers is None:
        workers = get_optimal_workers()
    
    config = Config()
    config.bind = [f"{host}:{port}"]
    config.workers = workers
    config.worker_class = "asyncio"
    config.backlog = 2048
    config.max_requests = 10000
    config.keep_alive_timeout = 10
    config.graceful_timeout = 30
    config.access_log_format = '%(h)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
    
    print(f"🚀 Starting Hypercorn server with {workers} workers...")
    print(f"   Host: {host}:{port}")
    print(f"   HTTP/2 and WebSocket support enabled")
    
    import asyncio
    asyncio.run(hypercorn.app.serve(config, "main:app"))

def optimize_system():
    """Apply system-level optimizations"""
    print("🔧 Applying system optimizations...")
    
    # Set multiprocessing method for CUDA compatibility
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    
    # Set environment variables for optimal performance
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    
    # PyTorch optimizations
    os.environ.setdefault("TORCH_CUDNN_V8_API_ENABLED", "1")
    os.environ.setdefault("CUDA_LAUNCH_BLOCKING", "0")
    os.environ.setdefault("TORCH_MULTIPROCESSING_SHARING_STRATEGY", "file_system")
    
    # Memory optimizations
    os.environ.setdefault("MALLOC_ARENA_MAX", "2")
    
    # Disable tokenizers parallelism warnings
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    
    print("✅ System optimizations applied (CUDA-safe)")
    print("✅ Multiprocessing method set to 'spawn'")

def main():
    parser = argparse.ArgumentParser(description="Production Spam Filter Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8990, help="Port to bind to")
    parser.add_argument("--workers", type=int, help="Number of workers (auto-detect if not specified)")
    parser.add_argument("--server", choices=["uvicorn", "gunicorn", "hypercorn"], 
                       default="gunicorn", help="Server to use")
    parser.add_argument("--no-optimize", action="store_true", help="Skip system optimizations")
    
    args = parser.parse_args()
    
    if not args.no_optimize:
        optimize_system()
    
    print(f"🎯 Production Spam Filter API Server")
    print(f"   Server: {args.server}")
    print(f"   Host: {args.host}:{args.port}")
    print(f"   Workers: {args.workers or 'auto-detect'}")
    print(f"   CPU cores: {multiprocessing.cpu_count()}")
    print(f"   GPU available: {'Yes' if os.getenv('CUDA_VISIBLE_DEVICES') else 'No'}")
    
    if args.server == "gunicorn":
        run_gunicorn_server(args.host, args.port, args.workers)
    elif args.server == "uvicorn":
        run_uvicorn_server(args.host, args.port, args.workers)
    elif args.server == "hypercorn":
        run_hypercorn_server(args.host, args.port, args.workers)

if __name__ == "__main__":
    main()