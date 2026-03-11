import tkinter as tk
from tkinter import ttk
import math
from typing import Dict, List, Tuple

class DMXSimulator:
    def __init__(self, parent_root=None):
        self.parent_root = parent_root
        self.window = None
        self.canvas = None
        self.light_circles = {}  # Store canvas circle objects
        self.light_labels = {}   # Store canvas label objects
        self.lights_config = {}
        self.is_visible = False
        
        # Visual settings
        self.circle_size = 40
        self.circle_spacing = 80
        self.lights_per_row = 4
        
        # Store current light states for display
        self.light_states = {}  # {light_id: {'r': int, 'g': int, 'b': int, 'dimmer': int}}
        
    def show_simulator(self, lights_config: Dict):
        """Show the DMX simulator window"""
        if self.window is None:
            self._create_window()
        
        self.lights_config = lights_config
        self._update_layout()
        
        if not self.is_visible:
            self.window.deiconify()
            self.is_visible = True
    
    def hide_simulator(self):
        """Hide the DMX simulator window"""
        if self.window and self.is_visible:
            self.window.withdraw()
            self.is_visible = False
    
    def toggle_simulator(self, lights_config: Dict = None):
        """Toggle the simulator window visibility"""
        if self.is_visible:
            self.hide_simulator()
        else:
            if lights_config:
                self.show_simulator(lights_config)
    
    def _create_window(self):
        """Create the simulator window"""
        self.window = tk.Toplevel(self.parent_root if self.parent_root else None)
        self.window.title("🎭 DMX Light Simulator")
        self.window.geometry("400x300")
        self.window.resizable(True, True)
        
        # Make it stay on top but not modal
        self.window.attributes('-topmost', True)
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.hide_simulator)
        
        # Create main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎭 DMX Light Simulator", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Canvas for lights
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg='#f0f0f0', highlightthickness=1, 
                               highlightbackground='gray')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Simulator Mode - No lights configured")
        self.status_label.pack(pady=(10, 0))
        
        # Initially hide the window
        self.window.withdraw()
    
    def _update_layout(self):
        """Update the layout of lights on the canvas"""
        if not self.canvas or not self.lights_config:
            return
        
        # Clear existing items
        self.canvas.delete("all")
        self.light_circles.clear()
        self.light_labels.clear()
        self.light_states.clear()
        
        # Get lights from config
        lights = self.lights_config.get('lights', {})
        if not lights:
            self.status_label.config(text="No lights configured")
            return
        
        # Calculate canvas size needed
        num_lights = len(lights)
        rows_needed = math.ceil(num_lights / self.lights_per_row)
        canvas_width = self.lights_per_row * self.circle_spacing + 40
        canvas_height = rows_needed * self.circle_spacing + 40
        
        # Update canvas size
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))
        
        # Create light circles
        for i, (light_id, light_config) in enumerate(lights.items()):
            row = i // self.lights_per_row
            col = i % self.lights_per_row
            
            x = col * self.circle_spacing + self.circle_spacing // 2 + 20
            y = row * self.circle_spacing + self.circle_spacing // 2 + 20
            
            # Create circle (initially off - dark gray with black outline)
            circle = self.canvas.create_oval(
                x - self.circle_size // 2, y - self.circle_size // 2,
                x + self.circle_size // 2, y + self.circle_size // 2,
                fill='#222222', outline='black', width=2
            )
            
            # Create brightness/color text overlay ON the circle
            brightness_text = self.canvas.create_text(
                x, y - 8,
                text="OFF", fill='white', font=('Arial', 8, 'bold'),
                tags=f"{light_id}_brightness"
            )
            
            # Create RGB values text overlay
            rgb_text = self.canvas.create_text(
                x, y + 8,
                text="0,0,0", fill='white', font=('Arial', 7),
                tags=f"{light_id}_rgb"
            )
            
            # Create label with light ID below the circle
            light_name = light_config.get('name', light_id)
            if len(light_name) > 12:
                light_name = light_name[:12] + "..."
            
            name_label = self.canvas.create_text(
                x, y + self.circle_size // 2 + 15,
                text=light_name, fill='black', font=('Arial', 8)
            )
            
            # Store references - now includes text overlays
            self.light_circles[light_id] = {
                'circle': circle,
                'brightness_text': brightness_text,
                'rgb_text': rgb_text,
                'name_label': name_label
            }
            
            # Initialize light state
            self.light_states[light_id] = {'r': 0, 'g': 0, 'b': 0, 'dimmer': 0}
        
        # Update status
        self.status_label.config(text=f"Simulating {num_lights} lights")
        
        # Resize window to fit content
        self.window.geometry(f"{min(canvas_width + 20, 800)}x{min(canvas_height + 100, 600)}")
    
    def update_light_color(self, light_id: str, r: int, g: int, b: int, dimmer: int = 255):
        """Update the color of a specific light"""
        if not self.is_visible:
            return
            
        if light_id not in self.light_circles:
            return
        
        # Store the light state
        self.light_states[light_id] = {'r': r, 'g': g, 'b': b, 'dimmer': dimmer}
        
        # Apply dimmer to RGB values
        dimmer_factor = dimmer / 255.0
        actual_r = int(r * dimmer_factor)
        actual_g = int(g * dimmer_factor)
        actual_b = int(b * dimmer_factor)
        
        # SIMULATOR ENHANCEMENT: Boost very dim colors for better visibility
        # When lights are "on" but very dim, scale them up to 30% minimum brightness
        # This only affects visual display - actual DMX values remain unchanged
        is_light_on = r > 0 or g > 0 or b > 0 or dimmer > 0
        
        if is_light_on:
            min_brightness = 76  # 30% of 255
            # Apply minimum brightness while preserving color ratios
            max_actual = max(actual_r, actual_g, actual_b)
            if max_actual > 0 and max_actual < min_brightness:
                # Scale up to minimum brightness while maintaining color balance
                scale_factor = min_brightness / max_actual
                display_r = min(255, int(actual_r * scale_factor))
                display_g = min(255, int(actual_g * scale_factor))
                display_b = min(255, int(actual_b * scale_factor))
            else:
                display_r = actual_r
                display_g = actual_g
                display_b = actual_b
        else:
            display_r = actual_r
            display_g = actual_g
            display_b = actual_b
        
        # Convert to hex color using display values
        hex_color = f"#{display_r:02x}{display_g:02x}{display_b:02x}"
        
        # Get light components
        light_components = self.light_circles[light_id]
        circle = light_components['circle']
        brightness_text = light_components['brightness_text']
        rgb_text = light_components['rgb_text']
        
        # Update circle color - enhance dark colors for visibility (legacy enhancement)
        if display_r + display_g + display_b < 30:  # Very dark
            # Show a subtle dark color instead of pure black
            display_color = f"#{max(display_r, 20):02x}{max(display_g, 20):02x}{max(display_b, 20):02x}"
        else:
            display_color = hex_color
            
        self.canvas.itemconfig(circle, fill=display_color)
        
        # Update outline color based on display brightness
        brightness = (display_r + display_g + display_b) / 3
        outline_color = 'black' if brightness > 128 else 'gray'
        self.canvas.itemconfig(circle, outline=outline_color)
        
        # Update brightness text
        brightness_percent = int((dimmer / 255.0) * 100)
        if brightness_percent == 0:
            brightness_label = "OFF"
            text_color = 'gray'
        else:
            brightness_label = f"{brightness_percent}%"
            text_color = 'white' if brightness < 128 else 'black'
        
        self.canvas.itemconfig(brightness_text, text=brightness_label, fill=text_color)
        
        # Update RGB text with actual DMX values (not display-enhanced values)
        rgb_label = f"{actual_r},{actual_g},{actual_b}"
        self.canvas.itemconfig(rgb_text, text=rgb_label, fill=text_color)
    
    def update_all_lights(self, colors: Dict[str, int]):
        """Update all lights with the same RGB values"""
        r = colors.get('r', 0)
        g = colors.get('g', 0)
        b = colors.get('b', 0)
        
        if not self.is_visible or not self.lights_config:
            return
        
        lights = self.lights_config.get('lights', {})
        
        for light_id, light_config in lights.items():
            # Apply intensity limiting if configured
            max_intensity = light_config.get('max_intensity', 0)
            if max_intensity > 0:
                scale_factor = max_intensity / 255.0
                final_r = int(r * scale_factor)
                final_g = int(g * scale_factor)
                final_b = int(b * scale_factor)
                dimmer = min(max_intensity, max(final_r, final_g, final_b))
            else:
                final_r, final_g, final_b = r, g, b
                dimmer = max(r, g, b)
            
            self.update_light_color(light_id, final_r, final_g, final_b, dimmer)
    
    def turn_off_all_lights(self):
        """Turn off all lights (set to black)"""
        if not self.is_visible:
            return
        
        for light_id in self.light_circles.keys():
            self.update_light_color(light_id, 0, 0, 0, 0)
    
    def destroy(self):
        """Clean up the simulator window"""
        if self.window:
            self.window.destroy()
            self.window = None
            self.is_visible = False