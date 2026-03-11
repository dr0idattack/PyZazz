import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

class ConfigManager:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.songs_config_path = self.config_dir / "songs.json"
        self.settings_config_path = self.config_dir / "settings.json"
        
        self.songs_config = {}
        self.settings_config = {}
        
        self._load_configs()
        
    def _load_configs(self):
        """Load all configuration files"""
        self._load_songs_config()
        self._load_settings_config()
        
    def _load_songs_config(self):
        """Load songs configuration from JSON file"""
        if self.songs_config_path.exists():
            try:
                with open(self.songs_config_path, 'r') as f:
                    self.songs_config = json.load(f)
            except Exception as e:
                print(f"Error loading songs config: {e}")
                self._create_default_songs_config()
        else:
            self._create_default_songs_config()
            
    def _create_default_songs_config(self):
        """Create default songs configuration"""
        self.songs_config = {
            "songs": {
                "Example Song 1": {
                    "intensity": 180,
                    "reactivity_mode": "medium",
                    "color_bias": "blue",
                    "video_path": "",
                    "visualization_mode": "none",
                    "notes": "Example song with medium reactivity"
                },
                "Example Song 2": {
                    "intensity": 220,
                    "reactivity_mode": "very_reactive",
                    "color_bias": "red",
                    "video_path": "",
                    "visualization_mode": "none",
                    "notes": "High energy song with very reactive mode"
                },
                "Chill Song": {
                    "intensity": 120,
                    "reactivity_mode": "easy",
                    "color_bias": "purple",
                    "video_path": "",
                    "visualization_mode": "none",
                    "notes": "Calm song with easy reactivity"
                }
            }
        }
        self._save_songs_config()
        
    def _load_settings_config(self):
        """Load general settings configuration"""
        if self.settings_config_path.exists():
            try:
                with open(self.settings_config_path, 'r', encoding='utf-8') as f:
                    self.settings_config = json.load(f)
                self._normalize_settings_config()
            except Exception as e:
                print(f"Error loading settings config: {e}")
                self._create_default_settings_config()
        else:
            self._create_default_settings_config()
            
    def _create_default_settings_config(self):
        """Create default settings configuration"""
        self.settings_config = {
            "audio": {
                "sample_rate": 44100,
                "chunk_size": 1024,
                "beat_threshold": 0.3,
                "input_device": "default"
            },
            "dmx": {
                "port": "/dev/tty.usbserial-*",
                "simulate_mode": True,
                "universe_size": 512
            },
            "video": {
                "fullscreen_display": 2,
                "video_directory": "videos/",
                "default_volume": 80
            },
            "ui": {
                "theme": "dark",
                "update_rate_fps": 20,
                "show_debug_info": True
            }
        }
        self._save_settings_config()

    def _normalize_settings_config(self):
        """Backfill legacy settings keys and remove machine-specific defaults."""
        legacy_video = self.settings_config.pop("vlc", None)
        if "video" not in self.settings_config:
            self.settings_config["video"] = legacy_video or {}
        elif legacy_video:
            for key, value in legacy_video.items():
                self.settings_config["video"].setdefault(key, value)

        audio_settings = self.settings_config.setdefault("audio", {})
        video_settings = self.settings_config.setdefault("video", {})

        if audio_settings.get("input_device") in {
            None,
            "",
            "MacBook Pro Microphone",
            "0: MacBook Pro Microphone",
        }:
            audio_settings["input_device"] = "default"

        video_settings.setdefault("fullscreen_display", 2)
        video_settings.setdefault("video_directory", "videos/")
        video_settings.setdefault("default_volume", 80)
        
    def get_song_config(self, song_name: str) -> Optional[Dict]:
        """Get configuration for a specific song"""
        return self.songs_config.get("songs", {}).get(song_name)
        
    def get_all_songs(self) -> Dict:
        """Get all songs configuration"""
        return self.songs_config.get("songs", {})
        
    def add_song(self, song_name: str, config: Dict) -> bool:
        """Add a new song configuration"""
        if "songs" not in self.songs_config:
            self.songs_config["songs"] = {}
            
        # Validate required fields
        required_fields = ["intensity", "reactivity_mode", "color_bias"] 
        for field in required_fields:
            if field not in config:
                return False
                
        # Validate values
        if not (0 <= config["intensity"] <= 255):
            return False
            
        if config["reactivity_mode"] not in ["easy", "medium", "very_reactive"]:
            return False
            
        valid_colors = ["red", "green", "blue", "purple", "white", "yellow", "orange", "pink"]
        if config["color_bias"].lower() not in valid_colors:
            return False
            
        # Validate secondary color bias (optional)
        if "secondary_color_bias" in config:
            valid_secondary_colors = ["none"] + valid_colors
            if config["secondary_color_bias"].lower() not in valid_secondary_colors:
                return False
        
        # Add default fields if not provided
        if "video_path" not in config:
            config["video_path"] = ""
        if "visualization_mode" not in config:
            config["visualization_mode"] = "none"
        if "notes" not in config:
            config["notes"] = ""
        if "secondary_color_bias" not in config:
            config["secondary_color_bias"] = "none"
            
        self.songs_config["songs"][song_name] = config
        self._save_songs_config()
        return True
        
    def update_song(self, song_name: str, config: Dict) -> bool:
        """Update an existing song configuration"""
        print(f"DEBUG: Updating song '{song_name}' with config: {config}")
        
        if song_name not in self.songs_config.get("songs", {}):
            print(f"DEBUG: Song '{song_name}' not found in existing songs")
            return False
            
        # Show before update
        print(f"DEBUG: Before update: {self.songs_config['songs'][song_name]}")
        
        # Update the configuration
        self.songs_config["songs"][song_name].update(config)
        
        # Show after update
        print(f"DEBUG: After update: {self.songs_config['songs'][song_name]}")
        
        self._save_songs_config()
        print(f"DEBUG: Song '{song_name}' update completed and saved")
        return True
        
    def delete_song(self, song_name: str) -> bool:
        """Delete a song configuration"""
        if song_name in self.songs_config.get("songs", {}):
            del self.songs_config["songs"][song_name]
            self._save_songs_config()
            return True
        return False
        
    def get_setting(self, category: str, key: str) -> Optional[Any]:
        """Get a specific setting value"""
        category_name = self._resolve_settings_category(category)
        return self.settings_config.get(category_name, {}).get(key)

    def update_setting(self, category: str, key: str, value: Any):
        """Update a specific setting value"""
        category_name = self._resolve_settings_category(category)
        if category_name not in self.settings_config:
            self.settings_config[category_name] = {}

        self.settings_config[category_name][key] = value
        self._save_settings_config()

    def _resolve_settings_category(self, category: str) -> str:
        """Map legacy settings groups to the canonical public config shape."""
        return "video" if category == "vlc" else category
        
    def get_color_options(self) -> List[str]:
        """Get list of available color bias options"""
        return ["red", "green", "blue", "purple", "white", "yellow", "orange", "pink"]
        
    def get_reactivity_options(self) -> List[str]:
        """Get list of available reactivity mode options"""
        return ["easy", "medium", "very_reactive"]
        
    def _save_songs_config(self):
        """Save songs configuration to file"""
        try:
            with open(self.songs_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.songs_config, f, indent=2)
        except Exception as e:
            print(f"Error saving songs config: {e}")
            
    def _save_settings_config(self):
        """Save settings configuration to file"""
        try:
            with open(self.settings_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings_config, f, indent=2)
        except Exception as e:
            print(f"Error saving settings config: {e}")
            
    def export_config(self, export_path: str) -> bool:
        """Export all configurations to a single file"""
        try:
            combined_config = {
                "songs": self.songs_config,
                "settings": self.settings_config,
                "export_timestamp": time.time()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(combined_config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting config: {e}")
            return False
            
    def import_config(self, import_path: str) -> bool:
        """Import configurations from a file"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
                
            if "songs" in imported_config:
                self.songs_config = imported_config["songs"]
                self._save_songs_config()
                
            if "settings" in imported_config:
                self.settings_config = imported_config["settings"]
                self._normalize_settings_config()
                self._save_settings_config()
                
            return True
        except Exception as e:
            print(f"Error importing config: {e}")
            return False
            
    def validate_song_config(self, config: Dict) -> List[str]:
        """Validate a song configuration and return list of errors"""
        errors = []
        
        # Check required fields
        required_fields = ["intensity", "reactivity_mode", "color_bias"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
                continue
                
        # Validate intensity
        if "intensity" in config:
            if not isinstance(config["intensity"], (int, float)):
                errors.append("Intensity must be a number")
            elif not (0 <= config["intensity"] <= 255):
                errors.append("Intensity must be between 0 and 255")
                
        # Validate reactivity mode
        if "reactivity_mode" in config:
            if config["reactivity_mode"] not in self.get_reactivity_options():
                errors.append(f"Invalid reactivity mode: {config['reactivity_mode']}")
                
        # Validate color bias
        if "color_bias" in config:
            if config["color_bias"].lower() not in self.get_color_options():
                errors.append(f"Invalid color bias: {config['color_bias']}")
                
        # Validate video path if provided
        if "video_path" in config and config["video_path"]:
            if not os.path.exists(config["video_path"]):
                errors.append(f"Video file not found: {config['video_path']}")
                
        return errors
    
    @property
    def settings(self):
        """Get settings configuration"""
        return self.settings_config
    
    def save_settings(self):
        """Save settings configuration to file"""
        self._save_settings_config()
