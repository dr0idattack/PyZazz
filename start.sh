#!/bin/bash

# PyZazz startup script

# Function to check if setup is needed
needs_setup() {
    # Check if virtual environment exists and has required packages
    if [ ! -d "venv" ]; then
        return 0  # True - needs setup
    fi
    
    # Check if requirements are installed
    source venv/bin/activate 2>/dev/null || return 0
    python3 -c "import sounddevice, numpy, serial" 2>/dev/null || return 0
    
    return 1  # False - no setup needed
}

# Quick launch function
quick_launch() {
    echo "PyZazz - Quick Launch"
    echo "====================="
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Create directories if needed
    mkdir -p config videos
    
    # Set library path for libftdi (ARM64 Homebrew)
    export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
    
    # Start the application
    echo "Starting application..."
    python3 gui_main_modular.py
}

# Full setup function
full_setup() {
    echo "PyZazz - Setup and Launch"
    echo "========================="
    
    # Check if Python 3 is installed
    if ! command -v python3 &> /dev/null; then
        echo "ERROR: Python 3 not found. Please install Python 3."
        exit 1
    fi

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    echo "Activating virtual environment..."
    source venv/bin/activate

    # Upgrade pip if needed (suppress output for cleaner experience)
    echo "Updating pip..."
    pip install --upgrade pip -q 2>/dev/null || echo "Note: pip upgrade failed (this is usually fine)"

    # Install PortAudio for sounddevice on macOS when Homebrew is available.
    if command -v brew &> /dev/null; then
        if ! brew list portaudio &> /dev/null 2>&1; then
            echo "Installing PortAudio via Homebrew..."
            brew install portaudio
        else
            echo "PortAudio already installed"
        fi
    else
        echo "Homebrew not found; skipping PortAudio installation"
    fi

    # Install Python requirements
    echo "Installing Python requirements..."
    pip install -r requirements.txt -q

    # Check for ffplay availability
    if ! command -v ffplay &> /dev/null; then
        echo "WARNING: ffplay not found. Install ffmpeg to enable video playback."
    else
        echo "ffplay available for video playback"
    fi

    # Create necessary directories
    echo "Creating directories..."
    mkdir -p config videos

    # Check microphone permissions
    echo "Checking microphone permissions..."
    echo "   If prompted, please grant microphone access to your terminal."

    echo "Setup complete!"
    echo ""
}

# Main execution
if needs_setup; then
    full_setup
    echo "Starting PyZazz..."
    echo ""
    echo "Native macOS application starting..."
    echo "Press Cmd+Q to quit the application"
    echo ""
    
    # Set library path for libftdi (ARM64 Homebrew)
    export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
    
    source venv/bin/activate
    python3 gui_main_modular.py
else
    quick_launch
fi
