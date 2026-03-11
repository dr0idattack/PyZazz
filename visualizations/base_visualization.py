"""
Base visualization class with shared functionality for all visualization modes
"""

import tkinter as tk
import math
import random
import time
import colorsys
from typing import Optional, Dict, Any, List, Tuple
import threading
from screeninfo import get_monitors


class BaseVisualization:
    """Base class for all visualization modes with shared functionality"""
    
    def __init__(self):
        # Window and canvas
        self.window = None
        self.canvas = None
        self.width = 1920
        self.height = 1080
        self.display_number = 2
        
        # Core state
        self.is_running = False
        self.frame_count = 0
        self.beat_pulse = 0.0
        self.last_beat_time = 0
        self.color_phase = 0.0
        
        # Song color integration
        self.song_primary_color = 'auto'
        self.song_secondary_color = 'none'
        self.current_light_states = {}
        self.color_bias_primary = True
        self.random_color_percentage = 25  # Default 25% random colors
        
        # Audio data
        self.current_level = 0.0
        self.freq_bands = {'bass': 0.0, 'mid': 0.0, 'treble': 0.0}
        self.beat_detected = False
        
        # Visual effects parameters
        self.effects = {
            'spiral_rotation': 0.0,
            'color_shift': 0.0,
            'pulse_intensity': 0.0,
            'particle_burst': 0.0,
            'waveform_amplitude': 0.0,
            'waveform_rotation': 0.0,
            'smoke_intensity': 0.0
        }
        
        # Timing and animation
        self.animation_thread = None
        self.last_frame_time = time.time()
        self.effects_update_active = False
        
        # References to external systems
        self.audio_analyzer = None
        self.color_engine = None
        self.root = None

        # Cleanup synchronization
        self.cleanup_complete = threading.Event()
        self.cleanup_complete.set()  # Default to set

    def set_audio_analyzer(self, audio_analyzer):
        """Set reference to audio analyzer"""
        self.audio_analyzer = audio_analyzer
    
    def set_color_engine(self, color_engine):
        """Set reference to color engine"""
        self.color_engine = color_engine
    
    def create_fullscreen_window(self, display_number: int = 2) -> bool:
        """Create fullscreen visualization window on specified display using proper monitor detection"""
        try:
            if not self.root:
                print("ERROR: No root window provided")
                return False

            self.display_number = display_number

            # Create new window
            if self.window:
                try:
                    self.window.destroy()
                except:
                    pass

            self.window = tk.Toplevel(self.root)
            self.window.title("Music Visualization")
            self.window.configure(bg='black')

            # Use screeninfo to get proper monitor information
            monitors = get_monitors()
            print(f"DISPLAY DEBUG: Detected {len(monitors)} monitors:")
            for i, monitor in enumerate(monitors):
                print(f"  Monitor {i}: {monitor.width}x{monitor.height} at ({monitor.x}, {monitor.y})")

            # Select the target monitor
            if display_number == 2 and len(monitors) >= 2:
                # Use secondary monitor
                monitor = monitors[1]
                print(f"VISUALIZATION: Using secondary monitor: {monitor.width}x{monitor.height} at ({monitor.x}, {monitor.y})")
            else:
                # Use primary monitor (fallback)
                monitor = monitors[0]
                print(f"VISUALIZATION: Using primary monitor: {monitor.width}x{monitor.height} at ({monitor.x}, {monitor.y})")

            # Set window geometry to match the selected monitor
            geometry = f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}"
            print(f"VISUALIZATION: Setting geometry: {geometry}")
            self.window.geometry(geometry)
            self.window.update_idletasks()

            # Update dimensions to match the monitor
            self.width = monitor.width
            self.height = monitor.height

            # Store monitor info for later use
            self.monitor = monitor

            # Create canvas
            self.canvas = tk.Canvas(
                self.window,
                width=self.width,
                height=self.height,
                bg='black',
                highlightthickness=0
            )
            self.canvas.pack(expand=True, fill=tk.BOTH)

            # Bind resize event to update dimensions for edge-to-edge rendering
            self.canvas.bind('<Configure>', self._on_canvas_resize)

            # Bind escape key
            self.window.bind('<KeyPress-Escape>', self._handle_escape)
            self.window.bind('<KeyPress-q>', self._handle_escape)
            self.window.focus_set()

            return True

        except Exception as e:
            print(f"Window creation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _apply_fullscreen_immediately(self):
        """Apply true fullscreen mode using the working screeninfo approach"""
        try:
            if not self.window:
                return

            print(f"FULLSCREEN DEBUG: Applying fullscreen for display {self.display_number}")

            # Use the exact approach that works
            monitors = get_monitors()
            
            if self.display_number == 2 and len(monitors) >= 2:
                monitor = monitors[1]  # Secondary display
            else:
                monitor = monitors[0]  # Primary display fallback
            
            print(f"FULLSCREEN: Using monitor {monitor.width}x{monitor.height} at ({monitor.x}, {monitor.y})")
            
            # Position window on the correct monitor
            geometry = f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}"
            self.window.geometry(geometry)
            self.window.update_idletasks()
            
            # Apply fullscreen attribute (this hides menubar and dock)
            self.window.attributes('-fullscreen', True)
            
            print(f"FULLSCREEN: Applied fullscreen on monitor at {monitor.x},{monitor.y}")

            try:
                final_geometry = self.window.winfo_geometry()
                print(f"FULLSCREEN: Final geometry: {final_geometry}")
            except:
                pass

        except Exception as e:
            print(f"FULLSCREEN: Failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    def _apply_fullscreen(self):
        """Legacy method - kept for compatibility"""
        self._apply_fullscreen_immediately()
    
    def _ensure_fullscreen_positioning(self):
        """Ensure fullscreen window stays on correct display"""
        try:
            if self.window and self.display_number == 2:
                # Force positioning on external display again using consistent values
                primary_width = getattr(self, '_consistent_primary_width', 1512)
                x_pos = primary_width  # External display starts at primary width
                y_pos = 0
                
                # Re-apply geometry without fullscreen
                self.window.geometry(f"1920x1080+{x_pos}+{y_pos}")
                # Don't use -fullscreen attribute, keep borderless approach  
                self.window.attributes('-topmost', True)
                print(f"VISUALIZATION: Re-positioned on external display at {x_pos},{y_pos}")
                
        except Exception as e:
            print(f"Failed to ensure fullscreen positioning: {e}")
    
    def _handle_escape(self, event=None):
        """Handle escape key to exit fullscreen"""
        try:
            if self.window:
                self.window.attributes('-fullscreen', False)
                self.window.destroy()
            self.stop()
        except Exception as e:
            print(f"Error handling escape: {e}")
            self.stop()

    def _on_canvas_resize(self, event):
        """Update width and height when canvas is resized to ensure edge-to-edge visuals."""
        self.width = event.width
        self.height = event.height
    
    def update_audio_data(self, level: float, freq_bands: Dict[str, float], beat_detected: bool):
        """Update audio data from analyzer"""
        self.current_level = level
        self.freq_bands = freq_bands.copy()
        self.beat_detected = beat_detected
        
        # Update beat pulse
        if beat_detected:
            self.beat_pulse = 1.0
            self.last_beat_time = time.time()
        else:
            # Decay beat pulse
            time_since_beat = time.time() - self.last_beat_time
            self.beat_pulse = max(0.0, 1.0 - time_since_beat * 2.0)
    
    def update_song_colors(self, primary_color: str, secondary_color: str = 'none'):
        """Update song color theme"""
        self.song_primary_color = primary_color
        self.song_secondary_color = secondary_color
    
    def update_song_config(self, song_config: dict):
        """Update full song configuration including random color percentage"""
        if song_config:
            self.song_primary_color = song_config.get('primary_color_bias', self.song_primary_color)
            self.song_secondary_color = song_config.get('secondary_color_bias', self.song_secondary_color)
            self.random_color_percentage = song_config.get('random_color_percentage', 25)
    
    def get_song_colors(self) -> Tuple[str, str]:
        """Get current song colors"""
        if self.color_engine and hasattr(self.color_engine, 'get_current_colors'):
            try:
                colors = self.color_engine.get_current_colors()
                if colors and len(colors) >= 2:
                    return colors[0], colors[1] if len(colors) > 1 else 'none'
            except:
                pass
        return self.song_primary_color, self.song_secondary_color
    
    def get_color_for_visualization(self, base_hue: float = None, use_random_chance: bool = True) -> str:
        """Get color for visualization respecting random color percentage"""
        try:
            # Get color from color engine if available (respects random color percentage)
            if self.color_engine and use_random_chance:
                # Create a basic music_info dict for the color engine
                music_info = {
                    'current_level': self.current_level,
                    'frequency_bands': self.freq_bands,
                    'beat_detected': self.beat_detected,
                    'song_config': {
                        'primary_color_bias': self.song_primary_color,
                        'secondary_color_bias': self.song_secondary_color,
                        'random_color_percentage': getattr(self, 'random_color_percentage', 25)
                    }
                }
                
                try:
                    color_dict = self.color_engine.get_color_for_music(music_info)
                    return f"#{color_dict['r']:02x}{color_dict['g']:02x}{color_dict['b']:02x}"
                except Exception as e:
                    pass  # Fall through to manual color selection
            
            # Manual color selection (fallback or when use_random_chance=False)
            primary, secondary = self.get_song_colors()
            
            # Use song colors if available
            if primary != 'auto' and primary != 'none':
                if secondary != 'none' and not self.color_bias_primary:
                    return self._color_name_to_hex(secondary)
                return self._color_name_to_hex(primary)
            
            # Fallback to calculated color
            if base_hue is not None:
                r, g, b = colorsys.hsv_to_rgb(base_hue, 0.8, 1.0)
                return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            
            return "#ffffff"
            
        except Exception as e:
            return "#ffffff"
    
    def _color_name_to_hex(self, color_name: str) -> str:
        """Convert color name to hex"""
        color_map = {
            'red': '#ff0000', 'blue': '#0000ff', 'green': '#00ff00',
            'orange': '#ff8800', 'purple': '#8800ff', 'yellow': '#ffff00',
            'cyan': '#00ffff', 'magenta': '#ff00ff', 'white': '#ffffff',
            'pink': '#ff69b4', 'lime': '#00ff00', 'indigo': '#4b0082'
        }
        return color_map.get(color_name.lower(), '#ffffff')
    
    def update_effects(self):
        """Update visual effects based on audio"""
        current_time = time.time()
        dt = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        # Clamp delta time to prevent huge jumps on first frame or pauses
        dt = min(dt, 1.0/15.0)  # Max 15 FPS delta (0.067 seconds)
        dt = max(dt, 1.0/120.0)  # Min 120 FPS delta (0.008 seconds)
        
        # Update color phase
        self.color_phase += dt * 0.5
        if self.color_phase > 1.0:
            self.color_phase -= 1.0
        
        # Update effects based on audio
        self.effects['spiral_rotation'] += dt * (0.5 + self.current_level * 2.0)
        self.effects['color_shift'] = self.color_phase
        self.effects['pulse_intensity'] = self.beat_pulse
        
        # Update frame counter
        self.frame_count += 1
    
    def _validate_canvas(self) -> bool:
        """Check if canvas is still valid for rendering"""
        if not self.canvas:
            return False
        if not self.is_running:
            return False
            
        try:
            # Test canvas validity by checking if it's still accessible
            self.canvas.winfo_exists()
            return True
        except Exception:
            # Canvas is invalid, stop rendering
            self.is_running = False
            return False
    
    def _safe_canvas_delete_all(self) -> bool:
        """Safely delete all canvas items"""
        if not self._validate_canvas():
            return False
            
        try:
            self.canvas.delete("all")
            return True
        except:
            # Canvas operation failed, likely destroyed
            self.is_running = False
            return False
    
    def render(self):
        """Base render method - should be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement render method")
    
    def initialize(self):
        """Initialize visualization with proper timing"""
        print(f"INIT: Initializing {self.__class__.__name__}")
        self.is_running = True
        self.last_frame_time = time.time()

        # Apply fullscreen FIRST with delay to ensure window is ready
        if self.window:
            self.window.after(100, self._delayed_fullscreen)  # 100ms delay
            
        # Start effects thread
        self.effects_update_active = True
        self.animation_thread = threading.Thread(target=self._effects_loop, daemon=False)
        self.animation_thread.start()

        # Start rendering with delay to ensure fullscreen is applied
        if self.window:
            self.window.after(200, self._schedule_render)  # 200ms delay
            
        print(f"INIT: {self.__class__.__name__} initialization complete")
        
    def _delayed_fullscreen(self):
        """Apply fullscreen after window is fully ready"""
        try:
            print(f"FULLSCREEN: Applying delayed fullscreen for {self.__class__.__name__}")
            
            # Ensure window is properly positioned first
            if hasattr(self, 'monitor'):
                geometry = f"{self.monitor.width}x{self.monitor.height}+{self.monitor.x}+{self.monitor.y}"
                print(f"FULLSCREEN: Re-applying geometry: {geometry}")
                self.window.geometry(geometry)
                self.window.update_idletasks()
            
            # Apply fullscreen
            self.window.attributes('-fullscreen', True)
            print(f"FULLSCREEN: Applied fullscreen attribute")
            
            # Final positioning check
            try:
                final_geometry = self.window.winfo_geometry()
                print(f"FULLSCREEN: Final geometry after fullscreen: {final_geometry}")
            except:
                pass
                
        except Exception as e:
            print(f"FULLSCREEN ERROR: {e}")
            import traceback
            traceback.print_exc()

    def _force_fullscreen(self):
        """Force fullscreen using the working screeninfo approach"""
        if not self.window:
            return

        print(f"{self.__class__.__name__}: Applying fullscreen")
        try:
            # Use screeninfo to get correct monitor positioning
            monitors = get_monitors()
            
            if self.display_number == 2 and len(monitors) >= 2:
                monitor = monitors[1]  # Secondary display
            else:
                monitor = monitors[0]  # Primary display fallback
            
            # Position and apply fullscreen
            geometry = f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}"
            self.window.geometry(geometry)
            self.window.update_idletasks()
            self.window.attributes('-fullscreen', True)
            
            print(f"{self.__class__.__name__}: Fullscreen applied on monitor at {monitor.x},{monitor.y}")

        except Exception as e:
            print(f"{self.__class__.__name__}: Fullscreen failed: {e}")
            import traceback
            traceback.print_exc()
    
    def cleanup(self):
        """Cleanup resources - can be overridden by subclasses"""
        pass
    
    def _effects_loop(self):
        """Background thread for updating effects parameters"""
        target_fps = 24
        frame_time = 1.0 / target_fps

        while self.effects_update_active and self.is_running:
            start_time = time.time()

            try:
                self.update_effects()

                # Periodic geometry check
                if self.frame_count % 300 == 0:  # Check every ~12 seconds
                    self._ensure_fullscreen_positioning()

            except Exception as e:
                if self.is_running:
                    print(f"Effects update error: {e}")
                break

            # Consistent timing
            elapsed = time.time() - start_time
            sleep_time = max(0.020, frame_time - elapsed)  # 20ms minimum
            time.sleep(sleep_time)
    
    def _schedule_render(self):
        """Schedule rendering on main thread with tkinter-compatible timing"""
        if self.is_running and self.window and self.canvas:
            try:
                # Check if window still exists
                if not self.window.winfo_exists():
                    return
                    
                self._render_frame()
                # Schedule next render - 42ms = ~24fps
                self.window.after(42, self._schedule_render)
                
            except Exception as e:
                if self.is_running:
                    print(f"Render scheduling error: {e}")
    
    def _render_frame(self):
        """Render current frame with zero flashing"""
        if not self.canvas or not self.is_running:
            return
        
        try:
            # Check if canvas still exists
            if not self.canvas.winfo_exists():
                return
                
            # Clear and render in one operation
            self.canvas.delete("all")
            self.render()
            
        except Exception as e:
            if self.is_running:
                print(f"Render frame error: {e}")

    def stop(self):
        """Stop the visualization with proper cleanup timing"""
        print(f"STOP: Stopping {self.__class__.__name__}")
        self.is_running = False
        self.effects_update_active = False
        self.cleanup_complete.clear()

        # Stop effects thread first
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1.0)  # Longer timeout

        # Immediate cleanup without delays to prevent race conditions
        self._immediate_cleanup()

    def _immediate_cleanup(self):
        """Perform immediate cleanup to prevent race conditions"""
        try:
            print(f"CLEANUP: Immediate cleanup for {self.__class__.__name__}")
            
            # Clear canvas immediately
            if self.canvas:
                try:
                    self.canvas.delete("all")
                    self.canvas.update_idletasks()
                except:
                    pass
            
            # Call subclass cleanup
            self.cleanup()

            # Destroy window and canvas in correct order
            if self.window:
                try:
                    # Remove fullscreen first to prevent issues
                    self.window.attributes('-fullscreen', False)
                    # Then destroy
                    self.window.destroy()
                    print(f"CLEANUP: Window destroyed for {self.__class__.__name__}")
                except:
                    pass
                self.window = None
                self.canvas = None  # Canvas is destroyed with window

        except Exception as e:
            print(f"CLEANUP ERROR: {e}")
        finally:
            self.cleanup_complete.set()
            print(f"CLEANUP: Complete for {self.__class__.__name__}")