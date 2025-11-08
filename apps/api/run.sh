#!/bin/bash

# SWE Agent API - Quick Start Script

set -e

echo "🚀 SWE Agent API Setup"
echo "======================"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python $PYTHON_VERSION detected"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env exists, create from example if not
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration"
fi

# Run the application
echo ""
echo "✅ Setup complete!"
echo ""
echo "Starting FastAPI server..."
echo "=========================="
echo "API Docs: http://localhost:8000/docs"
echo "ReDoc: http://localhost:8000/redoc"
echo "Health Check: http://localhost:8000/health"
echo ""

python main.py
