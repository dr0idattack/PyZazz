"""
Wild visualization with high-energy 1960s-inspired effects
"""

import math
import random
import colorsys
from .base_visualization import BaseVisualization


class WildVisualization(BaseVisualization):
    """High-energy Born to Be Wild inspired visualization"""
    
    def __init__(self):
        super().__init__()
        # Wild-specific state
        self.wild_freedom_rays = []
        self.wild_lightning_bolts = []
        self.wild_explosion_particles = []
        
    def initialize(self):
        """Initialize Wild visualization (1960s inspired with Born to Be Wild spirit)"""
        super().initialize()
        # Initialize freedom rays
        self.wild_freedom_rays = []
        for i in range(12):
            self.wild_freedom_rays.append({
                'angle': (i * 30) + random.uniform(-15, 15),  # Roughly evenly spaced
                'length': random.randint(300, 600),
                'phase': random.uniform(0, math.pi * 2),
                'speed': random.uniform(0.02, 0.05)
            })
        
        # Initialize lightning bolts
        self.wild_lightning_bolts = []
        for i in range(6):
            self.wild_lightning_bolts.append({
                'x1': random.randint(0, self.width),
                'y1': random.randint(0, self.height // 3),
                'active': False,
                'duration': 0,
                'jagged_points': []
            })
        
        # Initialize explosion particles
        self.wild_explosion_particles = []
        for i in range(50):
            self.wild_explosion_particles.append({
                'x': self.width // 2,
                'y': self.height // 2,
                'velocity_x': random.uniform(-8, 8),
                'velocity_y': random.uniform(-8, 8),
                'life': 0,
                'max_life': random.randint(30, 90),
                'active': False
            })
    
    def render(self):
        """Render Wild visualization - HIGH ENERGY ROCK REBELLION!"""
        center_x = self.width // 2
        center_y = self.height // 2
        
        # INTENSE WILD COLORS - use song colors for consistency
        wild_palette = {
            'electric_blue': self._get_pure_song_color(primary=True, intensity=1.0),
            'neon_yellow': self._get_song_biased_color(0.16, 1.0),  # Yellow hue with song color bias
            'hot_pink': self._get_pure_song_color(primary=False, intensity=1.0) if self.song_secondary_color != 'none' else self._get_song_biased_color(0.91, 1.0),
            'lime_green': self._get_song_biased_color(0.33, 1.0),  # Green hue with song color bias
            'blazing_orange': self._get_song_biased_color(0.08, 1.0),  # Orange hue with song color bias
            'pure_white': self._get_song_biased_color(0.0, 1.0) if self.song_primary_color != 'white' else '#FFFFFF',
            'blood_red': self._get_song_biased_color(0.0, 1.0),  # Red hue with song color bias
            'purple_haze': self._get_song_biased_color(0.83, 1.0)  # Purple hue with song color bias
        }
        
        # DYNAMIC BACKGROUND - pulsing, shifting energy field
        self._draw_wild_energy_field(wild_palette)
        
        # MASSIVE EXPLOSIVE BURSTS - screen-filling energy blasts
        self._draw_wild_mega_explosions(center_x, center_y, wild_palette)
        
        # ELECTRIC STORM - constant lightning and energy arcs
        self._draw_wild_electric_storm(wild_palette)
        
        # BLAZING COMETS - fast-moving fire trails across screen
        self._draw_wild_blazing_comets(wild_palette)
        
        # PSYCHEDELIC VORTEX - spinning dimensional portal
        self._draw_wild_vortex(center_x, center_y, wild_palette)
        
        # RHYTHM PULSE RINGS - massive expanding circles on beats
        self._draw_wild_pulse_rings(center_x, center_y, wild_palette)
        
    
    def _draw_wild_energy_field(self, palette):
        """Draw dynamic pulsing energy field background"""
        bass_energy = self.freq_bands.get('bass', 0.0)
        total_energy = sum(self.freq_bands.values())
        
        # Create animated energy grid
        grid_size = 60
        for x in range(0, self.width, grid_size):
            for y in range(0, self.height, grid_size):
                # Animated wave pattern
                wave = math.sin((x + y) * 0.01 + self.frame_count * 0.2) * math.cos(self.frame_count * 0.15)
                energy_boost = total_energy * 2
                
                if abs(wave) > (0.3 - energy_boost):
                    # Bright energy cell
                    intensity = int(50 + abs(wave) * 100 + energy_boost * 100)
                    color_index = int((self.frame_count * 0.1 + x + y) * 0.01) % 4
                    colors = [palette['electric_blue'], palette['neon_yellow'], palette['hot_pink'], palette['lime_green']]
                    
                    cell_size = int(20 + bass_energy * 40)
                    self.canvas.create_rectangle(
                        x - cell_size//2, y - cell_size//2,
                        x + cell_size//2, y + cell_size//2,
                        fill=colors[color_index], outline='', stipple='gray50'
                    )
    
    def _draw_wild_mega_explosions(self, center_x, center_y, palette):
        """Draw massive screen-filling explosive bursts"""
        total_energy = sum(self.freq_bands.values())
        
        # Trigger mega explosion on strong beats - reduced frequency
        if self.beat_detected and total_energy > 1.5 and random.random() < 0.6:
            # Fewer explosion rings to reduce strobing
            for ring in range(3):
                radius = (self.frame_count % 30) * 40 + ring * 80
                if radius < 800:  # Keep on screen
                    ring_width = int(15 - ring * 2)
                    if ring_width > 0:
                        color_cycle = (ring + self.frame_count * 0.2) % 4
                        colors = [palette['blazing_orange'], palette['neon_yellow'], palette['blood_red'], palette['pure_white']]
                        
                        self.canvas.create_oval(
                            center_x - radius, center_y - radius,
                            center_x + radius, center_y + radius,
                            outline=colors[int(color_cycle)], width=ring_width
                        )
    
    def _draw_wild_electric_storm(self, palette):
        """Draw chaotic electric arcs and lightning"""
        treble_energy = self.freq_bands.get('treble', 0.0)
        
        # Draw lightning bolts randomly
        if random.random() < (0.1 + treble_energy * 0.3):  # Higher chance with treble
            bolt_count = random.randint(1, 3)
            for _ in range(bolt_count):
                start_x = random.randint(0, self.width)
                start_y = random.randint(0, self.height // 2)
                end_x = start_x + random.randint(-200, 200)
                end_y = start_y + random.randint(100, 300)
                
                # Create jagged lightning path
                points = [start_x, start_y]
                segments = 8
                for i in range(1, segments):
                    progress = i / segments
                    x = start_x + (end_x - start_x) * progress + random.randint(-50, 50)
                    y = start_y + (end_y - start_y) * progress
                    points.extend([x, y])
                points.extend([end_x, end_y])
                
                if len(points) >= 4:
                    colors = [palette['pure_white'], palette['electric_blue'], palette['neon_yellow']]
                    color = colors[random.randint(0, 2)]
                    self.canvas.create_line(points, fill=color, width=random.randint(3, 8), capstyle='round')
    
    def _draw_wild_blazing_comets(self, palette):
        """Draw fast-moving fire trails across screen"""
        mid_energy = self.freq_bands.get('mid', 0.0)
        
        # Draw comets with fire trails
        comet_count = int(3 + mid_energy * 5)
        for _ in range(comet_count):
            if random.random() < 0.3:  # 30% chance each frame
                # Comet position and motion
                start_x = random.choice([0, self.width])  # Start from sides
                start_y = random.randint(0, self.height)
                end_x = self.width - start_x  # Go to opposite side
                end_y = start_y + random.randint(-200, 200)
                
                # Create fire trail
                trail_segments = 10
                for i in range(trail_segments):
                    progress = i / trail_segments
                    x = start_x + (end_x - start_x) * progress
                    y = start_y + (end_y - start_y) * progress
                    
                    # Trail gets smaller towards the end
                    size = int(15 * (1 - progress * 0.7))
                    if size > 2:
                        colors = [palette['blazing_orange'], palette['blood_red'], palette['neon_yellow']]
                        color = colors[i % 3]
                        self.canvas.create_oval(x - size, y - size, x + size, y + size, fill=color, outline='')
    
    def _draw_wild_vortex(self, center_x, center_y, palette):
        """Draw spinning dimensional portal"""
        # Create spiral vortex
        spiral_count = 4
        for spiral_idx in range(spiral_count):
            points = []
            num_points = 50
            
            rotation = self.frame_count * 3 + (spiral_idx * 90)  # Fast rotation
            max_radius = min(self.width, self.height) // 4
            
            for i in range(num_points):
                angle = (i / num_points) * 6 * math.pi + math.radians(rotation)
                radius = (i / num_points) * max_radius * (1 + self.current_level)
                
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                points.extend([x, y])
            
            if len(points) >= 4:
                colors = [palette['purple_haze'], palette['hot_pink'], palette['electric_blue'], palette['lime_green']]
                color = colors[spiral_idx]
                self.canvas.create_line(points, fill=color, width=3, smooth=True)
    
    def _draw_wild_pulse_rings(self, center_x, center_y, palette):
        """Draw massive expanding circles on beats"""
        if self.beat_detected:
            ring_count = 5
            for ring in range(ring_count):
                radius = (self.frame_count % 60) * 10 + ring * 60
                if radius < 600:  # Keep on screen
                    ring_width = int(8 - ring)
                    if ring_width > 0:
                        colors = [palette['pure_white'], palette['electric_blue'], palette['hot_pink'], palette['neon_yellow'], palette['lime_green']]
                        color = colors[ring]
                        
                        self.canvas.create_oval(
                            center_x - radius, center_y - radius,
                            center_x + radius, center_y + radius,
                            outline=color, width=ring_width, fill=''
                        )
    
    def _get_pure_song_color(self, primary: bool = True, intensity: float = 1.0) -> str:
        """Get pure primary or secondary song color without blending"""
        color_name = self.song_primary_color if primary else self.song_secondary_color
        
        if color_name == 'auto' or color_name == 'none' or not color_name:
            # Fallback to dynamic colors instead of white
            return self._get_dynamic_song_color(0.5, intensity)
        
        color_hues = {
            'red': 0.0, 'orange': 0.08, 'yellow': 0.16, 'green': 0.33,
            'blue': 0.66, 'purple': 0.83, 'pink': 0.91, 'white': 0.0
        }
        
        if color_name in color_hues:
            hue = color_hues[color_name]
            if color_name == 'white':
                return f"#{int(255 * intensity):02x}{int(255 * intensity):02x}{int(255 * intensity):02x}"
            
            r, g, b = colorsys.hsv_to_rgb(hue, 0.8, intensity)
            return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
        
        # Fallback if unknown color
        return "#ffffff"
    
    def _get_song_biased_color(self, base_hue: float, intensity: float = 1.0) -> str:
        """Get color biased toward song's primary/secondary colors"""
        # Use rainbow color if no song colors configured
        if self.song_primary_color == 'auto' and self.song_secondary_color == 'none':
            r, g, b = colorsys.hsv_to_rgb(base_hue, 0.9, min(1.0, 0.8 + intensity * 0.2))
            return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        
        # Map song color names to hue values
        color_hues = {
            'red': 0.0, 'orange': 0.08, 'yellow': 0.16, 'green': 0.33,
            'blue': 0.66, 'purple': 0.83, 'pink': 0.91, 'white': 0.0
        }
        
        # Choose primary or secondary based on bias
        if self.color_bias_primary or self.song_secondary_color == 'none':
            song_color = self.song_primary_color
        else:
            song_color = self.song_secondary_color
        
        # Get base hue for song color
        if song_color in color_hues:
            song_hue = color_hues[song_color]
            # Enhanced blending - 85% song color, 15% base for stronger song color presence
            blended_hue = (song_hue * 0.85 + base_hue * 0.15) % 1.0
        else:
            blended_hue = base_hue
        
        # Handle white separately
        if song_color == 'white':
            return f"#{int(255 * intensity):02x}{int(255 * intensity):02x}{int(255 * intensity):02x}"
        
        # Create color with higher saturation for more vibrant colors
        r, g, b = colorsys.hsv_to_rgb(blended_hue, 0.9, min(1.0, 0.8 + intensity * 0.2))
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    
    def _get_dynamic_song_color(self, phase: float, intensity: float = 1.0) -> str:
        """Generate dynamic color based on audio"""
        import time
        base_hue = (time.time() * 0.1 + phase) % 1.0
        r, g, b = colorsys.hsv_to_rgb(base_hue, 0.8, intensity)
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
    
    def cleanup(self):
        """Clean up wild resources"""
        self.wild_freedom_rays = []
        self.wild_lightning_bolts = []
        self.wild_explosion_particles = []