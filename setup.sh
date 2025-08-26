#!/bin/bash

# Voice Chat Assistant Setup Script
echo "🎤 Voice Chat Assistant Setup"
echo "=============================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8+ from https://www.python.org/"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed."
    echo "Please install pip for Python 3."
    exit 1
fi

echo "✅ pip3 found"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if pip3 install -r requirements.txt; then
    echo "✅ Python dependencies installed successfully"
else
    echo "❌ Failed to install Python dependencies"
    echo "You may need to install additional system dependencies:"
    echo "  brew install portaudio  # for PyAudio"
    exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found"
    if [ -f ".env.example" ]; then
        echo "📝 Creating .env from template..."
        cp .env.example .env
        echo "✅ .env file created"
        echo ""
        echo "🔑 IMPORTANT: Edit .env file and add your OpenAI API key:"
        echo "   OPENAI_API_KEY=your_actual_api_key_here"
        echo ""
    else
        echo "❌ No .env.example template found"
        exit 1
    fi
else
    echo "✅ .env file exists"
fi

# Check if Homebrew is installed (for potential PortAudio dependency)
if command -v brew &> /dev/null; then
    echo "✅ Homebrew found"
    
    # Check if PortAudio is installed
    if brew list portaudio &> /dev/null; then
        echo "✅ PortAudio is already installed"
    else
        echo "📦 Installing PortAudio (required for speech recognition)..."
        if brew install portaudio; then
            echo "✅ PortAudio installed successfully"
        else
            echo "⚠️  Failed to install PortAudio. You may need to install it manually."
        fi
    fi
else
    echo "⚠️  Homebrew not found. You may need to install PortAudio manually if you encounter PyAudio issues."
    echo "   Visit: https://brew.sh/ to install Homebrew"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Run the application:"
echo "   • Command line: python3 voice_chat_app.py"
echo "   • GUI version: python3 voice_chat_gui.py"
echo ""
echo "3. Grant microphone permissions when prompted"
echo ""
echo "For troubleshooting, see README.md"
