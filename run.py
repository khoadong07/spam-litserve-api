#!/usr/bin/env python3
"""
Simple production runner - One command to rule them all
"""

import os
import sys
import subprocess
import multiprocessing

def main():
    print("🚀 Starting Spam Filter API Production Server")
    print("=" * 55)
    
    # Fix CUDA multiprocessing first
    try:
        multiprocessing.set_start_method('spawn', force=True)
        print("✅ CUDA multiprocessing fixed")
    except RuntimeError:
        print("⚠️ Multiprocessing method already set")
    
    # Set essential environment variables
    os.environ["PYTHONUNBUFFERED"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["TORCH_MULTIPROCESSING_SHARING_STRATEGY"] = "file_system"
    os.environ["ML_ENABLE"] = os.getenv("ML_ENABLE", "true")
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "8990")
    
    print(f"📊 Configuration:")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   ML Enabled: {os.environ['ML_ENABLE']}")
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Try to run the server
    print("🚀 Starting server...")
    
    try:
        # Method 1: Direct main.py
        print("Trying main.py...")
        subprocess.run([sys.executable, "main.py"], check=True)
    except (subprocess.CalledProcessError, KeyboardInterrupt):
        print("\n🛑 Server stopped")
    except FileNotFoundError:
        print("❌ main.py not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("Usage: python3 run.py")
        print("")
        print("Simple production runner")
        print("")
        print("Environment Variables:")
        print("  HOST        Host (default: 0.0.0.0)")
        print("  PORT        Port (default: 8990)")
        print("  ML_ENABLE   Enable ML (default: true)")
        print("")
        print("Examples:")
        print("  python3 run.py")
        print("  PORT=9000 python3 run.py")
    else:
        main()