"""
Spiral visualization with rotating spiral patterns
"""

import math
import colorsys
from .base_visualization import BaseVisualization


class SpiralVisualization(BaseVisualization):
    """Rotating spiral patterns visualization"""
    
    def __init__(self):
        super().__init__()
        
    def initialize(self):
        """Initialize spiral visualization"""
        super().initialize()
    
    def render(self):
        """Render BIG dynamic spiral visualization with MORE ACTION"""
        if not self.canvas or not self._validate_canvas():
            return
            
        try:
            import time
            
            center_x, center_y = self.width // 2, self.height // 2
            current_time = time.time()
            
            # BIGGER, MORE DRAMATIC spirals
            spiral_count = 8  # More spirals
            for spiral_idx in range(spiral_count):
                points = []
                num_points = 300  # More points for smoother spirals
                
                # FASTER rotation with different speeds per spiral  
                base_rotation_speed = 50.0 + spiral_idx * 20.0  # Much faster base speeds
                audio_speed_multiplier = 1.0 + self.current_level * 4.0  # More audio reactivity
                rotation = (current_time * base_rotation_speed * audio_speed_multiplier) + (spiral_idx * 45)
                
                # MUCH BIGGER radius - use most of the screen
                base_radius = min(self.width, self.height) // 2  # Bigger base radius
                audio_radius_boost = self.current_level * base_radius * 1.0  # More audio boost
                max_radius = base_radius + audio_radius_boost
                
                # DRAMATIC beat expansion
                beat_expansion = self.beat_pulse * 150  # Much bigger beat response
            
                for i in range(num_points):
                    # MORE COMPLEX spiral patterns with more turns
                    turns = 8.0 + spiral_idx * 1.5  # More turns for complexity
                    angle = (i / num_points) * turns * math.pi + math.radians(rotation)
                    
                    # DRAMATIC radius progression
                    radius_progress = (i / num_points) ** 0.8  # Non-linear for interesting shape
                    radius = radius_progress * max_radius + beat_expansion
                    
                    # BIGGER bass-reactive wobble with multiple frequencies
                    bass = self.freq_bands.get('bass', 0.0)
                    mid = self.freq_bands.get('mid', 0.0)
                    treble = self.freq_bands.get('treble', 0.0)
                    
                    bass_wobble = bass * 60 * math.sin(angle * 2)  # Bigger wobble
                    mid_wobble = mid * 40 * math.sin(angle * 5)   # Mid-frequency detail
                    treble_wobble = treble * 20 * math.sin(angle * 8)  # High-frequency detail
                    
                    radius += bass_wobble + mid_wobble + treble_wobble
                    
                    # DRAMATIC spiral distortions
                    if self.current_level > 0.7:  # High energy distortion
                        distortion = math.sin(angle * 10 + current_time * 5) * 30 * self.current_level
                        radius += distortion
                    
                    x = center_x + radius * math.cos(angle)
                    y = center_y + radius * math.sin(angle)
                    points.extend([x, y])
            
                if len(points) >= 4:
                    # THICKER, more dramatic line width
                    line_width = 3 + int(self.current_level * 8)  # Bigger lines
                    
                    # Alternate between primary and secondary colors with INTENSITY
                    if spiral_idx % 2 == 0 or self.song_secondary_color == 'none':
                        color = self._get_pure_song_color(primary=True, intensity=1.0)  # Full intensity
                    else:
                        color = self._get_pure_song_color(primary=False, intensity=1.0)  # Full intensity
                    
                    # Draw the main spiral
                    self.canvas.create_line(points, fill=color, width=line_width, smooth=True)
                    
                    # ADD GLOW EFFECT for more drama
                    if self.current_level > 0.5:
                        glow_width = max(1, line_width // 3)
                        glow_color = self._get_pure_song_color(primary=(spiral_idx % 2 == 0), intensity=0.6)
                        self.canvas.create_line(points, fill=glow_color, width=glow_width, smooth=True)
                
            # MASSIVE central swirling particle system for MAXIMUM ACTION
            particle_count = int(40 + self.current_level * 80)  # Way more particles
            for i in range(particle_count):
                # FASTER particle rotation with layers
                layer = i % 4  # 4 layers of particles
                layer_speed = (layer + 1) * 80.0  # Different speeds per layer
                particle_angle = (current_time * layer_speed + i * (360 / particle_count)) % 360
                
                # DYNAMIC particle radius with audio reactivity
                base_particle_radius = 30 + layer * 40  # Spread across layers
                audio_particle_boost = self.current_level * 100  # Big audio boost
                beat_particle_boost = self.beat_pulse * 80  # Big beat response
                particle_radius = base_particle_radius + audio_particle_boost + beat_particle_boost
                
                # Add frequency-specific effects
                freq_effect = 0
                if layer == 0:  # Bass layer
                    freq_effect = self.freq_bands.get('bass', 0.0) * 50
                elif layer == 1:  # Mid layer  
                    freq_effect = self.freq_bands.get('mid', 0.0) * 40
                elif layer == 2:  # Treble layer
                    freq_effect = self.freq_bands.get('treble', 0.0) * 60
                else:  # Combined layer
                    freq_effect = (self.current_level * 70)
                
                particle_radius += freq_effect
                
                px = center_x + particle_radius * math.cos(math.radians(particle_angle))
                py = center_y + particle_radius * math.sin(math.radians(particle_angle))
                
                # BIGGER, more dramatic particles
                particle_size = 3 + int(self.current_level * 8) + layer
                particle_color = self._get_pure_song_color(primary=(layer % 2 == 0), intensity=1.0)
                
                self.canvas.create_oval(px - particle_size, py - particle_size,
                                      px + particle_size, py + particle_size,
                                      fill=particle_color, outline="")
                
        except Exception as e:
            if self.is_running:
                print(f"Spiral render error: {e}")
    
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
    
    def _get_dynamic_song_color(self, phase: float, intensity: float = 1.0) -> str:
        """Generate dynamic color based on audio"""
        import time
        base_hue = (time.time() * 0.1 + phase) % 1.0
        r, g, b = colorsys.hsv_to_rgb(base_hue, 0.8, intensity)
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
    
    def cleanup(self):
        """Clean up spiral resources"""
        pass