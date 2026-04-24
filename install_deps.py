#!/usr/bin/env python3
"""
Smart dependency installer - detects Python version and installs compatible packages
"""

import sys
import subprocess
import os

def get_python_version():
    """Get Python version tuple"""
    return sys.version_info[:2]

def install_pytorch_compatible():
    """Install PyTorch compatible with current Python version"""
    python_version = get_python_version()
    
    print(f"Python version: {python_version[0]}.{python_version[1]}")
    
    if python_version >= (3, 11):
        # Python 3.11+ - can use latest versions
        torch_cmd = [
            sys.executable, "-m", "pip", "install", 
            "torch", "torchvision", "torchaudio", 
            "--index-url", "https://download.pytorch.org/whl/cu121"
        ]
        print("Installing latest PyTorch with CUDA 12.1...")
    elif python_version >= (3, 8):
        # Python 3.8-3.10 - use compatible versions
        torch_cmd = [
            sys.executable, "-m", "pip", "install", 
            "torch>=2.0.0,<2.3.0", 
            "torchvision>=0.15.0,<0.18.0", 
            "torchaudio>=2.0.0,<2.3.0",
            "--index-url", "https://download.pytorch.org/whl/cu118"
        ]
        print("Installing compatible PyTorch with CUDA 11.8...")
    else:
        # Python < 3.8 - use older versions
        torch_cmd = [
            sys.executable, "-m", "pip", "install", 
            "torch==1.13.1", 
            "torchvision==0.14.1", 
            "torchaudio==0.13.1",
            "--index-url", "https://download.pytorch.org/whl/cu117"
        ]
        print("Installing older PyTorch with CUDA 11.7...")
    
    try:
        subprocess.run(torch_cmd, check=True)
        print("✅ PyTorch installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ PyTorch installation failed: {e}")
        # Fallback to CPU version
        print("Trying CPU-only PyTorch...")
        cpu_cmd = [sys.executable, "-m", "pip", "install", "torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cpu"]
        try:
            subprocess.run(cpu_cmd, check=True)
            print("✅ PyTorch CPU installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ PyTorch CPU installation also failed")
            return False

def install_other_deps():
    """Install other dependencies"""
    python_version = get_python_version()
    
    # Base dependencies that work across versions
    base_deps = [
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.20.0",
        "transformers>=4.30.0",
        "numpy>=1.21.0",
        "requests>=2.28.0",
        "psutil>=5.9.0",
        "python-dotenv>=1.0.0",
        "gunicorn>=20.0.0"
    ]
    
    if python_version >= (3, 9):
        # Newer versions for Python 3.9+
        base_deps.extend([
            "pydantic>=2.0.0",
            "httpx>=0.24.0",
            "pandas>=2.0.0"
        ])
    else:
        # Older compatible versions
        base_deps.extend([
            "pydantic>=1.10.0,<2.0.0",
            "httpx>=0.23.0,<0.25.0",
            "pandas>=1.5.0,<2.0.0"
        ])
    
    print("Installing other dependencies...")
    try:
        cmd = [sys.executable, "-m", "pip", "install"] + base_deps
        subprocess.run(cmd, check=True)
        print("✅ Other dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Dependencies installation failed: {e}")
        return False

def main():
    print("🚀 Smart Dependency Installer")
    print("=" * 40)
    
    # Upgrade pip first
    print("Upgrading pip...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        print("✅ Pip upgraded")
    except subprocess.CalledProcessError:
        print("⚠️ Pip upgrade failed, continuing...")
    
    # Install PyTorch
    if not install_pytorch_compatible():
        print("❌ Failed to install PyTorch")
        return False
    
    # Install other dependencies
    if not install_other_deps():
        print("❌ Failed to install other dependencies")
        return False
    
    print("\n✅ All dependencies installed successfully!")
    print("\nYou can now run:")
    print("  python3 main.py")
    print("  python3 run.py")
    print("  ./run_production.sh")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)