#!/bin/bash

# Install PyTorch with CUDA 12.1 support
set -e

echo "🚀 Installing PyTorch with CUDA 12.1"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

VENV_PATH=${VENV_PATH:-".venv"}

# Check and activate venv
if [ ! -d "$VENV_PATH" ]; then
    print_error "Virtual environment not found at $VENV_PATH"
    print_info "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
fi

print_info "Activating virtual environment: $VENV_PATH"
source "$VENV_PATH/bin/activate"

# Upgrade pip first
print_info "Upgrading pip..."
pip install --upgrade pip

# Check CUDA availability
if command -v nvidia-smi &> /dev/null; then
    print_success "NVIDIA GPU detected"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    
    # Install PyTorch with CUDA 12.1
    print_info "Installing PyTorch with CUDA 12.1..."
    pip install torch==2.5.1+cu121 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    
    if [ $? -eq 0 ]; then
        print_success "PyTorch with CUDA 12.1 installed successfully"
    else
        print_warning "CUDA 12.1 installation failed, trying CUDA 11.8..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    fi
else
    print_warning "No NVIDIA GPU detected, installing CPU version"
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install other ML dependencies
print_info "Installing other ML dependencies..."
pip install transformers>=4.30.0 tokenizers>=0.13.0 accelerate safetensors

# Install FastAPI and servers
print_info "Installing FastAPI and servers..."
pip install fastapi uvicorn[standard] gunicorn

# Install other dependencies
print_info "Installing other dependencies..."
pip install numpy pandas requests psutil python-dotenv httpx pydantic

# Verify installation
print_info "Verifying PyTorch installation..."
python -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU count: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        print(f'GPU {i}: {torch.cuda.get_device_name(i)}')
else:
    print('Using CPU')
"

print_info "Verifying other dependencies..."
python -c "
try:
    import transformers
    import fastapi
    import uvicorn
    print('✅ All dependencies installed successfully')
    print(f'Transformers: {transformers.__version__}')
    print(f'FastAPI: {fastapi.__version__}')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
    exit(1)
"

print_success "🎉 Installation completed successfully!"
print_info "You can now run:"
echo "  source $VENV_PATH/bin/activate"
echo "  python main.py"
echo "  # or"
echo "  ./start.sh"