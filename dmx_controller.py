import serial.tools.list_ports
import time
import json
import threading
from typing import Dict, List, Optional

# PyDMX imports for proper FTDI support
try:
    from dmx import DMXInterface
    PYDMX_AVAILABLE = True
    # PyDMX loaded
except ImportError as e:
    # PyDMX not available - using serial fallback
    PYDMX_AVAILABLE = False
    import serial

class DMXController:
    def __init__(self, simulate: bool = True, port: str = "/dev/tty.usbserial-*"):
        self.simulate = simulate
        self.port = port
        self.dmx_interface = None  # PyDMX interface
        self.serial_connection = None  # Fallback for non-FTDI
        self.dmx_data = [0] * 512  # DMX universe (512 channels)
        self.lights_config = {}
        self.simulator = None  # Will be set by GUI
        self.use_pydmx = PYDMX_AVAILABLE and not simulate
        
        # DMX timing and threading (only needed for fallback serial)
        self.dmx_refresh_rate = 40  # Hz (40 FPS for smooth DMX)
        self.dmx_thread = None
        self.dmx_running = False
        self.dmx_lock = threading.Lock()
        
        # Load lights configuration
        self.load_lights_config()
        
        if not simulate:
            self._connect_hardware()
    
    def detect_ftdi_interface(self) -> bool:
        """Detect if FTDI interface is available for DMX hardware"""
        try:
            # First check if PyDMX is available
            if not PYDMX_AVAILABLE:
                pass  # PyDMX not available
                return False
            
            # Check for FTDI devices in available ports
            available_ports = self.get_available_dmx_ports()
            ftdi_found = False
            
            for port_info in available_ports:
                interface_type = port_info.get('interface_type', '')
                if 'FTDI' in interface_type:
                    print(f"✅ Found FTDI DMX interface: {port_info['device']}")
                    ftdi_found = True
            
            # Also try to create a DMX interface to verify FTDI is working
            if ftdi_found:
                try:
                    test_interface = DMXInterface("FT232R")
                    test_interface.open()
                    test_interface.close()
                    # FTDI test successful
                    return True
                except Exception as e:
                    pass  # FTDI test failed
                    return False
            
            return False
            
        except Exception as e:
            pass  # Error detecting FTDI interface
            return False
    
    def set_simulator(self, simulator):
        """Set the DMX simulator for visual feedback"""
        self.simulator = simulator
        
        # If simulator is set and we have lights config, update the simulator
        if self.simulator and self.lights_config:
            print(f"🎭 DMX Simulator: {len(self.lights_config.get('lights', {}))} lights configured")
            # Don't show it automatically, just prepare it with the config
            if hasattr(self.simulator, 'lights_config'):
                self.simulator.lights_config = self.lights_config
            
    def toggle_simulate_mode(self):
        """Toggle between simulate and hardware mode"""
        self.simulate = not self.simulate
        if not self.simulate:
            self._connect_hardware()
        else:
            self._disconnect_hardware()
            
    def _connect_hardware(self):
        """Connect to DMX hardware via USB using PyDMX for FTDI or fallback to serial"""
        try:
            # Try PyDMX with FT232R driver
            if PYDMX_AVAILABLE:
                try:
                    self.dmx_interface = DMXInterface("FT232R")
                    self.dmx_interface.open()
                    self.use_pydmx = True
                    print("✅ Connected to DMX hardware via FTDI")
                    return
                except Exception as e:
                    self.dmx_interface = None
            
            # Fallback to serial method for non-FTDI devices
            available_ports = self.get_available_dmx_ports()
            
            print(f"🔍 Scanning {len(available_ports)} serial ports for DMX interfaces...")
            for i, port_info in enumerate(available_ports):
                print(f"  {i+1}. {port_info['device']} - {port_info.get('interface_type', 'Unknown')}")
            
            if not available_ports:
                print("⚠️  No DMX interfaces found. Available ports:")
                for port in serial.tools.list_ports.comports():
                    print(f"  {port.device} - {port.description} (VID:{port.vid:04X}, PID:{port.pid:04X})")
                self.simulate = True
                return
                
            # Use the first available DMX port or the configured port if available
            selected_port = None
            if self.port and self.port != "/dev/tty.usbserial-*":
                # Check if the configured port is available
                for port_info in available_ports:
                    if port_info['device'] == self.port:
                        selected_port = self.port
                        break
            
            if not selected_port and available_ports:
                selected_port = available_ports[0]['device']
                
            if selected_port and not PYDMX_AVAILABLE:
                print(f"🔌 Connecting to DMX interface: {selected_port}")
                # Configure for DMX512: 250kbps, 8N2
                self.serial_connection = serial.Serial(
                    port=selected_port,
                    baudrate=250000,  # DMX512 standard baud rate
                    bytesize=8,
                    parity=serial.PARITY_NONE,
                    stopbits=2,
                    timeout=0.1,
                    write_timeout=0.1
                )
                self.port = selected_port
                self.use_pydmx = False
                print(f"✅ DMX serial connection established: {selected_port}")
                self._start_dmx_thread()  # Only needed for serial fallback
            else:
                print("❌ No suitable DMX interface found")
                self.simulate = True
                
        except Exception as e:
            print(f"Failed to connect to DMX hardware: {e}")
            import traceback
            traceback.print_exc()
            self.simulate = True
            
    def _disconnect_hardware(self):
        """Disconnect from DMX hardware"""
        self._stop_dmx_thread()
        
        # Close PyDMX interface
        if self.dmx_interface:
            try:
                self.dmx_interface.close()
                # PyDMX interface closed
            except:
                pass
            self.dmx_interface = None
            
        # Close serial connection (fallback)
        if self.serial_connection:
            try:
                self.serial_connection.close()
                # Serial connection closed
            except:
                pass
            self.serial_connection = None
            
    def load_lights_config(self, config_path: str = "config/lights.json"):
        """Load light configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                self.lights_config = json.load(f)
        except FileNotFoundError:
            # Create default config if file doesn't exist
            self._create_default_lights_config(config_path)
            
        # Update simulator with new lights config
        if self.simulator and self.lights_config:
            print(f"🎭 DMX Simulator updated: {len(self.lights_config.get('lights', {}))} lights")
            # If simulator is visible, update its layout
            if hasattr(self.simulator, 'is_visible') and self.simulator.is_visible:
                self.simulator.lights_config = self.lights_config
                self.simulator._update_layout()
            
    def _create_default_lights_config(self, config_path: str):
        """Create a default lights configuration file"""
        default_config = {
            "lights": {
                "light1": {
                    "name": "Main Stage Light 1",
                    "address": 1,
                    "channels": {
                        "red": 1,
                        "green": 2,
                        "blue": 3,
                        "dimmer": 4
                    }
                },
                "light2": {
                    "name": "Main Stage Light 2", 
                    "address": 5,
                    "channels": {
                        "red": 5,
                        "green": 6,
                        "blue": 7,
                        "dimmer": 8
                    }
                },
                "light3": {
                    "name": "Back Light 1",
                    "address": 9,
                    "channels": {
                        "red": 9,
                        "green": 10,
                        "blue": 11,
                        "dimmer": 12
                    }
                }
            }
        }
        
        # Create config directory if it doesn't exist
        import os
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
            
        self.lights_config = default_config
        
    def update_lights(self, colors: Dict[str, int], intensity: Optional[int] = None):
        """Update all lights with the given RGB values and optional intensity."""
        if not self.lights_config:
            self.load_lights_config()

        r = int(colors.get('r', 0))
        g = int(colors.get('g', 0))
        b = int(colors.get('b', 0))

        for light_id in self.lights_config.get('lights', {}):
            self.set_light_rgb(light_id, r, g, b, intensity)
        
        self._send_dmx_data()

        if self.simulator:
            self.simulator.update_all_lights({'r': r, 'g': g, 'b': b})

    def set_light_rgb(self, light_id: str, r: int, g: int, b: int, intensity: Optional[int] = None):
        """Set RGB and intensity for a specific light."""
        try:
            if light_id not in self.lights_config.get('lights', {}):
                return False

            light_config = self.lights_config['lights'][light_id]
            channels = light_config.get('channels', {})
            max_intensity = light_config.get('max_intensity', 0)
            light_type = light_config.get('type', '').lower()

            # If intensity is not provided, use the max of RGB as a fallback
            dimmer_value = intensity if intensity is not None else max(r, g, b)

            # Handle brightness and color rules based on light type
            if light_type == 'wash':
                # Wash lights: Always use max brightness (255) for both dimmer and colors
                original_dimmer = dimmer_value
                dimmer_value = 255
                # Colors are used as-is (should already be at full intensity from light engine)
                color_r, color_g, color_b = r, g, b
                if original_dimmer != dimmer_value and (r > 0 or g > 0 or b > 0):
                    # print(f"WASH OVERRIDE: {light_id} dimmer {original_dimmer} -> 255, colors R={color_r} G={color_g} B={color_b}")
                    pass  # Debug message commented out
            elif light_type == 'par':
                # PAR lights: Colors always at max when supposed to be on, but dimmer respects max_intensity
                if r > 0 or g > 0 or b > 0:  # If any color is supposed to be on
                    # Normalize colors to maximum intensity while preserving ratios
                    max_color = max(r, g, b)
                    if max_color > 0:
                        color_r = int((r / max_color) * 255)
                        color_g = int((g / max_color) * 255) 
                        color_b = int((b / max_color) * 255)
                        if max_color < 255:
                            # print(f"PAR COLOR BOOST: {light_id} colors ({r},{g},{b}) -> ({color_r},{color_g},{color_b}), dimmer={dimmer_value}")
                            pass  # Debug message commented out
                    else:
                        color_r, color_g, color_b = 0, 0, 0
                else:
                    color_r, color_g, color_b = 0, 0, 0
                
                # Dimmer respects max_intensity limit for PARs
                original_dimmer = dimmer_value
                if max_intensity > 0:
                    dimmer_value = min(dimmer_value, max_intensity)
                    if original_dimmer != dimmer_value:
                        print(f"PAR DIMMER LIMIT: {light_id} dimmer {original_dimmer} -> {dimmer_value} (max={max_intensity})")
            else:
                # Default behavior for other light types
                color_r, color_g, color_b = r, g, b
                if max_intensity > 0:
                    dimmer_value = min(dimmer_value, max_intensity)

            with self.dmx_lock:
                if 'red' in channels:
                    self.dmx_data[channels['red'] - 1] = color_r
                if 'green' in channels:
                    self.dmx_data[channels['green'] - 1] = color_g
                if 'blue' in channels:
                    self.dmx_data[channels['blue'] - 1] = color_b
                if 'dimmer' in channels:
                    self.dmx_data[channels['dimmer'] - 1] = dimmer_value
                
                # Send DMX data while holding the lock (avoid double locking)
                self._send_dmx_data_locked()

            if self.simulator:
                self.simulator.update_light_color(light_id, color_r, color_g, color_b, dimmer_value)

            return True
        except Exception as e:
            print(f"ERROR: DMX set_light_rgb failed for {light_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def set_channel(self, channel: int, value: int):
        """Set a specific DMX channel value (1-512)"""
        if 1 <= channel <= 512:
            with self.dmx_lock:
                self.dmx_data[channel - 1] = max(0, min(255, value))
            self._send_dmx_data()
            
    def all_lights_off(self):
        """Turn off all lights"""
        with self.dmx_lock:
            self.dmx_data = [0] * 512
        self._send_dmx_data()
        
        # Update simulator if available (show in both simulate and hardware mode)
        if self.simulator:
            # Turning off lights
            self.simulator.turn_off_all_lights()
        else:
            # No simulator available
            pass
        
    def _start_dmx_thread(self):
        """Start the DMX transmission thread"""
        if not self.simulate and not self.dmx_running:
            self.dmx_running = True
            self.dmx_thread = threading.Thread(target=self._dmx_transmission_loop, daemon=True)
            self.dmx_thread.start()
            print(f"🎭 DMX thread started (Mode: {'Simulate' if self.simulate else 'Hardware'})")
        else:
            print("⚠️  DMX thread already running")
            
    def _stop_dmx_thread(self):
        """Stop the DMX transmission thread"""
        if self.dmx_running:
            self.dmx_running = False
            if self.dmx_thread and self.dmx_thread.is_alive():
                self.dmx_thread.join(timeout=1.0)
            print("🎭 DMX thread stopped")
    
    def _dmx_transmission_loop(self):
        """Continuous DMX transmission loop at specified refresh rate"""
        frame_time = 1.0 / self.dmx_refresh_rate  # Time between frames
        frame_count = 0
        
        print(f"🎭 DMX transmission started: {self.dmx_refresh_rate}Hz refresh rate")
        
        while self.dmx_running and self.serial_connection:
            start_time = time.time()
            
            try:
                with self.dmx_lock:
                    self._send_dmx_packet()
                frame_count += 1
                
                # Debug output every 1000 frames (25 seconds at 40Hz) - much less frequent
                if frame_count % 1000 == 0:
                    active_channels = sum(1 for val in self.dmx_data if val > 0)
                    print(f"🎭 DMX: {frame_count} frames sent, {active_channels} active channels")
                    
            except Exception as e:
                print(f"DMX transmission error: {e}")
                
            # Maintain consistent frame rate
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_time - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
                
        print("🎭 DMX transmission stopped")
                
    def _send_dmx_packet(self):
        """Send a single DMX512 packet with proper timing"""
        if not self.serial_connection:
            pass  # No serial connection - expected in simulate mode
            return
            
        try:
            # Step 1: Send break (88-176 microseconds of low signal)
            # pyserial's send_break() duration varies by platform, typically ~0.25ms
            self.serial_connection.send_break(duration=0.0001)  # 100 microseconds
            
            # Step 2: Mark After Break (8-12 microseconds of high signal)
            # This is automatically handled by the UART after break
            
            # Step 3: Send DMX packet (513 bytes: start code + 512 channel data)
            # Start code (0x00 for standard DMX)
            packet = bytearray([0x00])  # DMX start code
            packet.extend(self.dmx_data)   # 512 channel bytes
            
            # Send the complete 513-byte packet
            bytes_written = self.serial_connection.write(packet)
            
            # Ensure data is transmitted immediately
            self.serial_connection.flush()
            
            if bytes_written != 513:
                print(f"WARNING: DMX packet incomplete ({bytes_written}/513 bytes)")
                
        except Exception as e:
            print(f"ERROR: Failed to send DMX packet: {e}")
            # If we get serial errors, the connection might be bad
            import traceback
            traceback.print_exc()
            
    def _send_dmx_data_locked(self):
        """Send DMX data while already holding the lock (avoid deadlock)"""
        if self.simulate:
            # In simulate mode, only log significant changes (not every packet)
            pass  # Removed excessive per-packet logging - visual feedback via simulator is sufficient
        elif self.use_pydmx and self.dmx_interface:
            # PyDMX handles timing automatically - send immediately (lock already held)
            try:
                # PyDMX uses set_frame with the complete 512-channel array
                self.dmx_interface.set_frame(self.dmx_data)
                self.dmx_interface.send_update()
                    
            except Exception as e:
                print(f"ERROR: PyDMX send failed: {e}")
                import traceback
                traceback.print_exc()
        # Serial fallback uses background thread (existing code)
    
    def _send_dmx_data(self):
        """Send DMX data using PyDMX (immediate) or queue for serial thread"""
        with self.dmx_lock:
            self._send_dmx_data_locked()
                    
    def get_lights_config(self):
        """Get the current lights configuration"""
        if not self.lights_config:
            self.load_lights_config()
        return self.lights_config
        
    def save_lights_config(self, config_path: str = "config/lights.json"):
        """Save the current lights configuration"""
        with open(config_path, 'w') as f:
            json.dump(self.lights_config, f, indent=2)
            
    def get_available_dmx_ports(self) -> List[Dict]:
        """Get list of available DMX interface ports"""
        dmx_ports = []
        
        for port in serial.tools.list_ports.comports():
            port_info = {
                'device': port.device,
                'description': port.description or '',
                'manufacturer': port.manufacturer or '',
                'vid': port.vid,
                'pid': port.pid,
                'serial_number': port.serial_number or ''
            }
            
            # Check for known DMX interface patterns
            is_dmx_port = False
            
            # FT232RNL chip (FTDI-based interfaces)
            if port.vid == 0x0403:  # FTDI vendor ID
                if port.pid in [0x6001, 0x6015]:  # FT232R/FT230X/FT231X/FT234XD
                    is_dmx_port = True
                    port_info['interface_type'] = 'FTDI FT232/FT230 Series'
            
            # Check for DMX-related keywords in description
            dmx_keywords = ['dmx', 'lighting', 'enttec', 'art-net', 'sacn']
            desc_lower = port_info['description'].lower()
            if any(keyword in desc_lower for keyword in dmx_keywords):
                is_dmx_port = True
                port_info['interface_type'] = 'DMX Interface'
            
            # macOS USB-Serial patterns
            if port.device.startswith('/dev/tty.usbserial'):
                is_dmx_port = True
                if 'interface_type' not in port_info:
                    port_info['interface_type'] = 'USB-Serial Adapter'
            
            # Also include any FTDI-based device as potential DMX interface
            if 'ftdi' in desc_lower or 'ft232' in desc_lower:
                is_dmx_port = True
                if 'interface_type' not in port_info:
                    port_info['interface_type'] = 'FTDI USB-Serial'
            
            if is_dmx_port:
                dmx_ports.append(port_info)
                
        return dmx_ports
        
    def set_dmx_port(self, port: str):
        """Set the DMX interface port"""
        self.port = port
        if not self.simulate:
            self._disconnect_hardware()
            self._connect_hardware()
            
    def test_dmx_output(self, channel: int = 1, value: int = 255):
        """Test function to manually set a DMX channel and verify output"""
        print(f"🧪 Testing DMX Channel {channel} = {value}")
        self.set_channel(channel, value)
        
        # Show current state
        active_channels = [(i+1, val) for i, val in enumerate(self.dmx_data) if val > 0]
        if active_channels:  # Only show if there are active channels
            print(f"📡 Active channels: {active_channels[:5]}")  # Show only first 5
        
        # Force an immediate packet send in simulate mode for testing
        if self.simulate:
            pass  # Simulate mode - no hardware output
        else:
            print(f"🔧 Hardware mode active, thread running: {self.dmx_running}")
            
    def get_dmx_status(self):
        """Get current DMX system status for debugging"""
        status = {
            'simulate': self.simulate,
            'port': self.port,
            'use_pydmx': self.use_pydmx,
            'pydmx_available': PYDMX_AVAILABLE,
            'pydmx_connected': self.dmx_interface is not None,
            'serial_connected': self.serial_connection is not None,
            'thread_running': self.dmx_running,
            'thread_alive': self.dmx_thread.is_alive() if self.dmx_thread else False,
            'active_channels': sum(1 for val in self.dmx_data if val > 0),
            'max_value': max(self.dmx_data) if any(self.dmx_data) else 0
        }
        return status
    
    def __del__(self):
        """Cleanup when controller is destroyed"""
        self._stop_dmx_thread()
        if self.serial_connection:
            self.serial_connection.close()