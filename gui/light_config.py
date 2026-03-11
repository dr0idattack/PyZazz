"""
Light Configuration Widget for DMX Light Show Controller
Handles DMX light setup and management
"""

import tkinter as tk
from tkinter import ttk, messagebox
from .base_ui import BaseUIComponent, LoggingMixin, FormHelper, TreeViewHelper, VariableManager


class LightConfigWidget(BaseUIComponent, LoggingMixin):
    """Widget for DMX light configuration management"""
    
    def __init__(self, parent, controllers=None):
        self.variables = VariableManager()
        self.editing_light_id = None
        # Initialize logging mixin
        self.info_display = None
        self.status_display = None
        super().__init__(parent, controllers)
        self._setup_variables()
    
    def setup_ui(self):
        """Setup light configuration UI"""
        self.frame = ttk.Frame(self.parent, padding="10")
        
        # Create form and list sections
        self._create_light_form()
        self._create_lights_list()
        
        # Configure grid weights
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)
    
    def _setup_variables(self):
        """Setup tkinter variables for light configuration"""
        self.variables.add_string_var('light_id')
        self.variables.add_string_var('light_name')
        self.variables.add_string_var('light_type', 'Par')  # Add light type variable
        self.variables.add_int_var('light_start_address', 1)
        self.variables.add_int_var('light_channel_count', 4)
        self.variables.add_int_var('light_dimmer_channel', 1)
        self.variables.add_int_var('light_red_channel', 2)
        self.variables.add_int_var('light_green_channel', 3)
        self.variables.add_int_var('light_blue_channel', 4)
        self.variables.add_int_var('light_max_intensity', 0)
        self.variables.add_bool_var('beat_pulse_enabled', True)  # Add beat pulse enabled
    
    def _create_light_form(self):
        """Create compact light configuration form"""
        form_frame = ttk.LabelFrame(self.frame, text="Light Configuration", padding="5")
        form_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Row 1: Basic info - ID, Name, Type
        ttk.Label(form_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=1, padx=(0,5))
        self.light_id_entry = ttk.Entry(form_frame, textvariable=self.variables.get_var('light_id'), width=8)
        self.light_id_entry.grid(row=0, column=1, pady=1, padx=(0,10))
        
        ttk.Label(form_frame, text="Name:").grid(row=0, column=2, sticky=tk.W, pady=1, padx=(0,5))
        self.light_name_entry = ttk.Entry(form_frame, textvariable=self.variables.get_var('light_name'), width=15)
        self.light_name_entry.grid(row=0, column=3, pady=1, padx=(0,10))
        
        ttk.Label(form_frame, text="Type:").grid(row=0, column=4, sticky=tk.W, pady=1, padx=(0,5))
        self.light_type_combo = ttk.Combobox(form_frame, textvariable=self.variables.get_var('light_type'), 
                                       values=['Par', 'Wash', 'Accent', 'Strobe'], width=8, state="readonly")
        self.light_type_combo.grid(row=0, column=5, pady=1, padx=(0,10))
        
        # Row 2: Address config - Start, Count, Max Intensity, Beat Pulse
        ttk.Label(form_frame, text="Start Addr:").grid(row=1, column=0, sticky=tk.W, pady=1, padx=(0,5))
        self.start_addr_spinbox = ttk.Spinbox(form_frame, from_=1, to=509, 
                                        textvariable=self.variables.get_var('light_start_address'),
                                        width=6, command=self.update_channel_addresses)
        self.start_addr_spinbox.grid(row=1, column=1, pady=1, padx=(0,10))
        self.start_addr_spinbox.bind('<KeyRelease>', lambda e: self.update_channel_addresses())
        
        ttk.Label(form_frame, text="Channels:").grid(row=1, column=2, sticky=tk.W, pady=1, padx=(0,5))
        self.channel_count_spinbox = ttk.Spinbox(form_frame, from_=1, to=8, 
                                           textvariable=self.variables.get_var('light_channel_count'),
                                           width=6, command=self.update_channel_addresses)
        self.channel_count_spinbox.grid(row=1, column=3, pady=1, padx=(0,10))
        self.channel_count_spinbox.bind('<KeyRelease>', lambda e: self.update_channel_addresses())
        
        ttk.Label(form_frame, text="Max Int:").grid(row=1, column=4, sticky=tk.W, pady=1, padx=(0,5))
        self.max_intensity_spinbox = ttk.Spinbox(form_frame, from_=0, to=255, textvariable=self.variables.get_var('light_max_intensity'),
                   width=6)
        self.max_intensity_spinbox.grid(row=1, column=5, pady=1, padx=(0,10))
        
        # Row 3: RGB Channels
        ttk.Label(form_frame, text="Dimmer:").grid(row=2, column=0, sticky=tk.W, pady=1, padx=(0,5))
        self.dimmer_spinbox = ttk.Spinbox(form_frame, from_=1, to=512, textvariable=self.variables.get_var('light_dimmer_channel'),
                   width=6)
        self.dimmer_spinbox.grid(row=2, column=1, pady=1, padx=(0,10))
        
        ttk.Label(form_frame, text="Red:").grid(row=2, column=2, sticky=tk.W, pady=1, padx=(0,5))
        self.red_spinbox = ttk.Spinbox(form_frame, from_=1, to=512, textvariable=self.variables.get_var('light_red_channel'),
                   width=6)
        self.red_spinbox.grid(row=2, column=3, pady=1, padx=(0,10))
        
        ttk.Label(form_frame, text="Green:").grid(row=2, column=4, sticky=tk.W, pady=1, padx=(0,5))
        self.green_spinbox = ttk.Spinbox(form_frame, from_=1, to=512, textvariable=self.variables.get_var('light_green_channel'),
                   width=6)
        self.green_spinbox.grid(row=2, column=5, pady=1, padx=(0,10))
        
        ttk.Label(form_frame, text="Blue:").grid(row=2, column=6, sticky=tk.W, pady=1, padx=(0,5))
        self.blue_spinbox = ttk.Spinbox(form_frame, from_=1, to=512, textvariable=self.variables.get_var('light_blue_channel'),
                   width=6)
        self.blue_spinbox.grid(row=2, column=7, pady=1, padx=(0,10))
        
        # Row 4: Beat pulse checkbox and buttons
        self.beat_pulse_checkbutton = ttk.Checkbutton(form_frame, text="Beat Pulse", variable=self.variables.get_var('beat_pulse_enabled'))
        self.beat_pulse_checkbutton.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=1)
        
        # Action buttons in same row
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=3, column=2, columnspan=6, sticky=tk.E, pady=1)
        
        self.add_light_button = ttk.Button(button_frame, text="Add Light", command=self.add_light)
        self.add_light_button.grid(row=0, column=0, padx=2)
        
        self.save_light_button = ttk.Button(button_frame, text="Save Changes", command=self.save_light_changes)
        self.save_light_button.grid(row=0, column=1, padx=2)
        self.save_light_button.grid_remove()  # Hidden initially
        
        self.cancel_edit_button = ttk.Button(button_frame, text="Cancel Edit", command=self.cancel_light_edit)
        self.cancel_edit_button.grid(row=0, column=2, padx=2)
        self.cancel_edit_button.grid_remove()  # Hidden initially
    
    
    def _create_lights_list(self):
        """Create lights list with management controls"""
        list_frame = ttk.LabelFrame(self.frame, text="Configured Lights", padding="10")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create treeview directly for better control
        light_columns = ('ID', 'Name', 'Type', 'Start Addr', 'Max Intensity', 'Beat Pulse', 'Dimmer Ch', 'Red Ch', 'Green Ch', 'Blue Ch')
        
        # Create treeview with explicit height - set high to ensure visibility
        self.lights_tree = ttk.Treeview(list_frame, columns=light_columns, show='headings', height=15)
        
        # Set optimized column widths and headings
        column_widths = {
            'ID': 60,
            'Name': 120,
            'Type': 60,
            'Start Addr': 80,
            'Max Intensity': 100,
            'Beat Pulse': 80,
            'Dimmer Ch': 80,
            'Red Ch': 60,
            'Green Ch': 70,
            'Blue Ch': 60
        }
        
        for col in light_columns:
            width = column_widths.get(col, 80)
            self.lights_tree.heading(col, text=col)
            self.lights_tree.column(col, width=width)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.lights_tree.yview)
        self.lights_tree.config(yscrollcommand=scrollbar.set)
        
        self.lights_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind double-click to edit light
        self.lights_tree.bind('<Double-1>', self.on_light_double_click)
        
        # Test buttons
        self._create_test_buttons(list_frame)
        
        # Management buttons
        self._create_management_buttons(list_frame)
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Initialize lights list
        self.refresh_lights_list()
    
    def _create_test_buttons(self, parent):
        """Create light test buttons"""
        test_frame = ttk.Frame(parent)
        test_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        test_colors = [
            ("Test Red", lambda: self.test_light_color('red')),
            ("Test Green", lambda: self.test_light_color('green')),
            ("Test Blue", lambda: self.test_light_color('blue')),
            ("Test White", lambda: self.test_light_color('white'))
        ]
        
        for i, (text, command) in enumerate(test_colors):
            ttk.Button(test_frame, text=text, command=command).grid(
                row=0, column=i, padx=(0, 5) if i < len(test_colors) - 1 else 0
            )
    
    def _create_management_buttons(self, parent):
        """Create light management buttons"""
        button_config = [
            ("Edit Selected", self.edit_selected_light),
            ("Delete Selected", self.delete_selected_light),
            ("Refresh", self.refresh_lights_list)
        ]
        
        FormHelper.create_button_frame(parent, 2, button_config)
    
    def update_channel_addresses(self):
        """Update individual channel addresses based on start address and channel count"""
        try:
            start_addr = self.variables.get_value('light_start_address')
            channel_count = self.variables.get_value('light_channel_count')
            
            # Auto-assign channels based on DRGB pattern (Dimmer first)
            if channel_count >= 1:
                self.variables.set_value('light_dimmer_channel', start_addr)
            if channel_count >= 2:
                self.variables.set_value('light_red_channel', start_addr + 1)
            if channel_count >= 3:
                self.variables.set_value('light_green_channel', start_addr + 2)
            if channel_count >= 4:
                self.variables.set_value('light_blue_channel', start_addr + 3)
                
        except tk.TclError:
            # Handle invalid input gracefully
            pass
    
    def add_light(self):
        """Add a new DMX light"""
        light_id = self.variables.get_value('light_id').strip()
        light_name = self.variables.get_value('light_name').strip()
        
        if not light_id or not light_name:
            messagebox.showerror("Error", "Please enter light ID and name")
            return
        
        dmx_controller = self.get_controller('dmx_controller')
        if not dmx_controller:
            messagebox.showerror("Error", "DMX controller not available")
            return
            
        lights_config = dmx_controller.get_lights_config()
        
        if "lights" not in lights_config:
            lights_config["lights"] = {}
            
        # Check if light ID already exists
        if light_id in lights_config["lights"]:
            messagebox.showerror("Error", f"Light ID '{light_id}' already exists")
            return
            
        lights_config["lights"][light_id] = {
            "name": light_name,
            "type": self.variables.get_value('light_type'),
            "address": self.variables.get_value('light_dimmer_channel'),
            "channels": {
                "dimmer": self.variables.get_value('light_dimmer_channel'),
                "red": self.variables.get_value('light_red_channel'),
                "green": self.variables.get_value('light_green_channel'),
                "blue": self.variables.get_value('light_blue_channel')
            },
            "max_intensity": self.variables.get_value('light_max_intensity'),
            "beat_pulse_enabled": self.variables.get_value('beat_pulse_enabled')
        }
        
        dmx_controller.lights_config = lights_config
        dmx_controller.save_lights_config()
        
        # Auto-increment start address for next light
        current_start = self.variables.get_value('light_start_address')
        channel_count = self.variables.get_value('light_channel_count')
        next_start = current_start + channel_count
        if next_start <= 509:  # Ensure we don't exceed DMX range
            self.variables.set_value('light_start_address', next_start)
        
        self.refresh_lights_list()
        self.clear_light_form()
        self.log_info(f"Added light: {light_name} ({light_id})")
    
    def clear_light_form(self):
        """Clear the light form and reset to add mode"""
        self.variables.set_value('light_id', "")
        self.variables.set_value('light_name', "")
        self.variables.set_value('light_type', 'Par')
        self.variables.set_value('beat_pulse_enabled', True)
        self.variables.set_value('light_max_intensity', 0)
        self.update_channel_addresses()
        self.editing_light_id = None
        
        # Show add button, hide save/cancel buttons
        self.add_light_button.grid()
        self.save_light_button.grid_remove()
        self.cancel_edit_button.grid_remove()
    
    def refresh_lights_list(self):
        """Refresh the lights list in the treeview"""
        dmx_controller = self.get_controller('dmx_controller')
        if not dmx_controller:
            return
        
        # Clear existing items
        for item in self.lights_tree.get_children():
            self.lights_tree.delete(item)
            
        # Add lights sorted by starting channel (dimmer channel)
        lights_config = dmx_controller.get_lights_config()
        lights_list = []
        
        for light_id, config in lights_config.get("lights", {}).items():
            channels = config.get('channels', {})
            max_intensity = config.get('max_intensity', 0)
            intensity_display = "Unlimited" if max_intensity == 0 else str(max_intensity)
            dimmer_channel = channels.get('dimmer', 999)  # Default to high number for sorting
            
            # Get light type and beat pulse status
            light_type = config.get('type', 'Par')
            beat_pulse = 'Yes' if config.get('beat_pulse_enabled', True) else 'No'
            
            lights_list.append({
                'dimmer_channel': dimmer_channel,
                'values': (
                    light_id,
                    config.get('name', ''),
                    light_type,
                    dimmer_channel if dimmer_channel != 999 else '',  # Start address
                    intensity_display,
                    beat_pulse,
                    channels.get('dimmer', ''),
                    channels.get('red', ''),
                    channels.get('green', ''),
                    channels.get('blue', '')
                )
            })
        
        # Sort by dimmer channel (starting address)
        lights_list.sort(key=lambda x: x['dimmer_channel'])
        
        # Insert sorted lights into tree
        for light in lights_list:
            self.lights_tree.insert('', 'end', values=light['values'])
        
        # Update the display after inserting all lights
        self.lights_tree.update_idletasks()
    
    def test_light_color(self, color):
        """Test a specific color on selected light or all lights"""
        selection = self.lights_tree.selection()
        dmx_controller = self.get_controller('dmx_controller')
        if not dmx_controller:
            return
        
        color_map = {
            'red': {'r': 255, 'g': 0, 'b': 0},
            'green': {'r': 0, 'g': 255, 'b': 0},
            'blue': {'r': 0, 'g': 0, 'b': 255},
            'white': {'r': 255, 'g': 255, 'b': 255}
        }
        
        colors = color_map.get(color, {'r': 0, 'g': 0, 'b': 0})
        
        if not selection:
            # Test all lights
            dmx_controller.update_lights(colors)
            self.log_status(f"Testing {color} on all lights")
        else:
            # Test selected light
            item = self.lights_tree.item(selection[0])
            light_id = item['values'][0]
            dmx_controller.set_light_rgb(light_id, colors['r'], colors['g'], colors['b'])
            self.log_status(f"Testing {color} on light {light_id}")
    
    def on_light_double_click(self, event):
        """Handle double-click on light in the list"""
        selection = self.lights_tree.selection()
        if selection:
            self.edit_selected_light()
    
    def edit_selected_light(self):
        """Edit the selected light"""
        selection = self.lights_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a light to edit")
            return
            
        item = self.lights_tree.item(selection[0])
        light_id = item['values'][0]
        
        dmx_controller = self.get_controller('dmx_controller')
        if not dmx_controller:
            return
        
        lights_config = dmx_controller.get_lights_config()
        light_config = lights_config.get("lights", {}).get(light_id)
        
        if not light_config:
            messagebox.showerror("Error", f"Light '{light_id}' not found")
            return
            
        # Populate form with light data (set variables for consistency)
        self.variables.set_value('light_id', light_id)
        
        light_name = light_config.get('name', '')
        self.variables.set_value('light_name', light_name)
        
        light_type = light_config.get('type', 'Par')
        self.variables.set_value('light_type', light_type)
        
        beat_pulse = light_config.get('beat_pulse_enabled', True)
        self.variables.set_value('beat_pulse_enabled', beat_pulse)
        
        channels = light_config.get('channels', {})
        self.variables.set_value('light_dimmer_channel', channels.get('dimmer', 1))
        self.variables.set_value('light_red_channel', channels.get('red', 2))
        self.variables.set_value('light_green_channel', channels.get('green', 3))
        self.variables.set_value('light_blue_channel', channels.get('blue', 4))
        self.variables.set_value('light_max_intensity', light_config.get('max_intensity', 0))
        
        # Try to calculate start address and channel count
        dimmer_ch = channels.get('dimmer', 1)
        self.variables.set_value('light_start_address', dimmer_ch)
        max_offset = max(
            channels.get('red', 2) - dimmer_ch, 
            channels.get('green', 3) - dimmer_ch, 
            channels.get('blue', 4) - dimmer_ch
        )
        self.variables.set_value('light_channel_count', max_offset + 1)
        
        # Set editing mode
        self.editing_light_id = light_id
        
        # Switch to edit mode buttons
        self.add_light_button.grid_remove()
        self.save_light_button.grid()
        self.cancel_edit_button.grid()
        
        # Force update ALL form widgets manually (VariableManager not updating UI properly)
        try:
            # Update Light ID, Name, Type
            self.light_id_entry.delete(0, tk.END)
            self.light_id_entry.insert(0, light_id)
            
            self.light_name_entry.delete(0, tk.END)
            self.light_name_entry.insert(0, light_name)
            
            self.light_type_combo.set(light_type)
            
            # Update Address Configuration
            start_addr = channels.get('dimmer', 1)
            max_offset = max(
                channels.get('red', 2) - start_addr, 
                channels.get('green', 3) - start_addr, 
                channels.get('blue', 4) - start_addr
            )
            channel_count = max_offset + 1
            max_intensity = light_config.get('max_intensity', 0)
            
            self.start_addr_spinbox.delete(0, tk.END)
            self.start_addr_spinbox.insert(0, str(start_addr))
            
            self.channel_count_spinbox.delete(0, tk.END)
            self.channel_count_spinbox.insert(0, str(channel_count))
            
            self.max_intensity_spinbox.delete(0, tk.END)
            self.max_intensity_spinbox.insert(0, str(max_intensity))
            
            # Update Channel Assignments
            self.dimmer_spinbox.delete(0, tk.END)
            self.dimmer_spinbox.insert(0, str(channels.get('dimmer', 1)))
            
            self.red_spinbox.delete(0, tk.END)
            self.red_spinbox.insert(0, str(channels.get('red', 2)))
            
            self.green_spinbox.delete(0, tk.END)
            self.green_spinbox.insert(0, str(channels.get('green', 3)))
            
            self.blue_spinbox.delete(0, tk.END)
            self.blue_spinbox.insert(0, str(channels.get('blue', 4)))
            
            # Update Beat Pulse Checkbox
            # The checkbutton should update automatically through its textvariable
            # but we can force it by setting the variable directly
            beat_pulse_var = self.variables.get_var('beat_pulse_enabled')
            beat_pulse_var.set(beat_pulse)
            
        except Exception as e:
            print(f"Error updating form fields: {e}")
            import traceback
            traceback.print_exc()
        
        self.log_info(f"Editing light: {light_config.get('name', '')} ({light_id})")
    
    def save_light_changes(self):
        """Save changes to the light being edited"""
        if not self.editing_light_id:
            return
            
        new_light_id = self.variables.get_value('light_id').strip()
        light_name = self.variables.get_value('light_name').strip()
        
        if not new_light_id or not light_name:
            messagebox.showerror("Error", "Please enter both light ID and name")
            return
        
        dmx_controller = self.get_controller('dmx_controller')
        if not dmx_controller:
            return
            
        lights_config = dmx_controller.get_lights_config()
        
        if "lights" not in lights_config:
            lights_config["lights"] = {}
            
        # If light ID changed, check if new ID already exists
        if new_light_id != self.editing_light_id and new_light_id in lights_config["lights"]:
            messagebox.showerror("Error", f"Light ID '{new_light_id}' already exists")
            return
            
        # Create the updated light configuration
        updated_config = {
            "name": light_name,
            "type": self.variables.get_value('light_type'),
            "address": self.variables.get_value('light_dimmer_channel'),
            "channels": {
                "dimmer": self.variables.get_value('light_dimmer_channel'),
                "red": self.variables.get_value('light_red_channel'),
                "green": self.variables.get_value('light_green_channel'),
                "blue": self.variables.get_value('light_blue_channel')
            },
            "max_intensity": self.variables.get_value('light_max_intensity'),
            "beat_pulse_enabled": self.variables.get_value('beat_pulse_enabled')
        }
        
        # If light ID changed, remove old entry
        if new_light_id != self.editing_light_id:
            if self.editing_light_id in lights_config["lights"]:
                del lights_config["lights"][self.editing_light_id]
        
        # Add/update with new ID
        lights_config["lights"][new_light_id] = updated_config
        
        dmx_controller.lights_config = lights_config
        dmx_controller.save_lights_config()
        
        self.refresh_lights_list()
        self.clear_light_form()
        self.log_info(f"Updated light: {light_name} ({new_light_id})")
    
    def cancel_light_edit(self):
        """Cancel light editing and return to add mode"""
        self.clear_light_form()
    
    def delete_selected_light(self):
        """Delete the selected light"""
        selection = self.lights_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a light to delete")
            return
            
        item = self.lights_tree.item(selection[0])
        light_id = item['values'][0]
        light_name = item['values'][1]
        
        if messagebox.askyesno("Confirm Delete", f"Delete light '{light_name}' ({light_id})?"):
            dmx_controller = self.get_controller('dmx_controller')
            if not dmx_controller:
                return
            
            lights_config = dmx_controller.get_lights_config()
            
            if light_id in lights_config.get("lights", {}):
                del lights_config["lights"][light_id]
                dmx_controller.lights_config = lights_config
                dmx_controller.save_lights_config()
                
                self.refresh_lights_list()
                self.log_info(f"Deleted light: {light_name} ({light_id})")
                
                # If we were editing this light, clear the form
                if self.editing_light_id == light_id:
                    self.clear_light_form()
            else:
                messagebox.showerror("Error", "Failed to delete light")