#!/bin/bash
set -e

echo "=========================================="
echo "Setting up development environment..."
echo "=========================================="
echo

# Update packages
echo "📦 Updating system packages..."
sudo apt update
sudo apt install -y --no-install-recommends uuid-runtime
echo "✓ System packages updated"
echo

# Source NVM to make it available (using system installation path)
export NVM_DIR="/usr/local/share/nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
    echo "🔧 Loading NVM..."
    \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
    
    # Install Node LTS
    echo "📦 Installing Node.js LTS..."
    nvm install --lts
    echo "✓ Node.js installed"
    echo
fi

# Initialize uv and sync dependencies
echo "🐍 Setting up Python environment with uv..."
if command -v uv &> /dev/null; then
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo "   Creating virtual environment..."
        uv venv .venv
    fi
    
    # Sync dependencies from pyproject.toml
    echo "   Installing dependencies from pyproject.toml..."
    uv pip install -e ".[dev]"
    
    echo "✓ Python environment ready (uv)"
else
    echo "⚠️  uv not found, using pip fallback..."
    python -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    
    # Install from pyproject.toml if exists, otherwise requirements.txt
    if [ -f "pyproject.toml" ]; then
        pip install -e ".[dev]"
    elif [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    
    echo "✓ Python environment ready (pip)"
fi
echo

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env created (please configure with your credentials)"
    echo "   Edit .env with your Azure OpenAI settings"
else
    echo "✓ .env file already exists"
fi
echo

# Make scripts executable
echo "🔧 Setting up scripts..."
chmod +x test_intent_recognizer.sh 2>/dev/null || true
echo "✓ Scripts configured"
echo

# Display environment info
echo "=========================================="
echo "Environment Setup Complete!"
echo "=========================================="
echo
python --version
echo "Virtual environment: .venv/"
if command -v node &> /dev/null; then
    node --version
fi
if command -v az &> /dev/null; then
    az version --output tsv | head -n 1
fi
if command -v terraform &> /dev/null; then
    terraform version | head -n 1
fi
echo

echo "📚 Quick Reference:"
echo "   • Azure OpenAI Setup: docs/AZURE_OPENAI_SETUP.md"
echo "   • Dev Container Guide: .devcontainer/README.md"
echo
echo "⚡ Next steps:"
echo "   1. Configure .env with your Azure OpenAI credentials"
echo "   2. Activate venv: source .venv/bin/activate"
echo "   3. Test: ./test_intent_recognizer.sh"
echo
echo "💡 Tip: Virtual environment auto-activates in new terminals"
echo
echo "=========================================="
