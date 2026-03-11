"""
Modular DMX Light Show Controller GUI
Refactored version using modular components for better maintainability
"""

import tkinter as tk
from tkinter import ttk
import os
import subprocess
import threading
from pathlib import Path

# Import controllers
from dmx_controller import DMXController
from audio_analyzer import AudioAnalyzer
from config_manager import ConfigManager
from video_controller import VideoController
from visualization_controller import VisualizationController
from dmx_simulator import DMXSimulator
from color_engine import ColorEngine
from light_show_engine import LightShowEngine
from psychedelic_visualizer import PsychedelicVisualizer

# Import GUI modules
from gui.base_ui import StyleMixin, LoggingMixin
from gui.status_bar import StatusBarWidget
from gui.light_show import LightShowWidget
from gui.song_config import SongConfigWidget
from gui.light_config import LightConfigWidget
from gui.manual_controls import ManualControlsWidget



class ModularDMXLightShowGUI(StyleMixin):
    """Modular DMX Light Show GUI using component-based architecture"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("DMX Light Show Controller")
        
        # Calculate center position before setting geometry to avoid visible repositioning
        self._set_centered_geometry(1200, 900)
        
        # Configure styling
        self.setup_styles()
        
        # Initialize controllers
        self._init_controllers()
        
        # Create controller registry for components
        self.controllers = {
            'config_manager': self.config_manager,
            'dmx_controller': self.dmx_controller,
            'audio_analyzer': self.audio_analyzer,
            'video_controller': self.video_controller,
            'visualization_controller': self.visualization_controller,
            'psychedelic_visualizer': self.psychedelic_visualizer,
            'dmx_simulator': self.dmx_simulator,
            'color_engine': self.color_engine,
            'light_show_engine': self.light_show_engine,
            'status_bar': None,  # Will be set after creation
            'main_app': self,  # Add reference to main app for refresh notifications
        }
        
        # State variables
        self.is_running = False
        self.current_song = None
        
        # Create GUI components
        self._create_gui()
        
        # Start status updates
        self._start_status_updates()
        
        # Setup window closing handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _init_controllers(self):
        """Initialize all controllers"""
        # Clean up any existing media/visualization processes on startup
        self._cleanup_media_apps_on_startup()
        
        self.config_manager = ConfigManager()
        self.dmx_controller = DMXController(simulate=True)

        # Read preferred input device from settings (may be index or name)
        preferred_device = self.config_manager.get_setting('audio', 'input_device')
        # Normalize saved device: if it's 'default' or None, pass None to AudioAnalyzer
        # If it's a combobox label like '0: Name', extract numeric index
        if preferred_device == 'default' or preferred_device is None:
            normalized_device = None
        elif isinstance(preferred_device, int):
            normalized_device = preferred_device
        elif isinstance(preferred_device, str) and ':' in preferred_device:
            try:
                normalized_device = int(preferred_device.split(':', 1)[0].strip())
            except Exception:
                normalized_device = preferred_device
        else:
            normalized_device = preferred_device

        self.audio_analyzer = AudioAnalyzer(input_device=normalized_device, 
                                           blocksize=128, 
                                           ultra_low_latency=True)
        self.video_controller = VideoController()
        self.visualization_controller = VisualizationController()
        
        self.dmx_simulator = DMXSimulator(self.root)
        
        # Create intelligent light show system
        self.color_engine = ColorEngine()
        self.light_show_engine = LightShowEngine(self.color_engine)
        fullscreen_display = self.config_manager.get_setting('video', 'fullscreen_display') or 2
        self.psychedelic_visualizer = self.visualization_controller
        
        # Connect simulator to DMX controller
        self.dmx_controller.set_simulator(self.dmx_simulator)
        
        # Setup light groups when DMX controller loads config
        lights_config = self.dmx_controller.get_lights_config()
        self.light_show_engine.setup_light_groups(lights_config)
        
        # Auto-detect FTDI interface and switch to hardware mode if found
        self._auto_detect_ftdi()
    
    def _auto_detect_ftdi(self):
        """Auto-detect FTDI interface and switch to hardware mode if found"""
        try:
            print("DEBUG: Checking for FTDI interfaces...")
            
            # Check if FTDI interface is detected
            if self.dmx_controller.detect_ftdi_interface():
                print("FTDI interface detected! Automatically switching to Hardware mode...")
                
                # Switch to hardware mode
                if self.dmx_controller.simulate:
                    self.dmx_controller.toggle_simulate_mode()
                    print("DMX mode automatically changed to: Hardware")
                else:
                    print("Already in Hardware mode")
            else:
                print("No FTDI interface detected. Staying in Simulate mode.")
                
        except Exception as e:
            print(f"Error during FTDI auto-detection: {e}")
    
    def _cleanup_media_apps_on_startup(self):
        """Clean up any existing ffplay processes on startup to ensure clean state"""
        print("Cleaning up existing media processes...")
        
        try:
            # Clean up any existing ffplay processes
            result = subprocess.run(['pkill', '-f', 'ffplay'], 
                                 capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                print("  • Existing ffplay processes cleaned up")
            else:
                print("  • No existing ffplay processes found")
                
        except Exception as e:
            print(f"  • Warning: Could not clean up ffplay processes: {e}")
        
        # Small delay to ensure processes are fully terminated
        import time
        time.sleep(0.5)
    
    def _create_gui(self):
        """Create the modular GUI"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Logo and title container
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Try to load and display logo
        self._create_logo(header_frame)
        
        # Title
        title_label = ttk.Label(header_frame, text="DMX Light Show Controller", 
                               style='Title.TLabel')
        title_label.grid(row=1, column=0, pady=(5, 0))
        
        # Create status bar
        self.status_bar = StatusBarWidget(main_frame, self.controllers)
        self.status_bar.get_frame().grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Add status bar to controllers registry
        self.controllers['status_bar'] = self.status_bar
        
        # Create tabbed interface
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), 
                          pady=(10, 0))
        
        # Create tab components
        self._create_tabs()
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
    
    def _create_logo(self, parent_frame):
        """Create logo display - supports PNG, JPG, GIF images"""
        try:
            from PIL import Image, ImageTk
            import os
            
            # Look for logo files in common locations
            logo_paths = [
                "logo.png", "logo.jpg", "logo.gif", "logo.jpeg",
                "assets/logo.png", "assets/logo.jpg", 
                "images/logo.png", "images/logo.jpg",
                "resources/logo.png", "resources/logo.jpg"
            ]
            
            logo_found = False
            for logo_path in logo_paths:
                if os.path.exists(logo_path):
                    try:
                        # Load and resize image
                        image = Image.open(logo_path)
                        # Resize to reasonable size while maintaining aspect ratio
                        image.thumbnail((200, 100), Image.Resampling.LANCZOS)
                        self.logo_image = ImageTk.PhotoImage(image)
                        
                        # Create logo label
                        logo_label = ttk.Label(parent_frame, image=self.logo_image)
                        logo_label.grid(row=0, column=0, pady=(0, 5))
                        
                        print(f"Logo loaded from {logo_path}")
                        logo_found = True
                        break
                        
                    except Exception as e:
                        print(f"Failed to load logo from {logo_path}: {e}")
                        continue
            
            if not logo_found:
                # Create ASCII art logo as fallback
                logo_text = "DMX LIGHT SHOW"
                logo_label = ttk.Label(parent_frame, text=logo_text, 
                                     font=("Courier", 16, "bold"),
                                     foreground="#4A90E2")
                logo_label.grid(row=0, column=0, pady=(0, 5))
                print("No logo image found, using text logo")
                
        except ImportError:
            # PIL not available, create simple text logo
            logo_text = "DMX LIGHT SHOW"
            logo_label = ttk.Label(parent_frame, text=logo_text,
                                 font=("Helvetica", 14, "bold"))
            logo_label.grid(row=0, column=0, pady=(0, 5))
            print("PIL not available, using simple text logo")
            
        except Exception as e:
            print(f"Error creating logo: {e}")
            # Minimal fallback
            logo_label = ttk.Label(parent_frame, text="DMX Light Show",
                                 font=("Helvetica", 12, "bold"))
            logo_label.grid(row=0, column=0, pady=(0, 5))
    
    def _create_tabs(self):
        """Create all tab components"""
        # Light Show tab
        self.light_show_widget = LightShowWidget(self.notebook, self.controllers)
        self.notebook.add(self.light_show_widget.get_frame(), text="Light Show")
        
        # Song Configuration tab
        self.song_config_widget = SongConfigWidget(self.notebook, self.controllers)
        self.notebook.add(self.song_config_widget.get_frame(), text="Song Config")
        
        # DMX Configuration tab
        self.light_config_widget = LightConfigWidget(self.notebook, self.controllers)
        self.notebook.add(self.light_config_widget.get_frame(), text="DMX Config")
        
        # Manual Controls tab
        self.manual_controls_widget = ManualControlsWidget(self.notebook, self.controllers)
        self.notebook.add(self.manual_controls_widget.get_frame(), text="Manual Control")
        
        # Setup logging displays
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging displays for all components"""
        # Info display was removed, so use status display for all logging
        status_display = self.manual_controls_widget.get_status_display()
        
        # Set logging displays for all components that need them
        components_with_logging = [
            self.status_bar,
            self.light_show_widget,
            self.song_config_widget,
            self.light_config_widget,
            self.manual_controls_widget
        ]
        
        for component in components_with_logging:
            if hasattr(component, 'set_info_display'):
                component.set_info_display(status_display)  # Use status display instead
            if hasattr(component, 'set_status_display'):
                component.set_status_display(status_display)
    
    def _start_status_updates(self):
        """Start status update system"""
        # The status bar handles its own updates
        pass
    
    def on_closing(self):
        """Handle application closing"""
        # Stop any running shows
        if hasattr(self.light_show_widget, 'is_show_running') and self.light_show_widget.is_show_running():
            self.light_show_widget.stop_show()
        
        # Stop any running audio tests
        if hasattr(self.manual_controls_widget, 'stop_audio_test'):
            self.manual_controls_widget.stop_audio_test()
            
        # Cleanup controllers
        try:
            self.audio_analyzer.stop()
        except Exception as e:
            print(f"Error stopping audio analyzer: {e}")
        try:
            self.video_controller.stop()
        except Exception as e:
            print(f"Error stopping video controller: {e}")
        try:
            self.visualization_controller.stop()
        except Exception as e:
            print(f"Error stopping visualization controller: {e}")
        try:
            self.dmx_simulator.destroy()
        except Exception as e:
            print(f"Error destroying DMX simulator: {e}")
        
            
        self.root.destroy()
    
    def _set_centered_geometry(self, width, height):
        """Set window geometry with centered position from the start"""
        # Get screen dimensions (this works even before window is shown)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate center position
        x = (screen_width - width) // 2
        y = 0
        
        # Set geometry with position in one call - this prevents visible repositioning
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def get_widget(self, widget_name):
        """Get a widget by name for external access"""
        widget_map = {
            'status_bar': self.status_bar,
            'light_show': self.light_show_widget,
            'song_config': self.song_config_widget,
            'light_config': self.light_config_widget,
            'manual_controls': self.manual_controls_widget
        }
        return widget_map.get(widget_name)
    
    def get_controller(self, controller_name):
        """Get a controller by name for external access"""
        return self.controllers.get(controller_name)
    
    def refresh_all_data(self):
        """Refresh data in all widgets"""
        # Refresh songs in relevant widgets
        if hasattr(self.light_show_widget, 'refresh_songs'):
            self.light_show_widget.refresh_songs()
        
        if hasattr(self.song_config_widget, 'refresh_songs_list'):
            self.song_config_widget.refresh_songs_list()
        
        # Refresh lights in light config
        if hasattr(self.light_config_widget, 'refresh_lights_list'):
            self.light_config_widget.refresh_lights_list()
        
        # Refresh DMX ports in status bar
        if hasattr(self.status_bar, 'refresh_dmx_ports'):
            self.status_bar.refresh_dmx_ports()


def main():
    """Main entry point for the modular GUI"""
    
    # Global macOS alert suppression for entire application
    if os.name == 'posix':  # macOS/Unix
        try:
            # Suppress macOS system dialogs and alerts globally
            os.environ['NSAlert'] = 'false'
            os.environ['NSAppSuppressLogging'] = 'YES'
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            # Suppress macOS audio alerts and sounds
            os.environ['NSBeep'] = 'false'
            os.environ['NSSystemSoundDelegate'] = 'false'  
            os.environ['NSAlertSuppressionKey'] = 'true'
            # Additional macOS notification suppression
            os.environ['NSApplicationPresentationOptions'] = 'NSApplicationPresentationDefault'
            os.environ['NSWorkspaceNotificationCenter'] = 'false'
            
            # Try to disable system alert sounds via AppleScript
            try:
                disable_sounds_script = '''
                tell application "System Events"
                    set volume alert volume 0
                end tell
                '''
                subprocess.run(['osascript', '-e', disable_sounds_script], 
                             capture_output=True, timeout=2, check=False)
                print("Applied global macOS alert and sound suppression")
            except:
                print("Applied global macOS alert suppression (sound suppression may not have worked)")
        except Exception as e:
            print(f"Could not apply global alert suppression: {e}")
    
    root = tk.Tk()
    app = ModularDMXLightShowGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    # Bring window to foreground at startup
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(lambda: root.attributes('-topmost', False))
    root.focus_force()
    
    # Additional macOS-specific activation
    if os.name == 'posix':  # macOS/Unix
        try:
            # Use AppleScript to bring Python to foreground on macOS
            subprocess.run(['osascript', '-e', 'tell application "Python" to activate'], 
                         capture_output=True, timeout=2)
        except:
            # Fallback: try to activate current process
            try:
                subprocess.run(['osascript', '-e', 'tell application "System Events" to set frontmost of first process whose unix id is {} to true'.format(os.getpid())], 
                             capture_output=True, timeout=2)
            except:
                pass  # If AppleScript fails, just continue with tkinter methods
    
    root.mainloop()


if __name__ == "__main__":
    main()
