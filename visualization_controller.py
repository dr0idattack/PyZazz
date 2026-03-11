"""
Refactored Visualization Controller - Orchestrates individual visualization classes
"""

import tkinter as tk
from tkinter import TclError
import time
import random
import threading
from typing import Optional, Dict, Any

from visualizations import (
    BaseVisualization,
    PsychedelicVisualization,
    WaveformVisualization, 
    ParticlesVisualization,
    SpiralVisualization,
    HyperspaceVisualization,
    BubblesVisualization,
    WildVisualization
)


class VisualizationController:
    """Controller that orchestrates individual visualization classes"""
    
    def __init__(self):
        # Core state
        self.is_running = False
        self.current_mode = "psychedelic"
        self.actual_mode = "psychedelic"  # The actual visualization running (different from current_mode when random)
        self.display_number = 2
        self.animation_thread = None

        # Shared window and canvas
        self.window = None
        self.canvas = None

        # External system references
        self.audio_analyzer = None
        self.color_engine = None
        self.root = None
        
        # Current visualization instance
        self.current_visualization: Optional[BaseVisualization] = None
        
        # Random mode state
        self.last_viz_switch_time = 0
        self.min_mode_duration = 20.0
        self.random_switch_interval = 45.0
        self.next_random_switch_time = 0
        
        # Silent part detection for intelligent switching
        self.audio_history = []
        self.silent_start_time = None
        self.silent_threshold = 0.05
        self.silent_duration_needed = 2.0
        self.last_intelligent_switch = 0
        
        # Available visualization classes
        self.visualization_classes = {
            'psychedelic': PsychedelicVisualization,
            'waveform': WaveformVisualization,
            'particles': ParticlesVisualization,
            'spiral': SpiralVisualization, 
            'hyperspace': HyperspaceVisualization,
            'bubbles': BubblesVisualization,
            'wild': WildVisualization
        }
        
        # Audio data cache
        self.current_level = 0.0
        self.freq_bands = {'bass': 0.0, 'mid': 0.0, 'treble': 0.0}
        self.beat_detected = False
        
        # Timing
        self.visualization_start_time = None
        self.frame_count = 0
    
    def set_audio_analyzer(self, audio_analyzer):
        """Set reference to audio analyzer"""
        self.audio_analyzer = audio_analyzer
    
    def set_color_engine(self, color_engine):
        """Set reference to color engine"""
        self.color_engine = color_engine
    
    def start_visualization(self, root, mode: str = "psychedelic") -> bool:
        """Start visualization with specified mode"""
        try:
            self.root = root
            self.current_mode = mode
            self.visualization_start_time = time.time()

            # Create window and canvas if they don't exist - NOT fullscreen (individual visualizations handle that)
            if not self.window:
                self.window = tk.Toplevel(self.root)
                self.window.title("Music Visualization")
                self.window.configure(bg='black')
                self.canvas = tk.Canvas(self.window, bg='black', highlightthickness=0)
                self.canvas.pack(fill=tk.BOTH, expand=True)
                # Don't make this window fullscreen - individual visualizations create their own fullscreen windows
                self.window.withdraw()  # Hide this window since visualizations create their own
                self.window.bind("<Escape>", lambda e: self.stop())
                self.window.bind("<KeyPress-q>", lambda e: self.stop())

            # Stop any existing visualization
            self.stop()

            # Handle random mode
            if mode == "random":
                # Pick an initial random visualization mode
                available_modes = list(self.visualization_classes.keys())
                self.actual_mode = random.choice(available_modes)
                self.current_mode = "random"  # Keep this as random
                self._schedule_next_random_switch()
                print(f"Random mode: Starting with {self.actual_mode}")
            else:
                self.actual_mode = mode

            # Create and initialize the visualization
            if not self._create_current_visualization():
                return False

            # Start animation loop
            self.is_running = True
            self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
            self.animation_thread.start()

            print(f"Visualization started: {self.actual_mode} (mode={self.current_mode})")
            return True

        except Exception as e:
            print(f"Failed to start visualization: {e}")
            return False
    
    def _create_current_visualization(self) -> bool:
        """Create current visualization instance with proper cleanup sequence"""
        try:
            # FIRST: Complete cleanup of any existing visualization
            if self.current_visualization:
                print(f"CLEANUP: Ensuring complete cleanup of {type(self.current_visualization).__name__}")
                self._ensure_complete_cleanup()
            
            # BRIEF PAUSE: Allow system to complete cleanup
            time.sleep(0.1)
            
            # Get visualization class using actual_mode for random mode support
            viz_class = self.visualization_classes.get(self.actual_mode)
            if not viz_class:
                print(f"Unknown visualization mode: {self.actual_mode}")
                return False
            
            print(f"CREATING: New {self.actual_mode} visualization")
            
            # Create instance
            self.current_visualization = viz_class()
            
            # Set references
            self.current_visualization.set_audio_analyzer(self.audio_analyzer)
            self.current_visualization.set_color_engine(self.color_engine)
            self.current_visualization.root = self.root
            
            # Force display number to 2 (external display)
            self.display_number = 2
            self.current_visualization.display_number = 2
            print(f"CREATING: Setting up {self.actual_mode} on external display")
            
            # Create window with proper error handling
            if not self.current_visualization.create_fullscreen_window(2):
                print(f"ERROR: Failed to create {self.actual_mode} window")
                return False
            
            print(f"CREATING: Window created, initializing {self.actual_mode}")
            
            # Initialize the visualization
            self.current_visualization.initialize()
            
            # Provide initial audio data
            if hasattr(self, 'current_level'):
                self.current_visualization.update_audio_data(
                    self.current_level,
                    self.freq_bands,
                    self.beat_detected
                )
            
            print(f"CREATING: {self.actual_mode} visualization ready")
            return True
            
        except Exception as e:
            print(f"Failed to create visualization: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _ensure_complete_cleanup(self):
        """Ensure complete cleanup of current visualization"""
        if not self.current_visualization:
            return
            
        print(f"CLEANUP: Starting complete cleanup of {type(self.current_visualization).__name__}")
        
        # Stop the visualization immediately
        self.current_visualization.is_running = False
        self.current_visualization.effects_update_active = False
        
        # Clear canvas immediately
        if self.current_visualization.canvas:
            try:
                self.current_visualization.canvas.delete("all")
                self.current_visualization.canvas.update_idletasks()
            except:
                pass
        
        # Stop and wait for animation thread
        if (hasattr(self.current_visualization, 'animation_thread') and 
            self.current_visualization.animation_thread and 
            self.current_visualization.animation_thread.is_alive()):
            self.current_visualization.animation_thread.join(timeout=0.2)
        
        # Destroy window
        if self.current_visualization.window:
            try:
                self.current_visualization.window.destroy()
            except:
                pass
        
        # Call cleanup method
        try:
            self.current_visualization.cleanup()
        except:
            pass
        
        # Clear reference
        self.current_visualization = None
        print(f"CLEANUP: Complete cleanup finished")
    
    def set_visualization_mode(self, mode: str):
        """Change visualization mode with proper cleanup timing"""
        if mode == self.current_mode:
            return

        try:
            print(f"SWITCHING: From {self.current_mode} to {mode}")

            if mode == "random":
                # Pick an initial random visualization mode
                available_modes = list(self.visualization_classes.keys())
                new_actual_mode = random.choice(available_modes)
                self._schedule_next_random_switch()
                print(f"Random mode: Switching to {new_actual_mode}")
                self.actual_mode = new_actual_mode
                self.current_mode = "random"  # Keep this as random
            else:
                self.actual_mode = mode
                self.current_mode = mode

            # Clear the canvas
            if self.canvas:
                self.canvas.delete("all")

            # Create new visualization if we're running - use seamless switching
            if self.is_running:
                print(f"SWITCHING: Creating new visualization: {self.actual_mode}")
                success = self._seamless_switch_to_mode(self.actual_mode)
                if success:
                    print(f"SWITCHING: Successfully created {self.actual_mode}")
                else:
                    print(f"SWITCHING: Failed to create {self.actual_mode}")

            print(f"Switched to visualization mode: {self.actual_mode} (mode={self.current_mode})")

        except Exception as e:
            print(f"Failed to switch visualization mode: {e}")
            import traceback
            traceback.print_exc()

    def stop(self):
        """Stop the visualization with improved cleanup"""
        print(f"VISUALIZATION CONTROLLER: Stopping {self.current_mode}")
        self.is_running = False

        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1.0)

        if self.window:
            self.window.withdraw()
    
    def stop(self):
        """Stop the visualization with improved cleanup"""
        print(f"VISUALIZATION CONTROLLER: Stopping {self.current_mode}")
        self.is_running = False
        
        if self.current_visualization:
            print(f"VISUALIZATION CONTROLLER: Cleaning up {type(self.current_visualization).__name__}")
            
            # Force immediate stop
            self.current_visualization.is_running = False
            self.current_visualization.effects_update_active = False
            
            # Clear canvas immediately
            if self.current_visualization.canvas:
                try:
                    self.current_visualization.canvas.delete("all")
                    self.current_visualization.canvas.update()
                except:
                    pass
            
            # Stop the visualization
            self.current_visualization.stop()
            
            # Wait for animation thread to finish
            if (self.current_visualization.animation_thread and 
                self.current_visualization.animation_thread.is_alive()):
                self.current_visualization.animation_thread.join(timeout=0.3)
            
            self.current_visualization = None
            print(f"VISUALIZATION CONTROLLER: Cleanup complete")
        
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1.0)
            
        print(f"VISUALIZATION CONTROLLER: Stop complete")
    
    def is_running_visualization(self) -> bool:
        """Check if any visualization is currently running"""
        return (self.is_running and 
                self.current_visualization is not None and 
                self.current_visualization.is_running)
    
    def _animation_loop(self):
        """Main animation loop"""
        while self.is_running:
            try:
                start_time = time.time()
                
                # Check if we still have a valid visualization
                if not self.current_visualization or not self.current_visualization.canvas:
                    print("Visualization stopped - exiting animation loop")
                    break
                
                # Frame count is incremented in visualization's update_effects()
                
                # Update audio data in visualization
                self._update_visualization_audio()
                
                # Handle random mode switching
                if self.current_mode == "random":
                    self._handle_random_switching()
                
                # Handle intelligent switching
                self._handle_intelligent_switching()
                
                # Render current visualization
                if self.current_visualization and self.current_visualization.canvas:
                    try:
                        self.current_visualization.render()
                    except TclError as tcl_e:
                        if "invalid command name" in str(tcl_e):
                            print("Canvas destroyed - stopping animation loop")
                            break
                        else:
                            raise tcl_e
                
                # Target 24fps
                elapsed = time.time() - start_time
                target_frame_time = 1.0 / 24.0
                if elapsed < target_frame_time:
                    time.sleep(target_frame_time - elapsed)
                
            except Exception as e:
                print(f"Animation loop error: {e}")
                # Check if it's a canvas-related error that means we should stop
                if "invalid command name" in str(e) or "application has been destroyed" in str(e):
                    print("Canvas/window destroyed - stopping animation loop")
                    break
                # Continue for other errors but log them
                continue
    
    def _update_visualization_audio(self):
        """Update visualization with current audio data"""
        if not self.current_visualization:
            return
            
        # Get current audio data
        if self.audio_analyzer:
            self.current_level = getattr(self.audio_analyzer, 'current_level', 0.0)
            self.freq_bands = getattr(self.audio_analyzer, 'freq_bands', {'bass': 0.0, 'mid': 0.0, 'treble': 0.0})
            self.beat_detected = getattr(self.audio_analyzer, 'beat_detected', False)
        
        # Update visualization
        self.current_visualization.update_audio_data(
            self.current_level, 
            self.freq_bands, 
            self.beat_detected
        )
        
        # Update song colors - use current properties since get_current_colors doesn't exist
        if self.current_visualization:
            self.current_visualization.update_song_colors(
                self.current_visualization.song_primary_color,
                self.current_visualization.song_secondary_color
            )
    
    def _schedule_next_random_switch(self):
        """Schedule next random mode switch"""
        current_time = time.time()
        # Random interval between 40-50 seconds
        interval = random.uniform(40.0, 50.0)
        self.next_random_switch_time = current_time + interval
        print(f"Next random switch scheduled in {interval:.1f} seconds")
    
    def _handle_random_switching(self):
        """Handle random visualization mode switching"""
        current_time = time.time()
        
        # Check if it's time for a random switch
        if current_time >= self.next_random_switch_time:
            self._switch_random_mode("timer")
        
        # Also check for music-reactive switching
        elif self._should_switch_on_music():
            self._switch_random_mode("music_change")
    
    def _should_switch_on_music(self) -> bool:
        """Check if we should switch based on music changes"""
        current_time = time.time()
        
        # Don't switch too frequently
        if current_time - self.last_viz_switch_time < 10.0:
            return False
        
        # Check for significant energy changes
        if self.current_level > 0.7 and hasattr(self, '_prev_level'):
            # Big energy surge
            if self._prev_level < 0.3 and self.current_level > 0.7:
                return True
        
        # Check for big drops
        if hasattr(self, '_prev_level') and self._prev_level > 0.6 and self.current_level < 0.2:
            return True
        
        self._prev_level = self.current_level
        return False
     
    def _switch_random_mode(self, reason: str):
        """Switch to a new random visualization mode with seamless canvas reuse"""
        available_modes = list(self.visualization_classes.keys())
        
        # Don't repeat the same mode
        if self.actual_mode in available_modes:
            available_modes.remove(self.actual_mode)
        
        if available_modes:
            new_actual_mode = random.choice(available_modes)
            print(f"Random switch ({reason}): {self.actual_mode} -> {new_actual_mode}")
            
            # SEAMLESS SWITCHING - reuse existing window/canvas instead of destroying
            if self.current_visualization and hasattr(self.current_visualization, 'window') and self.current_visualization.window:
                print(f"SEAMLESS SWITCH: Reusing existing window for {new_actual_mode}")
                
                # Store existing window/canvas references
                existing_window = self.current_visualization.window
                existing_canvas = self.current_visualization.canvas
                existing_width = self.current_visualization.width
                existing_height = self.current_visualization.height
                existing_display_number = self.current_visualization.display_number
                existing_monitor = getattr(self.current_visualization, 'monitor', None)
                
                # Stop current visualization gracefully but keep window
                if self.current_visualization:
                    self.current_visualization.is_running = False
                    self.current_visualization.effects_update_active = False
                    
                    # Clear canvas content only, don't destroy
                    if existing_canvas:
                        try:
                            existing_canvas.delete("all")
                            existing_canvas.update_idletasks()
                        except:
                            pass
                    
                    # Quick thread cleanup with null check
                    if (hasattr(self.current_visualization, 'animation_thread') and
                        self.current_visualization.animation_thread and 
                        self.current_visualization.animation_thread.is_alive()):
                        self.current_visualization.animation_thread.join(timeout=0.1)
                
                # Create new visualization instance
                viz_class = self.visualization_classes.get(new_actual_mode)
                if viz_class:
                    self.current_visualization = viz_class()
                    
                    # Set references
                    self.current_visualization.set_audio_analyzer(self.audio_analyzer)
                    self.current_visualization.set_color_engine(self.color_engine)
                    self.current_visualization.root = self.root
                    
                    # REUSE existing window instead of creating new one
                    self.current_visualization.window = existing_window
                    self.current_visualization.canvas = existing_canvas
                    self.current_visualization.width = existing_width
                    self.current_visualization.height = existing_height
                    self.current_visualization.display_number = existing_display_number
                    if existing_monitor:
                        self.current_visualization.monitor = existing_monitor
                    
                    # Initialize the new visualization with existing canvas
                    try:
                        self.current_visualization.initialize()
                        print(f"SEAMLESS SWITCH: Successfully initialized {new_actual_mode} with reused canvas")
                        
                        # Provide initial audio data
                        if hasattr(self, 'current_level'):
                            self.current_visualization.update_audio_data(
                                self.current_level,
                                self.freq_bands,
                                self.beat_detected
                            )
                    except Exception as e:
                        print(f"SEAMLESS SWITCH: Failed to initialize {new_actual_mode}: {e}")
                        # Fallback to traditional window creation
                        self._fallback_create_visualization(new_actual_mode)
                else:
                    print(f"SEAMLESS SWITCH: Unknown visualization class: {new_actual_mode}")
                    return
            else:
                # No existing window - create new one normally
                print(f"SEAMLESS SWITCH: No existing window, creating new one for {new_actual_mode}")
                self._fallback_create_visualization(new_actual_mode)
            
            self.actual_mode = new_actual_mode
            self.last_viz_switch_time = time.time()
            self._schedule_next_random_switch()
    
    def _fallback_create_visualization(self, mode: str):
        """Fallback method to create visualization with new window"""
        self.current_visualization = None
        self.actual_mode = mode
        self.display_number = 2
        success = self._create_current_visualization()
        if not success:
            print(f"FALLBACK: Failed to create {mode}")
    
    def _seamless_switch_to_mode(self, new_mode: str) -> bool:
        """Seamlessly switch to a specific mode (used for manual switching)"""
        if (self.current_visualization and 
            hasattr(self.current_visualization, 'window') and 
            self.current_visualization.window):
            
            print(f"SEAMLESS MANUAL: Reusing existing window for {new_mode}")
            
            # Store existing window/canvas references
            existing_window = self.current_visualization.window
            existing_canvas = self.current_visualization.canvas
            existing_width = self.current_visualization.width
            existing_height = self.current_visualization.height
            existing_display_number = self.current_visualization.display_number
            existing_monitor = getattr(self.current_visualization, 'monitor', None)
            
            # Stop current visualization gracefully but keep window
            if self.current_visualization:
                self.current_visualization.is_running = False
                self.current_visualization.effects_update_active = False
                
                # Clear canvas content only, don't destroy
                if existing_canvas:
                    try:
                        existing_canvas.delete("all")
                        existing_canvas.update_idletasks()
                    except:
                        pass
                
                # Quick thread cleanup
                if (hasattr(self.current_visualization, 'animation_thread') and
                    self.current_visualization.animation_thread and 
                    self.current_visualization.animation_thread.is_alive()):
                    self.current_visualization.animation_thread.join(timeout=0.1)
            
            # Create new visualization instance
            viz_class = self.visualization_classes.get(new_mode)
            if viz_class:
                self.current_visualization = viz_class()
                
                # Set references
                self.current_visualization.set_audio_analyzer(self.audio_analyzer)
                self.current_visualization.set_color_engine(self.color_engine)
                self.current_visualization.root = self.root
                
                # REUSE existing window instead of creating new one
                self.current_visualization.window = existing_window
                self.current_visualization.canvas = existing_canvas
                self.current_visualization.width = existing_width
                self.current_visualization.height = existing_height
                self.current_visualization.display_number = existing_display_number
                if existing_monitor:
                    self.current_visualization.monitor = existing_monitor
                
                # Initialize the new visualization with existing canvas
                try:
                    self.current_visualization.initialize()
                    print(f"SEAMLESS MANUAL: Successfully initialized {new_mode} with reused canvas")
                    
                    # Provide initial audio data
                    if hasattr(self, 'current_level'):
                        self.current_visualization.update_audio_data(
                            self.current_level,
                            self.freq_bands,
                            self.beat_detected
                        )
                    return True
                except Exception as e:
                    print(f"SEAMLESS MANUAL: Failed to initialize {new_mode}: {e}")
                    # Fallback to traditional window creation
                    self._fallback_create_visualization(new_mode)
                    return True  # Return True since fallback might succeed
            else:
                print(f"SEAMLESS MANUAL: Unknown visualization class: {new_mode}")
                return False
        else:
            # No existing window - create new one normally
            print(f"SEAMLESS MANUAL: No existing window, creating new one for {new_mode}")
            self._fallback_create_visualization(new_mode)
            return True
    
    def _handle_intelligent_switching(self):
        """Handle intelligent switching during silent parts"""
        current_time = time.time()
        
        # Track audio history
        self.audio_history.append(self.current_level)
        if len(self.audio_history) > 60:  # Keep last 60 frames (~2.5 seconds at 24fps)
            self.audio_history.pop(0)
        
        # Check for silent periods
        if len(self.audio_history) >= 30:  # Need enough history
            recent_avg = sum(self.audio_history[-30:]) / 30
            
            if recent_avg < self.silent_threshold:
                if self.silent_start_time is None:
                    self.silent_start_time = current_time
                    
                # Check if we've been silent long enough
                silent_duration = current_time - self.silent_start_time
                if (silent_duration >= self.silent_duration_needed and 
                    current_time - self.last_intelligent_switch > self.min_mode_duration):
                    
                    if self.current_mode == "random":
                        self._switch_random_mode("silent_transition")
                    
                    self.last_intelligent_switch = current_time
            else:
                self.silent_start_time = None
    
    def handle_key_press(self, key: str):
        """Handle keyboard shortcuts for mode switching"""
        key_to_mode = {
            '1': 'psychedelic',
            '2': 'waveform', 
            '3': 'particles',
            '4': 'spiral',
            '5': 'hyperspace',
            '6': 'bubbles',
            '7': 'wild',
            '8': 'random',
            '9': 'random'
        }
        
        if key in key_to_mode:
            self.set_visualization_mode(key_to_mode[key])
    
    def is_running_visualization(self) -> bool:
        """Check if visualization is currently running"""
        return self.is_running and self.current_visualization is not None
    
    def get_available_modes(self) -> list:
        """Get list of available visualization modes"""
        modes = list(self.visualization_classes.keys())
        modes.append('random')
        return modes
    
    def get_current_mode(self) -> str:
        """Get current visualization mode"""
        return self.current_mode

    def hide_visualization(self):
        """Hide the visualization window."""
        if self.window:
            self.window.withdraw()

    def show_visualization(self):
        """Show the visualization window."""
        if self.window:
            self.window.deiconify()
    
    def update_audio_data(self, music_info: Dict[str, Any]):
        """Update visualization with current audio data from the GUI"""
        if not self.is_running:
            return
        
        # Extract audio data from music_info
        self.current_level = music_info.get('current_level', 0.0)
        self.freq_bands = music_info.get('frequency_bands', {'bass': 0.0, 'mid': 0.0, 'treble': 0.0})
        self.beat_detected = music_info.get('beat_detected', False)
        
        # Update current visualization if it exists
        if self.current_visualization:
            self.current_visualization.update_audio_data(
                self.current_level,
                self.freq_bands,
                self.beat_detected
            )
            
            # Update song config if provided (includes random color percentage)
            song_config = music_info.get('song_config', {})
            if song_config:
                self.current_visualization.update_song_config(song_config)
        
        # Handle random mode switching - change visualization every 45 seconds
        if self.current_mode == "random":
            current_time = time.time()
            if current_time >= self.next_random_switch_time:
                self._switch_random_mode("timer_gui")
        
        # Handle intelligent switching based on audio data
        self._handle_intelligent_switching()
    
    @property
    def song_primary_color(self):
        """Get current song primary color"""
        if self.current_visualization:
            return self.current_visualization.song_primary_color
        return 'auto'
    
    @song_primary_color.setter
    def song_primary_color(self, value):
        """Set song primary color"""
        if self.current_visualization:
            self.current_visualization.song_primary_color = value
    
    @property
    def song_secondary_color(self):
        """Get current song secondary color"""
        if self.current_visualization:
            return self.current_visualization.song_secondary_color
        return 'none'
    
    @song_secondary_color.setter
    def song_secondary_color(self, value):
        """Set song secondary color"""
        if self.current_visualization:
            self.current_visualization.song_secondary_color = value