"""
Status Bar Widget for DMX Light Show Controller
Displays system status and provides interface controls
"""

import tkinter as tk
from tkinter import ttk
from .base_ui import BaseUIComponent, LoggingMixin


class StatusBarWidget(BaseUIComponent, LoggingMixin):
    """Widget for system status display and control"""

    def __init__(self, parent, controllers=None):
        # Basic displays (mixins expect these to exist)
        self.info_display = None
        self.status_display = None

        # Initialize tkinter variables used by the status bar
        self.status_text = tk.StringVar(value="Ready")
        self.dmx_mode_text = tk.StringVar(value="Simulate Mode")
        self.audio_level_text = tk.StringVar(value="Audio Level: 0%")
        self.tempo_text = tk.StringVar(value="Tempo: -- BPM")
        self.dmx_port_var = tk.StringVar(value="Auto-detect")
        self.audio_input_var = tk.StringVar(value="default")
        self.last_tempo = None

        # Call BaseUIComponent initializer which will call setup_ui()
        super().__init__(parent, controllers)

        # After UI is constructed, populate dynamic lists and start updates
        self._populate_audio_devices()
        self.refresh_dmx_ports()
        self._start_status_updates()
    
    def setup_ui(self):
        """Setup the status bar UI"""
        self.frame = ttk.Frame(self.parent)
        
        # Main status text
        status_label = ttk.Label(self.frame, textvariable=self.status_text, 
                                style='Status.TLabel')
        status_label.pack(side=tk.LEFT, padx=(5, 15))
        
        # Separator
        ttk.Separator(self.frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Hardware Controls Section
        hardware_frame = ttk.Frame(self.frame)
        hardware_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        # DMX Mode and Port selection
        dmx_frame = ttk.Frame(hardware_frame)
        dmx_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        dmx_mode_label = ttk.Label(dmx_frame, textvariable=self.dmx_mode_text, 
                                  style='Status.TLabel')
        dmx_mode_label.pack(side=tk.LEFT)
        
        self.dmx_port_combo = ttk.Combobox(dmx_frame, textvariable=self.dmx_port_var,
                                          width=20, state="readonly", 
                                          style='Status.TCombobox')
        self.dmx_port_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.dmx_port_combo.bind('<<ComboboxSelected>>', self.on_dmx_port_selected)
        
        # Microphone Input section with audio analysis below
        mic_section_frame = ttk.Frame(hardware_frame)
        mic_section_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        # Microphone selector (top row)
        mic_input_frame = ttk.Frame(mic_section_frame)
        mic_input_frame.pack(side=tk.TOP, anchor=tk.W)
        
        ttk.Label(mic_input_frame, text="Mic Input:", style='Status.TLabel').pack(side=tk.LEFT)
        
        self.audio_input_combo = ttk.Combobox(mic_input_frame, textvariable=self.audio_input_var,
                                             width=25, state="readonly", 
                                             style='Status.TCombobox')
        self.audio_input_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.audio_input_combo.bind('<<ComboboxSelected>>', self.on_audio_input_selected)
        
        # Audio analysis (bottom row)
        audio_analysis_frame = ttk.Frame(mic_section_frame)
        audio_analysis_frame.pack(side=tk.TOP, anchor=tk.W, pady=(3, 0))
        
        audio_level_label = ttk.Label(audio_analysis_frame, textvariable=self.audio_level_text, 
                                     style='Status.TLabel')
        audio_level_label.pack(side=tk.LEFT, padx=(0, 10))
        
        tempo_label = ttk.Label(audio_analysis_frame, textvariable=self.tempo_text, 
                               style='Status.TLabel')
        tempo_label.pack(side=tk.LEFT)
        
        # Separator
        ttk.Separator(self.frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Control Buttons Section
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(side=tk.RIGHT, padx=(0, 5))
        
        # DMX control buttons
        dmx_button_frame = ttk.Frame(button_frame)
        dmx_button_frame.pack(side=tk.LEFT, padx=(0, 5))
        
        toggle_dmx_button = ttk.Button(dmx_button_frame, text="Toggle DMX Mode",
                                      command=self.toggle_dmx_mode, width=12)
        toggle_dmx_button.pack(side=tk.LEFT, padx=(0, 2))
        
        self.simulator_button = ttk.Button(dmx_button_frame, text="Show Simulator",
                                          command=self.toggle_simulator, width=12)
        self.simulator_button.pack(side=tk.LEFT)
    
    def _start_status_updates(self):
        """Start the status update loop"""
        def update_status():
            try:
                audio_analyzer = self.get_controller('audio_analyzer')
                dmx_controller = self.get_controller('dmx_controller')
                if audio_analyzer:
                    audio_level = audio_analyzer.get_audio_level()
                    self.audio_level_text.set(f"Audio Level: {int(audio_level * 100)}%")
                    
                    # Update tempo with transition arrow (only when light show is active)
                    light_show_engine = self.get_controller('light_show_engine')
                    show_is_active = light_show_engine and light_show_engine.engine_active
                    
                    if show_is_active:
                        current_tempo = audio_analyzer.get_tempo()
                        if current_tempo > 0:  # Valid tempo detected
                            if self.last_tempo is not None and self.last_tempo != current_tempo:
                                # Show transition with arrow
                                self.tempo_text.set(f"Tempo: {self.last_tempo}→{current_tempo} BPM")
                            else:
                                # Show current tempo
                                self.tempo_text.set(f"Tempo: {current_tempo} BPM")
                            self.last_tempo = current_tempo
                        else:
                            self.tempo_text.set("Tempo: Detecting...")
                    else:
                        # Show waiting status when light show is not active
                        self.tempo_text.set("Tempo: -- BPM")
                        self.last_tempo = None  # Reset tempo tracking
                
                if dmx_controller:
                    mode = "Hardware" if not dmx_controller.simulate else "Simulate"
                    self.dmx_mode_text.set(f"DMX Mode: {mode}")
                
            except Exception as e:
                print(f"Status update error: {e}")
            
            # Schedule next update if frame still exists
            if hasattr(self, 'frame') and self.frame.winfo_exists():
                self.frame.after(100, update_status)
        
        # Start the update loop
        if hasattr(self, 'frame'):
            self.frame.after(100, update_status)
    
    def set_status(self, status_text):
        """Set the main status text"""
        self.status_text.set(status_text)
    
    def set_running_status(self, song_name):
        """Set status to running with song name"""
        self.status_text.set(f"Running: {song_name}")
    
    def set_ready_status(self):
        """Set status to ready"""
        self.status_text.set("Ready")
    
    def refresh_dmx_ports(self):
        """Refresh the list of available DMX interfaces"""
        try:
            dmx_controller = self.get_controller('dmx_controller')
            if not dmx_controller:
                return
            
            available_ports = dmx_controller.get_available_dmx_ports()
            
            # Build port list for dropdown
            port_options = ["Auto-detect"]
            
            for port_info in available_ports:
                device = port_info['device']
                interface_type = port_info.get('interface_type', 'Unknown')
                description = port_info['description']
                
                # Create readable port name
                if description and description != device:
                    display_name = f"{device} - {interface_type}"
                else:
                    display_name = f"{device} - {interface_type}"
                    
                port_options.append(display_name)
                
            # If no DMX ports found, show all serial ports
            if len(port_options) == 1:  # Only "Auto-detect"
                import serial.tools.list_ports
                for port in serial.tools.list_ports.comports():
                    port_options.append(f"{port.device} - {port.description or 'Serial Port'}")
            
            # Update combobox
            self.dmx_port_combo['values'] = port_options
            
            # Keep current selection if still valid
            current_value = self.dmx_port_var.get()
            if current_value not in port_options:
                self.dmx_port_var.set("Auto-detect")
                
            self.log_info(f"Found {len(port_options) - 1} potential DMX interfaces")
            
        except Exception as e:
            self.log_error(f"Failed to refresh DMX ports: {e}")
    
    def on_dmx_port_selected(self, event=None):
        """Handle DMX port selection"""
        try:
            dmx_controller = self.get_controller('dmx_controller')
            if not dmx_controller:
                return
            
            selected = self.dmx_port_var.get()
            
            if selected == "Auto-detect":
                # Reset to auto-detect mode
                dmx_controller.port = "/dev/tty.usbserial-*"
                self.log_info("DMX interface set to auto-detect")
            else:
                # Extract device name from display text
                device = selected.split(' - ')[0]
                dmx_controller.set_dmx_port(device)
                self.log_info(f"DMX interface set to: {device}")
                
            # If in hardware mode, reconnect with new port
            if not dmx_controller.simulate:
                dmx_controller._disconnect_hardware()
                dmx_controller._connect_hardware()
                
        except Exception as e:
            self.log_error(f"Failed to set DMX port: {e}")
    
    def toggle_dmx_mode(self):
        """Toggle between DMX hardware and simulator mode"""
        dmx_controller = self.get_controller('dmx_controller')
        if dmx_controller:
            dmx_controller.toggle_simulate_mode()
            mode = "Hardware" if not dmx_controller.simulate else "Simulate"
            print(f"🔧 DMX mode changed to: {mode}")

    def _populate_audio_devices(self):
        """Populate available audio input devices into the combobox."""
        try:
            # avoid hard dependency without raising at import time
            import sounddevice as sd
            devices = sd.query_devices()
            options = ['default']
            for i, dev in enumerate(devices):
                if dev.get('max_input_channels', 0) > 0:
                    name = dev.get('name', f"device_{i}")
                    options.append(f"{i}: {name}")

            self.audio_input_combo['values'] = options

            # load saved setting if available
            config = self.get_controller('config_manager')
            saved = None
            if config:
                saved = config.get_setting('audio', 'input_device')

            if saved is None:
                # attempt to pick a sensible macbook internal mic by name
                chosen = 'default'
                
                # First priority: exact "MacBook Pro Microphone" match
                for val in options:
                    if 'macbook pro microphone' in val.lower():
                        chosen = val
                        break
                
                # Second priority: any MacBook microphone
                if chosen == 'default':
                    for val in options:
                        if 'macbook' in val.lower() and ('microphone' in val.lower() or 'mic' in val.lower()):
                            chosen = val
                            break
                
                # Third priority: built-in or internal mics
                if chosen == 'default':
                    for val in options:
                        if 'built-in' in val.lower() or 'internal' in val.lower():
                            chosen = val
                            break
                
                self.audio_input_var.set(chosen)
                
                # Save the chosen default to config so it persists
                if config and chosen != 'default':
                    # Extract device index for saving
                    if ':' in chosen:
                        device_idx = chosen.split(':', 1)[0].strip()
                        try:
                            config.update_setting('audio', 'input_device', int(device_idx))
                        except:
                            config.update_setting('audio', 'input_device', chosen)
                    else:
                        config.update_setting('audio', 'input_device', chosen)
            else:
                # if saved is integer index, convert to label if possible
                if isinstance(saved, int):
                    # find matching option
                    match = next((o for o in options if o.startswith(f"{saved}: ")), None)
                    self.audio_input_var.set(match or 'default')
                else:
                    # assume string like 'default' or '0: Name'
                    self.audio_input_var.set(str(saved))

        except Exception as e:
            print(f"Could not enumerate audio devices: {e}")
            self.audio_input_combo['values'] = ['default']
            self.audio_input_var.set('default')

    def on_audio_input_selected(self, event=None):
        """Handle audio input device selection: persist and notify audio analyzer."""
        try:
            chosen = self.audio_input_var.get()
            config = self.get_controller('config_manager')
            # Save numeric index if we can parse it, else save as string
            idx = None
            if chosen and chosen != 'default' and ':' in chosen:
                try:
                    idx = int(chosen.split(':', 1)[0])
                except Exception:
                    idx = chosen
            elif chosen == 'default':
                idx = 'default'
            else:
                idx = chosen

            if config:
                config.update_setting('audio', 'input_device', idx)

            # Notify audio analyzer to switch device at runtime
            audio_analyzer = self.get_controller('audio_analyzer')
            if audio_analyzer:
                try:
                    audio_analyzer.set_input_device(None if idx == 'default' else idx)
                    self.log_info(f"Switched audio input to: {chosen}")
                except Exception as e:
                    self.log_error(f"Failed to set audio input device: {e}")

        except Exception as e:
            self.log_error(f"Error handling audio input selection: {e}")
    
    def test_dmx(self):
        """Test DMX output and show debug information"""
        try:
            dmx_controller = self.get_controller('dmx_controller')
            if not dmx_controller:
                return
            
            # Get current DMX status
            status = dmx_controller.get_dmx_status()
            
            # Create debug message
            debug_msg = f"DMX Status:\n"
            debug_msg += f"Mode: {'Simulate' if status['simulate'] else 'Hardware'}\n"
            debug_msg += f"Port: {status['port']}\n"
            debug_msg += f"PyDMX Available: {status['pydmx_available']}\n"
            debug_msg += f"Using PyDMX: {status['use_pydmx']}\n"
            debug_msg += f"PyDMX Connected: {status['pydmx_connected']}\n"
            debug_msg += f"Serial Connected: {status['serial_connected']}\n"
            debug_msg += f"Thread Running: {status['thread_running']}\n"
            debug_msg += f"Thread Alive: {status['thread_alive']}\n"
            debug_msg += f"Active Channels: {status['active_channels']}\n"
            debug_msg += f"Max Value: {status['max_value']}"
            
            # Test DMX output
            dmx_controller.test_dmx_output(channel=1, value=255)
            
            # Show status dialog
            from tkinter import messagebox
            messagebox.showinfo("DMX Test", debug_msg)
            
        except Exception as e:
            self.log_error(f"DMX test failed: {e}")
    
    def test_audio(self):
        """Test audio input"""
        audio_analyzer = self.get_controller('audio_analyzer')
        if audio_analyzer:
            level = audio_analyzer.get_audio_level()
            beat = audio_analyzer.detect_beat()
            from tkinter import messagebox
            messagebox.showinfo("Audio Test", 
                               f"Audio Level: {level:.2f}\nBeat Detected: {beat}")
    
    def toggle_simulator(self):
        """Toggle the DMX simulator window"""
        dmx_simulator = self.get_controller('dmx_simulator')
        dmx_controller = self.get_controller('dmx_controller')
        
        if not dmx_simulator or not dmx_controller:
            return
        
        if dmx_simulator.is_visible:
            dmx_simulator.hide_simulator()
            self.simulator_button.config(text="Show Simulator")
            self.set_status("DMX simulator hidden")
        else:
            # Make sure lights config is loaded
            lights_config = dmx_controller.get_lights_config()
            dmx_simulator.show_simulator(lights_config)
            self.simulator_button.config(text="Hide Simulator")
            self.set_status(f"DMX simulator shown with {len(lights_config.get('lights', {}))} lights")