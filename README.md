# PyZazz

PyZazz is a Python-based audio-reactive light show controller for live performance work. It combines real-time audio analysis, DMX512 output, fullscreen visualizations, and optional external-display video playback in a single desktop application.

## Features

- Real-time bass, mid, and treble analysis with beat detection
- DMX512 output with automatic FTDI detection and simulator fallback
- Song-based presets for intensity, reactivity, colors, and media mode
- Built-in fullscreen visualizations with seamless mode switching
- FFplay-based external-display video playback
- JSON configuration for lights, songs, and runtime settings

## Requirements

- Python 3.11+
- `ffplay` from FFmpeg for video playback
- PortAudio for microphone input used by `sounddevice`

## Quick Start

```bash
./start.sh
```

For manual setup:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 gui_main_modular.py
```

## Testing

Run the automated test suite:

```bash
source venv/bin/activate
python -m pytest -q
```

There is also a manual audio smoke check:

```bash
python3 quick_tempo_test.py
```

## Configuration

Configuration lives in `config/`:

- `lights.json`: DMX fixture definitions
- `songs.json`: public-safe sample song presets
- `settings.json`: runtime defaults for audio, DMX, video, and UI

The repository ships with generic sample data only. Add your own songs, devices, and media paths locally after cloning.

## Main Files

- `gui_main_modular.py`: application entry point
- `audio_analyzer.py`: microphone capture and audio analysis
- `dmx_controller.py`: DMX interface and simulator integration
- `light_show_engine.py`: light behavior engine
- `video_controller.py`: ffplay process management
- `visualization_controller.py`: visualization lifecycle management
- `config_manager.py`: JSON config loading and persistence

## Notes

- The app defaults to simulator mode when no DMX hardware is detected.
- Video playback is optional; the rest of the system runs without `ffplay`.
- The included configs are intentionally sanitized for public release.
