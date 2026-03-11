# Agent Guidelines for PyZazz Audio-Reactive Light Show System

**Repository:** https://github.com/dr0idattack/PyZazz  
**System:** Professional live performance audio-reactive lighting controller with DMX512, video projection, and real-time visualizations

## Build/Test/Lint Commands
- **Setup**: `./start.sh` (creates venv, installs deps, launches app)
- **Quick Launch**: `source venv/bin/activate && python3 gui_main_modular.py`
- **Single Test**: `python3 quick_tempo_test.py` (10-second audio clap test)
- **Dependencies**: `pip install -r requirements.txt`

## Key Dependencies & Frameworks
- **Audio**: numpy, sounddevice, librosa for real-time frequency analysis
- **GUI**: tkinter with ttk styling, modular component architecture  
- **Hardware**: pyserial for DMX512 control via FTDI USB interfaces
- **Video**: ffplay (FFmpeg) for cross-platform video projection with instant startup
- **Display**: screeninfo for accurate multi-monitor fullscreen positioning
- **Config**: JSON files in config/ directory for all settings

## Code Style Guidelines
- **NO EMOJIS**: Keep all code, comments, and documentation professional
- **Imports**: Standard library first, then third-party, then local modules
- **Type Hints**: Use typing annotations (Optional, Dict, List, Tuple)
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Error Handling**: Use try/except blocks, never ignore exceptions silently
- **Threading**: Audio analysis in separate threads with deque collections
- **Line Length**: Keep under 120 chars when possible

## Project Architecture
- **Root Controllers**: audio_analyzer.py, dmx_controller.py, light_show_engine.py, visualization_controller.py
- **GUI Modules**: gui/ directory with BaseUIComponent inheritance pattern
- **Visualizations**: visualizations/ directory with 8+ advanced audio-reactive modes
- **Video System**: video_controller.py with optimized ffplay integration
- **Configuration**: JSON-based config management (lights.json, songs.json, settings.json)
- **Controller Registry**: Dependency injection pattern for component communication

## Audio-Reactive System Patterns
- **Frequency Bands**: Separate bass/mid/treble analysis for different light groups
- **Beat Detection**: Real-time BPM detection with auto-correction (80-160 BPM range)
- **Threading**: Audio callback → deque → processing thread → UI updates
- **Data Flow**: sounddevice → AudioAnalyzer → LightShowEngine/VisualizationController → DMXController/Display

## Visualization System Architecture
- **Seamless Switching**: Canvas reuse between modes prevents fullscreen loss
- **Random Mode**: Intelligent 45-second cycling with smooth transitions
- **Multi-Monitor Support**: Proper external display detection and fullscreen
- **Base Class Pattern**: All visualizations inherit from BaseVisualization
- **Audio Integration**: Real-time frequency band and beat detection integration

## Current Visualization Modes
1. **Psychedelic**: Swirling patterns with color morphing and audio reactivity
2. **Waveform**: Audio waveforms with instrument morphing, particle effects, reduced spinning
3. **Spiral**: Enhanced 8-spiral system with 4-layer particles and glow effects  
4. **Hyperspace**: Starfield with warp effects and audio-reactive movement
5. **Particles**: Advanced particle system with physics and collision detection
6. **Bubbles**: Wild wind-driven underwater scene with realistic physics
7. **Wild**: Extreme audio-reactive effects with chaos modes
8. **Random**: Automatic mode switching every 45 seconds

## Recent System Improvements
- **Fixed fullscreen switching**: Manual mode changes preserve external display state
- **Eliminated video startup delay**: Optimized ffplay for <1 second startup vs 60 seconds
- **Enhanced bubbles**: Wild wind-driven movement with music-reactive physics
- **Waveform improvements**: Reduced spinning, persistent floating particles with bass response
- **Seamless transitions**: Canvas reuse eliminates screen flashing during mode changes