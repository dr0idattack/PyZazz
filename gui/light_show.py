"""
Light Show Widget for DMX Light Show Controller
Main show control interface
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import random
from .base_ui import BaseUIComponent, LoggingMixin
from .song_config import SongSelectorWidget
from .video_controls import VideoControlsWidget


class LightShowWidget(BaseUIComponent, LoggingMixin):
    """Main light show control widget"""
    
    def __init__(self, parent, controllers=None):
        self.is_running = False
        self.current_song = None
        # Initialize logging mixin
        self.info_display = None
        self.status_display = None
        super().__init__(parent, controllers)
    
    def setup_ui(self):
        """Setup light show control UI"""
        self.frame = ttk.Frame(self.parent, padding="10")
        
        # Song selection section
        self._create_song_selection()
        
        # Video controls section  
        self._create_video_controls()
        
        # Control buttons
        self._create_control_buttons()
        
        # Show information display
        # self._create_info_display()  # Removed per user request
        
        # Configure grid weights
        self.frame.columnconfigure(0, weight=1)
        # No expandable row needed since info display was removed
    
    def _on_song_selection_change(self, event=None):
        """Handle song selection change - enable start button and optionally auto-start"""
        selected_song = self.song_selector.get_selected_song()
        
        # Always enable the start button when a song is selected
        if selected_song:
            self.start_button.config(state=tk.NORMAL)
            # Visualization mode is now handled in song configuration only
        
        # Do NOT auto-start when selection changes while a show is running.
        # User must click Start Show to switch shows. This keeps the Start
        # button enabled so they can manually switch.
    
    def _create_song_selection(self):
        """Create song selection section"""
        song_frame = ttk.LabelFrame(self.frame, text="Song Selection", padding="10")
        song_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Song selector widget with auto-start callback and double-click to start show
        self.song_selector = SongSelectorWidget(song_frame, self.controllers, self._on_song_selection_change, self.start_show)
        self.song_selector.get_frame().grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        song_frame.columnconfigure(0, weight=1)
    
    def _create_video_controls(self):
        """Create video controls section"""
        # Video controls widget
        self.video_controls = VideoControlsWidget(
            self.frame, 
            self.controllers,
            song_combo=self.song_selector.get_combo_widget()
        )
        self.video_controls.get_frame().grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Set logging displays for video controls
        self.video_controls.set_info_display(None)  # Will be set after info display is created
        self.video_controls.set_status_display(None)  # Will be set after status display is created

    
    def _create_control_buttons(self):
        """Create main control buttons"""
        control_frame = ttk.Frame(self.frame)
        control_frame.grid(row=2, column=0, columnspan=2, pady=(10, 10))
        
        self.start_button = ttk.Button(control_frame, text="Start Show", 
                                      command=self.start_show, style='Accent.TButton')
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="Stop Show", 
                                     command=self.stop_show, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1)
    
    # def _create_info_display(self):
    #     """Create show information display - REMOVED per user request"""
    #     pass
    
    def start_show(self):
        """Start a light show (auto-stops any running show/video first)"""
        selected_song = self.song_selector.get_selected_song()
        if not selected_song:
            print("ERROR: Please select a song")
            return
        
        config_manager = self.get_controller('config_manager')
        if not config_manager:
            print("ERROR: Configuration manager not available")
            return
            
        song_config = config_manager.get_song_config(selected_song)
        if not song_config:
            print(f"ERROR: Song '{selected_song}' not found")
            return
        
        # Always stop any existing visualizations/videos first, regardless of running state
        self.log_info(f"Cleaning up previous show to start: {selected_song}")
        
        # Force stop any running visualization first
        visualizer = self.get_controller('visualization_controller')
        if visualizer and visualizer.is_running_visualization():
            print(f"SHOW SWITCH: Force stopping {visualizer.current_mode} visualization")
            visualizer.stop()
            
            # Brief pause to ensure cleanup completes
            import time
            time.sleep(0.15)
            print(f"SHOW SWITCH: Previous visualization cleanup complete")
        
        # Stop any running video
        video_controller = self.get_controller('video_controller')
        if video_controller:
            video_controller.stop()
        
        # If show was running, do full stop
        if self.is_running:
            self.stop_show()  # Use the same method as the Stop Show button
            
        # Set current song and mark running
        self.current_song = song_config.copy()
        self.current_song['name'] = selected_song
        self.is_running = True

        # Update UI: keep Start enabled (user may want to restart), enable Stop
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)

        # Activate the light show engine
        light_show_engine = self.get_controller('light_show_engine')
        if light_show_engine:
            light_show_engine.activate_engine()

        # Start light show thread
        threading.Thread(target=self._run_light_show, daemon=True).start()

        self.log_info(f"Started light show: {selected_song}")
        self.log_info(f"Intensity: {song_config['intensity']}, Mode: {song_config['reactivity_mode']}, Color: {song_config['color_bias']}")

        # Determine media choice based on new media_mode field or legacy detection
        media_mode = self.current_song.get('media_mode', 'auto')
        
        if media_mode == 'video':
            vis_choice = 'video'
        elif media_mode == 'visualization':
            vis_choice = self.current_song.get('visualization_mode', 'psychedelic')
        else:
            # Legacy auto-detection for backwards compatibility
            vis_choice = self.current_song.get('visualization_mode', 'none')
            if vis_choice == 'none' and self.current_song.get('video_path'):
                video_path = self.current_song.get('video_path', '')
                if video_path and os.path.exists(video_path):
                    vis_choice = 'video'
                    print(f"LEGACY AUTO-DETECT: Song has video_path but no visualization_mode, defaulting to 'video'")

        print(f"SONG DEBUG: {selected_song} has media_mode='{media_mode}' -> vis_choice='{vis_choice}'")

        if vis_choice not in ['none', 'video']:
            self.log_info(f"{vis_choice.capitalize()} Visualizer will start.")
        elif self.current_song.get('video_path'):
            video_path = self.current_song.get('video_path', '')
            if video_path and os.path.exists(video_path):
                self.log_info(f"Video will auto-start immediately: {os.path.basename(video_path)}")

        # Notify status bar
        status_bar = self.get_controller('status_bar')
        if status_bar:
            status_bar.set_running_status(selected_song)
        
    
    def stop_show(self):
        """Stop the current light show"""
        self.is_running = False
        
        # Deactivate the light show engine
        light_show_engine = self.get_controller('light_show_engine')
        if light_show_engine:
            light_show_engine.deactivate_engine()
        
        dmx_controller = self.get_controller('dmx_controller')
        if dmx_controller:
            dmx_controller.all_lights_off()
        
        # Stop any running visualization
        visualizer = self.get_controller('visualization_controller')
        if visualizer and visualizer.is_running_visualization():
            visualizer.stop()
            self.log_info("Stopped visualization")
        
        # Stop any running video
        video_controller = self.get_controller('video_controller')
        if video_controller:
            video_controller.stop()
        
        # Update UI
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        self.log_info("Light show stopped")
        
        # Notify status bar
        status_bar = self.get_controller('status_bar')
        if status_bar:
            status_bar.set_ready_status()
    
    
    def _run_light_show(self):
        """Main light show loop with intelligent effects"""
        import time
        
        # Track start time for video auto-start
        show_start_time = time.time()
        media_started = False
        
        # Determine media choice using same logic as start_show
        if self.current_song:
            media_mode = self.current_song.get('media_mode', 'auto')
            
            if media_mode == 'video':
                vis_choice = 'video'
            elif media_mode == 'visualization':
                vis_choice = self.current_song.get('visualization_mode', 'psychedelic')
            else:
                # Legacy auto-detection
                vis_choice = self.current_song.get('visualization_mode', 'none')
                if vis_choice == 'none' and self.current_song.get('video_path'):
                    video_path = self.current_song.get('video_path', '')
                    if video_path and os.path.exists(video_path):
                        vis_choice = 'video'
        else:
            vis_choice = 'none'

        while self.is_running:
            try:
                audio_analyzer = self.get_controller('audio_analyzer')
                dmx_controller = self.get_controller('dmx_controller')
                color_engine = self.get_controller('color_engine')
                light_show_engine = self.get_controller('light_show_engine')
                
                if not all([audio_analyzer, dmx_controller, color_engine, light_show_engine]):
                    break
                
                # Auto-start video or visualizer immediately if configured
                current_time = time.time()
                if not media_started and (current_time - show_start_time) >= 0.0:  # Start video immediately
                    if self.current_song:
                        if vis_choice != 'none' and vis_choice != 'video':
                            # Start audio visualizer on secondary display
                            print(f"AUTO-START: Starting {vis_choice} visualizer...")
                            visualizer = self.get_controller('visualization_controller')
                            config_manager = self.get_controller('config_manager')
                            display_number = 2  # Default to secondary display
                            if config_manager:
                                setting = config_manager.get_setting('vlc', 'fullscreen_display')
                                if setting is not None:
                                    display_number = setting
                            
                            if visualizer:
                                success = self._start_visualization_with_display(visualizer, vis_choice, display_number)
                                if success:
                                    self.log_info(f"Auto-started {vis_choice} visualizer on display {display_number} (immediate)")
                                else:
                                    print(f"VISUALIZATION FAILED: Could not start {vis_choice} on display {display_number}")
                            else:
                                print(f"VISUALIZATION FAILED: No visualizer controller available")
                        elif vis_choice == 'video':
                            # Start video playback on external display
                            video_path = self.current_song.get('video_path', '')
                            if video_path and os.path.exists(video_path):
                                # Get display number for fullscreen
                                config_manager = self.get_controller('config_manager')
                                display_number = 2  # Default to secondary display
                                if config_manager:
                                    setting = config_manager.get_setting('vlc', 'fullscreen_display')
                                    if setting is not None:
                                        display_number = setting
                                
                                video_controller = self.get_controller('video_controller')
                                if video_controller:
                                    try:
                                        if video_controller.play_video(video_path, fullscreen_display=display_number):
                                            self.log_info(f"Auto-started video on display {display_number} (immediate): {os.path.basename(video_path)}")
                                        else:
                                            self.log_error(f"Failed to auto-start video: {os.path.basename(video_path)}")
                                    except Exception as e:
                                        self.log_error(f"Error auto-starting video: {e}")

                    media_started = True  # Mark as attempted regardless of success
                
                music_info = audio_analyzer.get_music_characteristics()

                if self.current_song:
                    # Add song config to music_info for light engine access
                    music_info['song_config'] = self.current_song
                    
                    # Extract and add song colors to music_info for color engine
                    music_info['song_color'] = self.current_song.get('color_bias', 'auto')
                    music_info['song_secondary_color'] = self.current_song.get('secondary_color_bias', 'none')
                    music_info['reactivity_mode'] = self.current_song.get('reactivity_mode', 'medium')
                    # Apply mic sensitivity to audio data BEFORE sending to visualizer
                    mic_sensitivity = self.current_song.get('mic_sensitivity', 0.3)
                    music_info['current_level'] *= mic_sensitivity * 3.33
                    music_info['current_level'] = min(1.0, music_info['current_level'])
                    
                    # Apply adaptive reactivity scaling based on reactivity mode and tempo
                    reactivity_mode = self.current_song.get('reactivity_mode', 'medium')
                    tempo = music_info.get('tempo', 120)
                    total_energy = sum(music_info.get('frequency_bands', {'bass': 0, 'mid': 0, 'treble': 0}).values())
                    
                    if reactivity_mode == 'easy':
                        # Easy mode: Keep lights on more but reduce dramatic flashing/pulsing
                        tempo_factor = 1.0
                        energy_factor = 1.0
                        
                        if tempo < 80:
                            # Very slow tempo: reduce reactivity but keep lights more active
                            tempo_factor = 0.6
                        elif tempo < 100:
                            # Slow tempo: reduce reactivity moderately  
                            tempo_factor = 0.75
                        elif tempo > 140:
                            # Fast tempo: allow more reactivity
                            tempo_factor = 1.0
                        elif tempo > 120:
                            # Medium-fast tempo: slightly more reactive
                            tempo_factor = 0.9
                        else:
                            # Medium tempo: standard reactivity
                            tempo_factor = 0.8
                        
                        # Energy-based scaling: less aggressive scaling to keep lights more active
                        if total_energy < 0.2:
                            energy_factor = 0.7  # Keep more light activity during quiet parts
                        elif total_energy < 0.5:
                            energy_factor = 0.85  # Moderate scaling during medium energy
                        else:
                            energy_factor = 1.0  # Full reactivity during high energy
                        
                        # Combine tempo and energy factors (use minimum for conservative approach)
                        adaptive_factor = min(tempo_factor, energy_factor)
                        
                        # Apply less aggressive scaling to beat detection to reduce flashing
                        if 'beat_detected' in music_info:
                            # Reduce beat intensity rather than eliminating beats entirely
                            if adaptive_factor < 0.7:
                                # Reduce beat frequency but don't eliminate beats completely
                                import random
                                if random.random() > adaptive_factor:
                                    music_info['beat_detected'] = False
                        
                        # Apply gentler scaling to frequency bands to maintain light activity
                        if 'frequency_bands' in music_info:
                            bands = music_info['frequency_bands']
                            # Use gentler scaling to keep lights more active
                            gentle_factor = max(0.8, adaptive_factor)  # Never go below 80%
                            if 'bass' in bands:
                                bands['bass'] *= gentle_factor
                            if 'mid' in bands:
                                bands['mid'] *= gentle_factor
                            if 'treble' in bands:
                                # Use even less aggressive scaling for treble to keep PARs working
                                treble_factor = max(0.85, adaptive_factor)  # Never go below 85% for treble
                                bands['treble'] *= treble_factor
                        
                        # Scale overall level less aggressively to maintain light activity
                        gentle_level_factor = max(0.8, adaptive_factor)
                        music_info['current_level'] *= gentle_level_factor
                        
                        # Only log Easy Mode status every 10 seconds to reduce spam
                        if not hasattr(self, '_last_easy_mode_log'):
                            self._last_easy_mode_log = 0
                        
                        current_time = time.time()
                        if current_time - self._last_easy_mode_log > 10.0:  # Every 10 seconds
                            self._last_easy_mode_log = current_time
                            print(f"Easy mode: tempo={tempo}bpm, energy={total_energy:.2f}, adaptive factor={adaptive_factor:.2f}")
                    
                    # Add song colors to music_info BEFORE sending to visualizer
                    song_color = self.current_song.get('color_bias', 'auto')
                    secondary_color = self.current_song.get('secondary_color_bias', 'none')
                    music_info['color_bias'] = song_color
                    music_info['secondary_color_bias'] = secondary_color
                    
                    
                    
                    # Send processed audio data to visualizer
                    visualizer = self.get_controller('visualization_controller')
                    if visualizer and visualizer.is_running_visualization():
                        visualizer.update_audio_data(music_info)
                        
                    color_engine.set_favorite_color(self.current_song.get('color_bias', 'white'))
                    # mic_sensitivity is a 0..1 factor; scale threshold proportionally
                    # (previous code divided and could set threshold to 1.0 which disables beats)
                    audio_analyzer.set_beat_threshold(0.3 * mic_sensitivity)
                    
                    # Set reactivity mode for enhanced beat detection
                    reactivity_mode = self.current_song.get('reactivity_mode', 'medium')
                    audio_analyzer.set_reactivity_mode(reactivity_mode)

                lights_config = dmx_controller.get_lights_config()
                
                # Debug: Verify lights_config type before passing to engine
                if not isinstance(lights_config, dict):
                    print(f"WARNING: lights_config from DMX controller is {type(lights_config)}, expected dict")
                    print(f"    Content: {lights_config}")
                    continue
                
                light_states = light_show_engine.generate_light_frame(music_info, lights_config)

                # Add light states to music_info for visualization sync
                music_info['light_states'] = light_states

                # Debug disabled for cleaner output

                for light_id, state in light_states.items():
                    dmx_controller.set_light_rgb(light_id, state['r'], state['g'], state['b'], state['intensity'])

                update_rate = 60  # Increased from 40 to 60 Hz (16.7ms instead of 25ms)
                time.sleep(1.0 / update_rate)

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"Light show error: {e}")
                print(f"Error details:\n{error_details}")
                self.log_error(f"Light show error: {e}")
                break
    
    def _stop_current_show_completely(self):
        """Completely stop the current show and clean up all resources"""
        # Stop the show loop
        self.is_running = False
        
        # Deactivate the light show engine
        light_show_engine = self.get_controller('light_show_engine')
        if light_show_engine:
            light_show_engine.deactivate_engine()
        
        # Turn off all lights
        dmx_controller = self.get_controller('dmx_controller')
        if dmx_controller:
            dmx_controller.all_lights_off()
        
        # Stop any video
        video_controller = self.get_controller('video_controller')
        if video_controller:
            video_controller.stop()

        # Stop the visualizer and wait for complete cleanup
        visualizer = self.get_controller('visualization_controller')
        if visualizer and visualizer.is_running_visualization():
            current_mode = getattr(visualizer, 'current_mode', 'unknown')
            print(f"Stopping {current_mode} visualization for clean transition...")
            visualizer.stop()
            
            # Skip waiting and polling to avoid system interaction - just proceed immediately
            # The visualization stop() method handles cleanup internally
            print(f"{current_mode} visualization stop initiated - proceeding immediately")
        
        # Minimal pause to allow UI cleanup
        time.sleep(0.01)
    
    def get_current_song(self):
        """Get the currently running song"""
        return self.current_song
    
    def is_show_running(self):
        """Check if show is currently running"""
        return self.is_running
    
    def refresh_songs(self):
        """Refresh the song list"""
        if hasattr(self, 'song_selector'):
            self.song_selector.refresh_songs()
    
    
    
    def _start_visualization_with_display(self, visualizer, mode, display_number):
        """Helper method to start visualization with specific display number and better error handling"""
        try:
            print(f"Attempting to start {mode} visualization on display {display_number}")
            
            # Set the display number for the visualizer before starting
            visualizer.display_number = display_number
            
            # Attempt to start visualization
            success = visualizer.start_visualization(self.frame.winfo_toplevel(), mode)
            
            if success:
                # Immediately set song colors for the visualization to prevent 'auto' fallback
                if self.current_song:
                    song_color = self.current_song.get('color_bias', 'auto') 
                    secondary_color = self.current_song.get('secondary_color_bias', 'none')
                    visualizer.song_primary_color = song_color
                    visualizer.song_secondary_color = secondary_color
                    print(f"Set initial visualization colors: primary='{song_color}', secondary='{secondary_color}'")
                
                print(f"{mode} visualization started successfully on display {display_number}")
                return True
            else:
                print(f"{mode} visualization failed to start on display {display_number}")
                
                
                # Try fallback to primary display if external display failed
                if display_number > 1:
                    print(f"Retrying {mode} visualization on primary display...")
                    visualizer.display_number = 1
                    fallback_success = visualizer.start_visualization(self.frame.winfo_toplevel(), mode)
                    
                    if fallback_success:
                        # Set colors for fallback visualization too
                        if self.current_song:
                            song_color = self.current_song.get('color_bias', 'auto')
                            secondary_color = self.current_song.get('secondary_color_bias', 'none')
                            visualizer.song_primary_color = song_color
                            visualizer.song_secondary_color = secondary_color
                            print(f"Set fallback visualization colors: primary='{song_color}', secondary='{secondary_color}'")
                        
                        print(f"{mode} visualization started on primary display as fallback")
                        return True
                    else:
                        print(f"{mode} visualization failed on both external and primary displays")
                        # Don't show popup during song switching - just log the error
                        print(f"Visualization Error: Failed to start {mode} visualization.\n"
                              f"   Try: Check display connections, restart app, or use different mode")
                        return False
                
                return False
                
        except Exception as e:
            print(f"Exception starting {mode} visualization: {e}")
            # Don't show popup during song switching - just log the exception
            print(f"Visualization Exception: Error starting {mode} visualization: {str(e)}\n"
                  f"   Try restarting the application or selecting a different mode")
            return False
    
    def set_info_display(self, info_display):
        """Set the info display widget for logging"""
        self.info_display = info_display
        if hasattr(self, 'video_controls'):
            self.video_controls.set_info_display(info_display)
    
    def set_status_display(self, status_display):
        """Set the status display widget for logging"""
        self.status_display = status_display
        if hasattr(self, 'video_controls'):
            self.video_controls.set_status_display(status_display)