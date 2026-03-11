"""
Fixed Psychedelic Visualization - Clean implementation without color errors
"""

import math
import random
import time
import colorsys
from .base_visualization import BaseVisualization


class PsychedelicVisualization(BaseVisualization):
    """Clean psychedelic visualization with proper color handling"""
    
    def __init__(self):
        super().__init__()
        self.patterns = []
        self.time_offset = 0
        
    def initialize(self):
        """Initialize psychedelic systems"""
        super().initialize()
        self.patterns = []
        self.time_offset = random.uniform(0, 100)
        
        # Create flowing patterns
        for i in range(12):
            pattern = {
                'x': random.uniform(0, self.width),
                'y': random.uniform(0, self.height),
                'size': random.uniform(20, 80),
                'speed': random.uniform(0.5, 2.0),
                'hue_offset': random.uniform(0, 1.0),
                'type': random.choice(['circle', 'spiral', 'wave'])
            }
            self.patterns.append(pattern)
    
    def render(self):
        """Render clean psychedelic visualization"""
        if not self.canvas or not self._validate_canvas():
            return
            
        try:
            current_time = time.time() + self.time_offset
            
            # Draw flowing gradient background
            self._draw_gradient_background(current_time)
            
            # Draw psychedelic patterns
            self._draw_patterns(current_time)
            
            # Draw audio-reactive spirals
            self._draw_spirals(current_time)
            
        except Exception as e:
            if self.is_running:
                print(f"Psychedelic render error: {e}")
    
    def _safe_color(self, hue, saturation=0.8, brightness=0.9):
        """Convert HSV to safe hex color"""
        try:
            # Ensure values are in valid range
            h = max(0.0, min(1.0, hue % 1.0))
            s = max(0.0, min(1.0, saturation))
            v = max(0.0, min(1.0, brightness))
            
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            
            # Convert to safe RGB values
            r_val = max(0, min(255, int(r * 255)))
            g_val = max(0, min(255, int(g * 255)))
            b_val = max(0, min(255, int(b * 255)))
            
            return f"#{r_val:02x}{g_val:02x}{b_val:02x}"
        except:
            return "#ff00ff"  # Fallback to magenta
    
    def _draw_gradient_background(self, current_time):
        """Draw flowing gradient background"""
        bands = 20
        for i in range(bands):
            progress = i / bands
            y_start = int(self.height * progress)
            y_end = int(self.height * (progress + 1.0/bands))
            
            # Flowing hue based on time and audio
            base_hue = (current_time * 0.1 + progress * 0.5) % 1.0
            audio_shift = self.current_level * 0.3
            final_hue = (base_hue + audio_shift) % 1.0
            
            saturation = 0.6 + self.current_level * 0.3
            brightness = 0.2 + progress * 0.4 + self.current_level * 0.2
            
            color = self._safe_color(final_hue, saturation, brightness)
            
            self.canvas.create_rectangle(
                0, y_start, self.width, y_end,
                fill=color, outline=""
            )
    
    def _draw_patterns(self, current_time):
        """Draw flowing psychedelic patterns"""
        for pattern in self.patterns:
            # Update pattern position
            pattern['x'] += math.sin(current_time * pattern['speed']) * 2
            pattern['y'] += math.cos(current_time * pattern['speed'] * 0.7) * 1.5
            
            # Keep on screen
            pattern['x'] = pattern['x'] % self.width
            pattern['y'] = pattern['y'] % self.height
            
            # Audio-reactive size
            size = pattern['size'] * (1.0 + self.current_level * 0.8)
            
            # Color with audio reactivity
            hue = (pattern['hue_offset'] + current_time * 0.2 + self.current_level * 0.5) % 1.0
            saturation = 0.8 + self.current_level * 0.2
            brightness = 0.7 + self.current_level * 0.3
            
            color = self._safe_color(hue, saturation, brightness)
            
            # Draw pattern based on type
            if pattern['type'] == 'circle':
                self.canvas.create_oval(
                    pattern['x'] - size/2, pattern['y'] - size/2,
                    pattern['x'] + size/2, pattern['y'] + size/2,
                    outline=color, width=max(2, int(self.current_level * 6)), fill=""
                )
            elif pattern['type'] == 'spiral':
                self._draw_mini_spiral(pattern['x'], pattern['y'], size, color)
            else:  # wave
                self._draw_wave_pattern(pattern['x'], pattern['y'], size, color, current_time)
    
    def _draw_spirals(self, current_time):
        """Draw main audio-reactive spirals"""
        center_x, center_y = self.width // 2, self.height // 2
        
        # Main spiral count based on audio
        spiral_count = 3 + int(self.current_level * 4)
        
        for i in range(spiral_count):
            points = []
            segments = 50
            
            # Spiral properties
            rotation = current_time * (30 + i * 20) + i * 60
            max_radius = min(self.width, self.height) // 3
            audio_radius = max_radius * (0.5 + self.current_level * 1.5)
            
            for seg in range(segments):
                progress = seg / segments
                angle = math.radians(rotation + progress * 720)  # 2 full turns
                radius = progress * audio_radius
                
                # Audio-reactive wobble
                bass_wobble = self.freq_bands.get('bass', 0) * 30 * math.sin(angle * 3)
                radius += bass_wobble
                
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                points.extend([x, y])
            
            if len(points) >= 4:
                # Spiral color
                hue = (i * 0.2 + current_time * 0.15) % 1.0
                color = self._safe_color(hue, 0.9, 0.8 + self.current_level * 0.2)
                
                width = max(2, int(3 + self.current_level * 5))
                self.canvas.create_line(
                    points, fill=color, width=width, smooth=True
                )
    
    def _draw_mini_spiral(self, x, y, size, color):
        """Draw a small spiral pattern"""
        points = []
        segments = 12
        
        for i in range(segments):
            progress = i / segments
            angle = progress * math.pi * 4
            radius = progress * size * 0.4
            
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            points.extend([px, py])
        
        if len(points) >= 4:
            self.canvas.create_line(points, fill=color, width=2, smooth=True)
    
    def _draw_wave_pattern(self, x, y, size, color, current_time):
        """Draw a wave pattern"""
        points = []
        segments = 16
        
        for i in range(segments):
            progress = i / segments
            wave_x = x + (progress - 0.5) * size
            wave_y = y + math.sin(progress * math.pi * 2 + current_time * 3) * size * 0.3
            points.extend([wave_x, wave_y])
        
        if len(points) >= 4:
            self.canvas.create_line(points, fill=color, width=3, smooth=True)
    
    def cleanup(self):
        """Clean up resources"""
        self.patterns = []