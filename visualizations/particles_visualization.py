"""
Particles visualization with dynamic particle system
"""

import math
import random
import colorsys
import time
from .base_visualization import BaseVisualization


class ParticlesVisualization(BaseVisualization):
    """Particle system visualization"""
    
    def __init__(self):
        super().__init__()
        self.particles = []
        self.max_particles = 100
        
    def initialize(self):
        """Initialize particle system"""
        super().initialize()
        self.particles = []
        
        # Create initial particles
        for _ in range(self.max_particles):
            particle = {
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(-2, 2),
                'size': random.uniform(2, 8),
                'life': random.uniform(0.5, 1.0),
                'color_phase': random.random(),
                'use_secondary': random.choice([True, False])  # Mix primary/secondary colors
            }
            self.particles.append(particle)
    
    def render(self):
        """Render particle system visualization"""
        
        # Update particles before rendering
        self._update_particles()
        
        # Draw particles with strong song color preference and variety
        for particle in self.particles:
            if particle['life'] > 0:
                size = particle['size'] * particle['life']
                
                # Create more varied colors based on particle properties
                particle_id = id(particle) % 3  # Get consistent ID for particle
                
                if particle.get('use_secondary', False) and self.song_secondary_color != 'none':
                    # Secondary color with some intensity variation
                    intensity = 0.7 + (particle['life'] * 0.3) + (particle_id * 0.1)
                    color = self._get_pure_song_color(primary=False, intensity=min(1.0, intensity))
                else:
                    # Primary color with position-based hue variation
                    base_intensity = 0.6 + (particle['life'] * 0.4)
                    # Add slight variation based on particle position for more interesting colors
                    position_variation = (particle['x'] % 100) / 500.0  # Small variation 0-0.2
                    intensity = min(1.0, base_intensity + position_variation)
                    color = self._get_pure_song_color(primary=True, intensity=intensity)
                
                # Fallback if song color fails - create hue based on position
                if color == "#FFFFFF" or not color:
                    hue = (particle['x'] + particle['y']) % 360 / 360.0
                    color = self._get_song_biased_color(hue, particle['life'])
                
                self.canvas.create_oval(
                    particle['x'] - size, particle['y'] - size,
                    particle['x'] + size, particle['y'] + size,
                    fill=color, outline=""
                )
    
    def _update_particles(self):
        """Update particle system"""
        for particle in self.particles:
            # Update position
            particle['x'] += particle['vx'] * (1 + self.current_level * 2)
            particle['y'] += particle['vy'] * (1 + self.current_level * 2)
            
            # Update life
            particle['life'] -= 0.01
            
            # Bounce off edges
            if particle['x'] <= 0 or particle['x'] >= self.width:
                particle['vx'] *= -1
            if particle['y'] <= 0 or particle['y'] >= self.height:
                particle['vy'] *= -1
            
            # Respawn dead particles
            if particle['life'] <= 0:
                particle['x'] = random.randint(0, self.width)
                particle['y'] = random.randint(0, self.height)
                particle['vx'] = random.uniform(-2, 2)
                particle['vy'] = random.uniform(-2, 2)
                particle['life'] = random.uniform(0.5, 1.0)
                particle['color_phase'] = random.random()
                particle['use_secondary'] = random.choice([True, False])
            
            # Burst effect on beats
            if self.effects['particle_burst'] > 0.5:
                particle['vx'] *= 1.5
                particle['vy'] *= 1.5
    
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
        """Get exciting dynamic color that cycles between primary and secondary song colors"""
        phase = phase % 1.0
        
        # Simple fallback rainbow when no song colors are set
        if (self.song_primary_color == 'auto' or not self.song_primary_color) and (self.song_secondary_color == 'none' or not self.song_secondary_color):
            rgb = colorsys.hsv_to_rgb(phase, 0.9, 0.9)
            return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
        
        # Use song-biased color with phase variation  
        return self._get_song_biased_color(phase, intensity, pure_song_color=True)
    
    def _get_song_biased_color(self, base_hue: float, intensity: float = 1.0, pure_song_color: bool = False) -> str:
        """Get color biased toward song's primary/secondary colors with enhanced prominence"""
        # Use rainbow color if no song colors configured
        if self.song_primary_color == 'auto' and self.song_secondary_color == 'none':
            rgb = colorsys.hsv_to_rgb(base_hue, 0.9, min(1.0, 0.8 + intensity * 0.2))
            return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
        
        # Map song color names to hue values with more accurate color mapping
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
            
            if pure_song_color:
                # Use pure song color for maximum impact
                blended_hue = song_hue
            else:
                # Enhanced blending - 85% song color, 15% base for stronger song color presence
                blended_hue = (song_hue * 0.85 + base_hue * 0.15) % 1.0
        else:
            blended_hue = base_hue
        
        # Handle white separately
        if song_color == 'white':
            return f"#{int(255 * intensity):02x}{int(255 * intensity):02x}{int(255 * intensity):02x}"
        
        # Create color with higher saturation for more vibrant colors
        rgb = colorsys.hsv_to_rgb(blended_hue, 0.9, min(1.0, 0.8 + intensity * 0.2))
        return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
    
    def cleanup(self):
        """Clean up particle resources"""
        self.particles = []