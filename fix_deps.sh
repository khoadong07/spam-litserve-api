#!/bin/bash

# Quick fix for missing dependencies
set -e

echo "🔧 Fixing missing dependencies..."

VENV_PATH=${VENV_PATH:-".venv"}

# Activate venv
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    echo "✅ Activated virtual environment: $VENV_PATH"
else
    echo "❌ Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Install missing packages
echo "📦 Installing accelerate..."
pip install accelerate

echo "📦 Installing other missing packages..."
pip install safetensors huggingface-hub

echo "📦 Ensuring all dependencies are installed..."
pip install transformers fastapi uvicorn[standard] gunicorn

echo "✅ Dependencies fixed!"

# Verify installation
echo "🔍 Verifying installation..."
python -c "
import torch
import transformers
import fastapi
import accelerate
print('✅ All core dependencies available')
print(f'PyTorch: {torch.__version__}')
print(f'Transformers: {transformers.__version__}')
print(f'FastAPI: {fastapi.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
"

echo "🎉 Ready to start server!"
echo "Run: ./start.sh"