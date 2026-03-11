"""
Manual Controls Widget for DMX Light Show Controller
Handles manual light control and audio testing
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from .base_ui import BaseUIComponent, LoggingMixin, FormHelper, VariableManager


class ManualControlsWidget(BaseUIComponent, LoggingMixin):
    """Widget for manual light controls and testing"""

    def __init__(self, parent, controllers=None):
        self.variables = VariableManager()
        self.audio_test_running = False
        # Initialize logging mixin
        self.info_display = None
        self.status_display = None
        # Setup RGB variables BEFORE calling super() which calls setup_ui()
        self._setup_rgb_variables()
        super().__init__(parent, controllers)
        # Setup remaining variables that need controllers
        self._setup_remaining_variables()

    def setup_ui(self):
        """Setup manual controls UI"""
        self.frame = ttk.Frame(self.parent, padding="10")
    # Create control sections
        self._create_global_controls()
        self._create_audio_test_controls(self.frame)
        self._create_status_display()

        # Configure grid weights
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(3, weight=1)

    def _setup_rgb_variables(self):
        """Setup RGB variables that sliders need (before GUI creation)"""
        self.variables.add_int_var('manual_r', 0)
        self.variables.add_int_var('manual_g', 0)
        self.variables.add_int_var('manual_b', 0)

    def _setup_remaining_variables(self):
        """Setup remaining variables that need controllers (after GUI creation)"""
        self.variables.add_string_var('test_color', 'white')
        self.variables.add_string_var('test_mode', 'medium')

        # Load saved sensitivity
        config_manager = self.get_controller('config_manager')
        saved_sensitivity = 0.3
        if config_manager:
            saved_sensitivity = config_manager.get_setting("audio", "beat_threshold") or 0.3

        self.variables.add_double_var('sensitivity', saved_sensitivity)

        # Apply saved sensitivity to audio analyzer
        audio_analyzer = self.get_controller('audio_analyzer')
        if audio_analyzer:
            audio_analyzer.set_beat_threshold(saved_sensitivity)

    def _create_global_controls(self):
        """Create global light control section"""
        global_frame = ttk.LabelFrame(self.frame, text="Global Light Control", padding="10")
        # Place below the input device selector (row 1)
        global_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # RGB sliders
        self._create_color_sliders(global_frame)

        # Control buttons
        self._create_control_buttons(global_frame)

        global_frame.columnconfigure(1, weight=1)

    def _create_color_sliders(self, parent):
        """Create RGB color sliders"""
        colors = [('Red', 'manual_r'), ('Green', 'manual_g'), ('Blue', 'manual_b')]

        for i, (label, var_name) in enumerate(colors):
            ttk.Label(parent, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, pady=(5 if i > 0 else 0, 0))

            var = self.variables.get_var(var_name)
            color_scale = ttk.Scale(parent, from_=0, to=255, variable=var,
                                   orient=tk.HORIZONTAL, length=200)
            color_scale.grid(row=i, column=1, padx=(10, 5), sticky=(tk.W, tk.E), pady=(5 if i > 0 else 0, 0))

            ttk.Label(parent, textvariable=var, width=5).grid(
                row=i, column=2, pady=(5 if i > 0 else 0, 0))

    def _create_control_buttons(self, parent):
        """Create control buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0))

        ttk.Button(button_frame, text="Apply Colors",
                  command=self.apply_manual_colors).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="All Lights Off",
                  command=self.all_lights_off).grid(row=0, column=1, padx=(0, 10))

        self.simulator_button = ttk.Button(button_frame, text="Show Simulator",
                                          command=self.toggle_simulator)
        self.simulator_button.grid(row=0, column=2)

        ttk.Button(button_frame, text="Test Simulator",
                  command=self.test_simulator_direct).grid(row=0, column=3, padx=(10, 0))

        ttk.Button(button_frame, text="Test DMX",
                  command=self.test_dmx).grid(row=0, column=4, padx=(10, 0))

    def _create_audio_test_controls(self, parent):
        """Create audio reactive test controls"""
        # Place below global controls (row 2)
        audio_frame = ttk.LabelFrame(self.frame, text="Audio Reactive Test", padding="10")
        audio_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Test configuration row
        ttk.Label(audio_frame, text="Test Color:").grid(row=0, column=0, sticky=tk.W)

        config_manager = self.get_controller('config_manager')
        color_options = config_manager.get_color_options() if config_manager else ['white', 'red', 'green', 'blue']

        test_color_combo = ttk.Combobox(audio_frame, textvariable=self.variables.get_var('test_color'),
                                       values=color_options, state="readonly", width=15)
        test_color_combo.grid(row=0, column=1, padx=(10, 0), sticky=tk.W)

        ttk.Label(audio_frame, text="Test Mode:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))

        reactivity_options = config_manager.get_reactivity_options() if config_manager else ['low', 'medium', 'high']

        test_mode_combo = ttk.Combobox(audio_frame, textvariable=self.variables.get_var('test_mode'),
                                       values=reactivity_options, state="readonly", width=15)
        test_mode_combo.grid(row=0, column=3, padx=(10, 0), sticky=tk.W)

        # Microphone sensitivity controls (row 1)
        self._create_sensitivity_controls(audio_frame)

        # Test button (row 2)
        test_button_frame = ttk.Frame(audio_frame)
        test_button_frame.grid(row=2, column=0, columnspan=4, pady=(10, 0))

        self.audio_test_button = ttk.Button(test_button_frame, text="Start Audio Test",
                                           command=self.toggle_audio_test)
        self.audio_test_button.grid(row=0, column=0, padx=(0, 10))

        ttk.Button(test_button_frame, text="Test Audio",
                  command=self.test_audio).grid(row=0, column=1)

    def _create_sensitivity_controls(self, parent):
        """Create microphone sensitivity controls"""
        ttk.Label(parent, text="Mic Sensitivity:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))

        sensitivity_scale = ttk.Scale(parent, from_=0.1, to=1.0, variable=self.variables.get_var('sensitivity'),
                                    orient=tk.HORIZONTAL, length=150, command=self.update_sensitivity)
        sensitivity_scale.grid(row=1, column=1, padx=(10, 5), sticky=(tk.W, tk.E), pady=(10, 0))

        sensitivity_value = self.variables.get_value('sensitivity') or 0.3
        self.sensitivity_label = ttk.Label(parent, text=f"{sensitivity_value:.2f}", width=5)
        self.sensitivity_label.grid(row=1, column=2, sticky=tk.W, pady=(10, 0))

        ttk.Label(parent, text="(0.1=Very Sensitive, 1.0=Less Sensitive)").grid(
            row=1, column=3, sticky=tk.W, padx=(10, 0), pady=(10, 0))

    def _create_status_display(self):
        """Create system status display"""
        # Place at the bottom (row 3)
        status_frame = ttk.LabelFrame(self.frame, text="System Status", padding="10")
        status_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.status_display = tk.Text(status_frame, height=8, width=70, state=tk.DISABLED)
        status_scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL,
                                        command=self.status_display.yview)
        self.status_display.config(yscrollcommand=status_scrollbar.set)

        self.status_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        status_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)

        # Override the set_status_display method to use our status display
        self.set_status_display(self.status_display)

    # input device selector was moved to the status bar to avoid duplication

    def apply_manual_colors(self):
        """Apply manual RGB colors to all lights"""
        colors = {
            'r': self.variables.get_value('manual_r'),
            'g': self.variables.get_value('manual_g'),
            'b': self.variables.get_value('manual_b')
        }

        dmx_controller = self.get_controller('dmx_controller')
        if dmx_controller:
            dmx_controller.update_lights(colors)
            self.log_status(f"Applied manual colors: R={colors['r']}, G={colors['g']}, B={colors['b']}")
        else:
            self.log_status("Error: No DMX controller available")

    def all_lights_off(self):
        """Turn off all lights"""
        dmx_controller = self.get_controller('dmx_controller')
        if dmx_controller:
            dmx_controller.all_lights_off()
            self.variables.set_value('manual_r', 0)
            self.variables.set_value('manual_g', 0)
            self.variables.set_value('manual_b', 0)
            self.log_status("All lights turned off")

    def update_sensitivity(self, value=None):
        """Update microphone sensitivity setting"""
        sensitivity = self.variables.get_value('sensitivity')

        # Update the audio analyzer beat threshold
        audio_analyzer = self.get_controller('audio_analyzer')
        if audio_analyzer:
            audio_analyzer.set_beat_threshold(sensitivity)

        # Save the setting to config
        config_manager = self.get_controller('config_manager')
        if config_manager:
            config_manager.update_setting("audio", "beat_threshold", sensitivity)

        # Update the display label
        self.sensitivity_label.config(text=f"{sensitivity:.2f}")

        self.log_status(f"Microphone sensitivity set to {sensitivity:.2f}")

    def toggle_simulator(self):
        """Toggle the DMX simulator window"""
        dmx_simulator = self.get_controller('dmx_simulator')
        dmx_controller = self.get_controller('dmx_controller')

        if not dmx_simulator or not dmx_controller:
            return

        if dmx_simulator.is_visible:
            dmx_simulator.hide_simulator()
            self.simulator_button.config(text="Show Simulator")
            self.log_status("DMX simulator hidden")
        else:
            # Make sure lights config is loaded
            lights_config = dmx_controller.get_lights_config()
            print(f"DEBUG: Showing simulator with {len(lights_config.get('lights', {}))} lights")

            dmx_simulator.show_simulator(lights_config)
            self.simulator_button.config(text="Hide Simulator")
            self.log_status(f"DMX simulator shown with {len(lights_config.get('lights', {}))} lights")

            # Test the simulator with a quick color flash to verify it's working
            # This will help debug the issue
            self.parent.after(1000, self._test_simulator_colors)

    def toggle_audio_test(self):
        """Toggle audio reactive test"""
        if not self.audio_test_running:
            # Start test
            test_config = {
                "intensity": 200,
                "reactivity_mode": self.variables.get_value('test_mode'),
                "color_bias": self.variables.get_value('test_color'),
                "video_path": "",
                "notes": "Audio test"
            }

            self.current_song = test_config
            self.audio_test_running = True
            self.audio_test_button.config(text="Stop Audio Test")

            # Activate light show engine for audio test
            light_show_engine = self.get_controller('light_show_engine')
            if light_show_engine:
                light_show_engine.activate_engine()

            # Start test thread
            threading.Thread(target=self._run_audio_test, daemon=True).start()
            self.log_status("Audio test started")
        else:
            # Stop test
            self.audio_test_running = False
            self.audio_test_button.config(text="Start Audio Test")

            # Deactivate light show engine
            light_show_engine = self.get_controller('light_show_engine')
            if light_show_engine:
                light_show_engine.deactivate_engine()

            dmx_controller = self.get_controller('dmx_controller')
            if dmx_controller:
                dmx_controller.all_lights_off()

            self.log_status("Audio test stopped")

    def _run_audio_test(self):
        """Run audio test loop with intelligent effects"""
        while self.audio_test_running:
            try:
                audio_analyzer = self.get_controller('audio_analyzer')
                dmx_controller = self.get_controller('dmx_controller')
                color_engine = self.get_controller('color_engine')
                light_show_engine = self.get_controller('light_show_engine')

                if not all([audio_analyzer, dmx_controller, color_engine, light_show_engine]):
                    break

                # DEBUG: Check raw microphone level first
                raw_audio_level = audio_analyzer.get_audio_level()
                print(f"DEBUG: Raw microphone level: {raw_audio_level:.3f}")

                # Get comprehensive music analysis
                music_info = audio_analyzer.get_music_characteristics()

                # DEBUG: Check engine status
                if not light_show_engine.engine_active:
                    print(f"DEBUG: Engine is INACTIVE! Activating it...")
                    light_show_engine.activate_engine()

                # Use test settings
                color_engine.set_favorite_color(self.variables.get_value('test_color'))

                # DEBUG: Show music info before generating frame
                print(f"DEBUG: Music info - Energy: {music_info.get('current_level', 0):.3f}, Beat: {music_info.get('beat_detected', False)}")
                print(f"DEBUG: Engine active: {light_show_engine.engine_active}, Current effect: {light_show_engine.current_effect}")

                # Generate intelligent light frame
                lights_config = dmx_controller.get_lights_config()
                light_colors = light_show_engine.generate_light_frame(music_info, lights_config)

                # DEBUG: Show what colors were generated
                sample_light = list(light_colors.keys())[0] if light_colors else None
                if sample_light:
                    colors = light_colors[sample_light]
                    print(f"DEBUG: Generated colors for {sample_light}: R={colors['r']}, G={colors['g']}, B={colors['b']}")

                # DEBUG: Show more detailed music analysis
                print(f"DEBUG: Full music_info: {music_info}")

                # Update each light individually
                for light_id, colors in light_colors.items():
                    dmx_controller.set_light_rgb(light_id, colors['r'], colors['g'], colors['b'])

                # Show music info in console for debugging
                if music_info.get('tempo', 0) > 0:
                    print(f"Music: Tempo={music_info['tempo']}BPM, Energy={music_info['current_level']:.2f}, "
                          f"Trend={'Building' if music_info['is_building'] else 'Stable'}")

                time.sleep(0.05)  # 20 FPS update rate

            except Exception as e:
                print(f"Audio test error: {e}")
                self.log_error(f"Audio test error: {e}")
                break

        # Ensure we reset the button state when exiting
        if hasattr(self, 'audio_test_button'):
            self.audio_test_button.config(text="Start Audio Test")
        self.audio_test_running = False

    def _test_simulator_colors(self):
        """Test simulator with a brief color sequence to verify it's working"""
        dmx_simulator = self.get_controller('dmx_simulator')
        dmx_controller = self.get_controller('dmx_controller')

        if dmx_simulator and dmx_controller:
            print("DEBUG: Testing simulator DIRECTLY (bypassing DMX controller)...")
            lights_config = dmx_controller.get_lights_config()
            lights = lights_config.get('lights', {})

            # Test simulator directly
            for light_id in lights.keys():
                print(f"DEBUG: Direct simulator test - setting {light_id} to RED")
                dmx_simulator.update_light_color(light_id, 255, 0, 0, 255)

            self.parent.after(1000, lambda: self._test_green_direct())
            self.parent.after(2000, lambda: self._test_blue_direct())
            self.parent.after(3000, lambda: self._test_off_direct())

    def _test_green_direct(self):
        """Test green colors directly"""
        dmx_simulator = self.get_controller('dmx_simulator')
        dmx_controller = self.get_controller('dmx_controller')
        if dmx_simulator and dmx_controller:
            lights_config = dmx_controller.get_lights_config()
            lights = lights_config.get('lights', {})
            for light_id in lights.keys():
                print(f"DEBUG: Direct simulator test - setting {light_id} to GREEN")
                dmx_simulator.update_light_color(light_id, 0, 255, 0, 255)

    def _test_blue_direct(self):
        """Test blue colors directly"""
        dmx_simulator = self.get_controller('dmx_simulator')
        dmx_controller = self.get_controller('dmx_controller')
        if dmx_simulator and dmx_controller:
            lights_config = dmx_controller.get_lights_config()
            lights = lights_config.get('lights', {})
            for light_id in lights.keys():
                print(f"DEBUG: Direct simulator test - setting {light_id} to BLUE")
                dmx_simulator.update_light_color(light_id, 0, 0, 255, 255)

    def _test_off_direct(self):
        """Test turning lights off directly"""
        dmx_simulator = self.get_controller('dmx_simulator')
        if dmx_simulator:
            print("DEBUG: Direct simulator test - turning off all lights")
            dmx_simulator.turn_off_all_lights()

    def _flash_color(self, colors):
        """Flash a specific color"""
        dmx_controller = self.get_controller('dmx_controller')
        if dmx_controller:
            dmx_controller.update_lights(colors)

    def get_status_display(self):
        """Get the status display widget"""
        return self.status_display

    def stop_audio_test(self):
        """Stop audio test if running"""
        if self.audio_test_running:
            self.audio_test_running = False
            self.audio_test_button.config(text="Start Audio Test")

            # Deactivate light show engine
            light_show_engine = self.get_controller('light_show_engine')
            if light_show_engine:
                light_show_engine.deactivate_engine()

            dmx_controller = self.get_controller('dmx_controller')
            if dmx_controller:
                dmx_controller.all_lights_off()

            self.log_status("Audio test stopped")

    def test_simulator_direct(self):
        """Test simulator directly without DMX controller interference"""
        self._test_simulator_colors()

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
            
            self.log_status("DMX test completed - check dialog for details")
            
        except Exception as e:
            self.log_error(f"DMX test failed: {e}")

    def test_audio(self):
        """Test audio input"""
        try:
            audio_analyzer = self.get_controller('audio_analyzer')
            if audio_analyzer:
                level = audio_analyzer.get_audio_level()
                beat = audio_analyzer.detect_beat()
                from tkinter import messagebox
                messagebox.showinfo("Audio Test", 
                                   f"Audio Level: {level:.2f}\nBeat Detected: {beat}")
                
                self.log_status(f"Audio test completed - Level: {level:.2f}, Beat: {beat}")
            else:
                self.log_error("Audio analyzer not available")
                
        except Exception as e:
            self.log_error(f"Audio test failed: {e}")