"""
Epic Hyperspace Visualization - Star Wars/Star Trek Style
Featuring hyperspace tunnels, streaking stars, energy waves, and warp effects
"""

import math
import random
import time
import colorsys
from .base_visualization import BaseVisualization


class HyperspaceVisualization(BaseVisualization):
    """Epic hyperspace tunnel visualization with Star Wars/Star Trek effects"""
    
    def __init__(self):
        super().__init__()
        # Hyperspace tunnel system
        self.tunnel_rings = []
        self.streaking_stars = []
        self.energy_bolts = []
        self.warp_particles = []
        
        # Animation state
        self.tunnel_speed = 5.0
        self.warp_factor = 1.0
        self.hyperspace_acceleration = 0.0
        
    def initialize(self):
        """Initialize epic hyperspace system"""
        super().initialize()
        self.tunnel_rings = []
        self.streaking_stars = []
        self.energy_bolts = []
        self.warp_particles = []
        
        print("HYPERSPACE: Initializing epic hyperspace tunnel system")
        
        # Create tunnel ring system - multiple concentric rings for depth
        for ring_index in range(100):  # More rings for smoother tunnel
            ring = {
                'z': ring_index * 25,  # Distance into the tunnel
                'base_radius': 50 + (ring_index * 8),
                'segments': 32,  # More segments for smoother rings
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(0.5, 2.0),
                'color_phase': random.uniform(0, 1),
                'pulse_offset': random.uniform(0, math.pi * 2)
            }
            self.tunnel_rings.append(ring)
        
        # Create streaking star field
        for star_index in range(200):  # More stars for density
            star = {
                'x': random.uniform(-self.width, self.width * 2),
                'y': random.uniform(-self.height, self.height * 2),
                'z': random.uniform(100, 2000),
                'speed': random.uniform(5, 15),
                'brightness': random.uniform(0.3, 1.0),
                'color': random.choice(['white', 'blue', 'cyan', 'yellow'])
            }
            self.streaking_stars.append(star)
        
        # Create energy bolt system
        for bolt_index in range(15):
            bolt = {
                'active': False,
                'z': random.uniform(0, 1000),
                'angle': random.uniform(0, 360),
                'length': random.uniform(100, 300),
                'width': random.uniform(5, 15),
                'energy': 0.0,
                'pulse_time': 0.0
            }
            self.energy_bolts.append(bolt)
        
        # Create warp particle system
        for particle_index in range(50):
            particle = {
                'x': random.uniform(-200, self.width + 200),
                'y': random.uniform(-200, self.height + 200),
                'z': random.uniform(50, 800),
                'velocity': random.uniform(10, 30),
                'trail_length': random.uniform(50, 150),
                'color_hue': random.uniform(0, 1)
            }
            self.warp_particles.append(particle)
        
        print(f"HYPERSPACE: Initialized {len(self.tunnel_rings)} tunnel rings, {len(self.streaking_stars)} stars, {len(self.energy_bolts)} energy bolts")
    
    def render(self):
        """Render epic hyperspace visualization"""
        if not self.canvas:
            return
            
        try:
            center_x = self.width // 2
            center_y = self.height // 2
            current_time = time.time()
            
            # Update hyperspace parameters based on audio
            self._update_hyperspace_physics()
            
            # Draw deep space background with nebula effects
            self._draw_deep_space_background()
            
            # Draw the main hyperspace tunnel
            self._draw_hyperspace_tunnel(center_x, center_y)
            
            # Draw streaking star field
            self._draw_streaking_stars(center_x, center_y)
            
            # Draw energy bolts and lightning
            self._draw_energy_bolts(center_x, center_y)
            
            # Draw warp particles and trails
            self._draw_warp_particles(center_x, center_y)
            
            # Draw tunnel energy waves
            self._draw_tunnel_energy_waves(center_x, center_y)
            
            # Update all systems for next frame
            self._update_hyperspace_systems()
            
        except Exception as e:
            # Ignore canvas errors during shutdown
            pass
    
    def _update_hyperspace_physics(self):
        """Update hyperspace speed and effects based on audio"""
        # Base tunnel speed increases with audio level
        base_speed = 5.0 + (self.current_level * 20.0)
        
        # Beat detection creates hyperspace jumps
        if self.beat_detected:
            self.hyperspace_acceleration = 50.0  # Warp jump on beats
        else:
            self.hyperspace_acceleration *= 0.9  # Decay acceleration
        
        # Different frequencies affect different aspects
        bass = self.freq_bands.get('bass', 0.0)
        mid = self.freq_bands.get('mid', 0.0) 
        treble = self.freq_bands.get('treble', 0.0)
        
        # Bass affects tunnel speed and size
        self.tunnel_speed = base_speed + (bass * 30.0) + self.hyperspace_acceleration
        
        # Treble affects energy bolt frequency
        self.energy_bolt_frequency = treble * 0.3 + 0.05
        
        # Mid affects warp particle density
        self.warp_factor = 1.0 + (mid * 3.0)
        
        # Overall level affects tunnel pulsing
        self.tunnel_pulse_intensity = self.current_level * 2.0
    
    def _draw_deep_space_background(self):
        """Draw animated deep space background with nebula effects"""
        # Create cosmic background with multiple layers
        for layer in range(5):
            layer_alpha = 0.1 + (layer * 0.02)
            layer_size = 200 + (layer * 100)
            
            # Audio-reactive background pulsing
            pulse_size = int(layer_size + (self.current_level * 50))
            
            # Get space colors - blues, purples, deep reds
            space_colors = ['#000033', '#001155', '#110033', '#330011', '#001133']
            color = space_colors[layer % len(space_colors)]
            
            # Create nebula patches
            for patch in range(3 + layer):
                x = (self.frame_count * (0.1 + layer * 0.02) + patch * 200) % (self.width + 400) - 200
                y = (self.frame_count * (0.05 + layer * 0.01) + patch * 150) % (self.height + 300) - 150
                
                self.canvas.create_oval(
                    x - pulse_size, y - pulse_size,
                    x + pulse_size, y + pulse_size,
                    fill=color, outline="", stipple="gray25"
                )
    
    def _draw_hyperspace_tunnel(self, center_x: int, center_y: int):
        """Draw the main hyperspace tunnel with 3D perspective"""
        # Sort rings by depth for proper rendering
        sorted_rings = sorted(self.tunnel_rings, key=lambda r: r['z'], reverse=True)
        
        for ring in sorted_rings:
            if ring['z'] > 0:  # Only draw rings in front of us
                # Calculate 3D perspective
                perspective = 1000.0 / (ring['z'] + 100)  # Prevent division by zero
                screen_radius = ring['base_radius'] * perspective
                
                # Audio-reactive radius pulsing
                audio_pulse = math.sin(self.frame_count * 0.1 + ring['pulse_offset']) * self.tunnel_pulse_intensity * 20
                screen_radius += audio_pulse
                
                if screen_radius > 5:  # Only draw visible rings
                    # Calculate ring color based on depth and audio
                    depth_intensity = max(0.1, min(1.0, perspective))
                    
                    # Use song colors or default hyperspace blue/cyan
                    if self.song_primary_color != 'auto' and self.song_primary_color != 'none':
                        ring_color = self._get_pure_song_color(primary=True, intensity=depth_intensity)
                    else:
                        # Default hyperspace colors
                        hue = 0.5 + ring['color_phase'] * 0.3  # Cyan to blue range
                        r, g, b = colorsys.hsv_to_rgb(hue, 0.8, depth_intensity)
                        ring_color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
                    
                    # Draw ring segments for tunnel effect
                    segments = ring['segments']
                    for segment in range(segments):
                        angle1 = (segment / segments) * 2 * math.pi + math.radians(ring['rotation'])
                        angle2 = ((segment + 1) / segments) * 2 * math.pi + math.radians(ring['rotation'])
                        
                        # Calculate segment points
                        x1 = center_x + screen_radius * math.cos(angle1)
                        y1 = center_y + screen_radius * math.sin(angle1)
                        x2 = center_x + screen_radius * math.cos(angle2)
                        y2 = center_y + screen_radius * math.sin(angle2)
                        
                        # Draw tunnel segment
                        line_width = max(1, int(perspective * 3))
                        self.canvas.create_line(
                            x1, y1, x2, y2,
                            fill=ring_color, width=line_width,
                            capstyle='round'
                        )
    
    def _draw_streaking_stars(self, center_x: int, center_y: int):
        """Draw streaking stars flying past in hyperspace"""
        for star in self.streaking_stars:
            if star['z'] > 0:
                # Calculate 3D perspective for star position
                perspective = 800.0 / star['z']
                screen_x = center_x + (star['x'] - center_x) * perspective
                screen_y = center_y + (star['y'] - center_y) * perspective
                
                # Calculate star trail based on speed and audio
                trail_length = star['speed'] * self.tunnel_speed * 0.5
                
                # Audio-reactive trail enhancement
                if self.beat_detected:
                    trail_length *= 3.0
                
                # Calculate trail end point
                trail_end_x = screen_x + (trail_length * math.cos(math.atan2(screen_y - center_y, screen_x - center_x)))
                trail_end_y = screen_y + (trail_length * math.sin(math.atan2(screen_y - center_y, screen_x - center_x)))
                
                # Draw star trail
                if 0 <= screen_x <= self.width and 0 <= screen_y <= self.height:
                    # Star colors
                    star_colors = {
                        'white': '#FFFFFF',
                        'blue': '#AACCFF', 
                        'cyan': '#00FFFF',
                        'yellow': '#FFFF88'
                    }
                    color = star_colors.get(star['color'], '#FFFFFF')
                    
                    # Draw bright star trail
                    trail_width = max(1, int(perspective * 2))
                    self.canvas.create_line(
                        screen_x, screen_y,
                        trail_end_x, trail_end_y,
                        fill=color, width=trail_width,
                        capstyle='round'
                    )
                    
                    # Draw bright star core
                    star_size = max(2, int(perspective * 4))
                    self.canvas.create_oval(
                        screen_x - star_size, screen_y - star_size,
                        screen_x + star_size, screen_y + star_size,
                        fill=color, outline=""
                    )
    
    def _draw_energy_bolts(self, center_x: int, center_y: int):
        """Draw energy bolts and lightning effects through the tunnel"""
        for bolt in self.energy_bolts:
            if bolt['active']:
                # Calculate bolt position in 3D space
                perspective = 500.0 / (bolt['z'] + 50)
                
                # Draw electrical arc
                arc_segments = 8
                bolt_x = center_x + math.cos(math.radians(bolt['angle'])) * bolt['length'] * perspective
                bolt_y = center_y + math.sin(math.radians(bolt['angle'])) * bolt['length'] * perspective
                
                # Create jagged lightning effect
                points = [center_x, center_y]
                for segment in range(1, arc_segments):
                    progress = segment / arc_segments
                    base_x = center_x + (bolt_x - center_x) * progress
                    base_y = center_y + (bolt_y - center_y) * progress
                    
                    # Add electrical jitter
                    jitter = 20 * bolt['energy'] * perspective
                    jitter_x = base_x + random.uniform(-jitter, jitter)
                    jitter_y = base_y + random.uniform(-jitter, jitter)
                    points.extend([jitter_x, jitter_y])
                
                points.extend([bolt_x, bolt_y])
                
                # Draw the lightning bolt
                if len(points) >= 4:
                    bolt_color = '#FFFFFF' if bolt['energy'] > 0.7 else '#AACCFF'
                    bolt_width = max(2, int(bolt['energy'] * 8 * perspective))
                    
                    self.canvas.create_line(
                        points, fill=bolt_color, width=bolt_width,
                        smooth=False, capstyle='round'
                    )
    
    def _draw_warp_particles(self, center_x: int, center_y: int):
        """Draw warp particles and trails"""
        for particle in self.warp_particles:
            if particle['z'] > 0:
                perspective = 600.0 / particle['z']
                screen_x = center_x + (particle['x'] - center_x) * perspective
                screen_y = center_y + (particle['y'] - center_y) * perspective
                
                if 0 <= screen_x <= self.width and 0 <= screen_y <= self.height:
                    # Calculate particle color
                    r, g, b = colorsys.hsv_to_rgb(particle['color_hue'], 0.8, 1.0)
                    particle_color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
                    
                    # Draw particle trail
                    trail_length = particle['trail_length'] * perspective * self.warp_factor
                    direction = math.atan2(screen_y - center_y, screen_x - center_x)
                    
                    trail_end_x = screen_x - trail_length * math.cos(direction)
                    trail_end_y = screen_y - trail_length * math.sin(direction)
                    
                    # Draw trail
                    self.canvas.create_line(
                        screen_x, screen_y,
                        trail_end_x, trail_end_y,
                        fill=particle_color, width=max(1, int(perspective * 3)),
                        capstyle='round'
                    )
                    
                    # Draw particle core
                    particle_size = max(2, int(perspective * 5))
                    self.canvas.create_oval(
                        screen_x - particle_size, screen_y - particle_size,
                        screen_x + particle_size, screen_y + particle_size,
                        fill='#FFFFFF', outline=""
                    )
    
    def _draw_tunnel_energy_waves(self, center_x: int, center_y: int):
        """Draw energy waves flowing through the tunnel"""
        # Draw concentric energy waves
        wave_count = 5
        for wave_idx in range(wave_count):
            wave_time = (self.frame_count * 0.1) + (wave_idx * math.pi / 2)
            wave_radius = 100 + (wave_idx * 80) + (math.sin(wave_time) * 50)
            
            # Audio-reactive wave intensity
            wave_intensity = 0.3 + (self.current_level * 0.7)
            
            # Beat-reactive wave expansion
            if self.beat_detected:
                wave_radius += 100
            
            # Wave color cycling
            wave_hue = (wave_time * 0.1) % 1.0
            r, g, b = colorsys.hsv_to_rgb(wave_hue, 0.6, wave_intensity)
            wave_color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            
            # Draw energy wave ring
            self.canvas.create_oval(
                center_x - wave_radius, center_y - wave_radius,
                center_x + wave_radius, center_y + wave_radius,
                outline=wave_color, width=3, fill=""
            )
    
    def _update_hyperspace_systems(self):
        """Update all hyperspace systems for animation"""
        # Update tunnel rings
        for ring in self.tunnel_rings:
            ring['rotation'] += ring['rotation_speed']
            ring['z'] -= self.tunnel_speed
            
            # Reset ring when it gets too close
            if ring['z'] <= -100:
                ring['z'] += len(self.tunnel_rings) * 25
                ring['rotation'] = random.uniform(0, 360)
        
        # Update streaking stars
        for star in self.streaking_stars:
            star['z'] -= star['speed'] * self.tunnel_speed
            
            # Reset star when it gets too close
            if star['z'] <= 0:
                star['z'] = random.uniform(1500, 2000)
                star['x'] = random.uniform(-self.width, self.width * 2)
                star['y'] = random.uniform(-self.height, self.height * 2)
        
        # Update energy bolts
        for bolt in self.energy_bolts:
            if bolt['active']:
                bolt['pulse_time'] += 0.1
                bolt['energy'] = max(0, bolt['energy'] - 0.05)
                
                if bolt['energy'] <= 0:
                    bolt['active'] = False
            else:
                # Random chance to activate bolt, higher with audio
                if random.random() < (self.energy_bolt_frequency if hasattr(self, 'energy_bolt_frequency') else 0.1):
                    bolt['active'] = True
                    bolt['energy'] = 1.0
                    bolt['pulse_time'] = 0.0
                    bolt['angle'] = random.uniform(0, 360)
                    bolt['z'] = random.uniform(100, 800)
        
        # Update warp particles
        for particle in self.warp_particles:
            particle['z'] -= particle['velocity'] * self.warp_factor
            
            # Reset particle when it gets too close
            if particle['z'] <= 0:
                particle['z'] = random.uniform(600, 1000)
                particle['x'] = random.uniform(-200, self.width + 200)
                particle['y'] = random.uniform(-200, self.height + 200)
                particle['color_hue'] = random.uniform(0, 1)
    
    def _get_pure_song_color(self, primary: bool = True, intensity: float = 1.0) -> str:
        """Get pure primary or secondary song color without blending"""
        color_name = self.song_primary_color if primary else self.song_secondary_color
        
        if color_name == 'auto' or color_name == 'none' or not color_name:
            # Fallback to hyperspace blue
            return f"#{int(100*intensity):02x}{int(150*intensity):02x}{int(255*intensity):02x}"
        
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
        return "#66AAFF"
    
    def cleanup(self):
        """Clean up hyperspace resources"""
        self.tunnel_rings = []
        self.streaking_stars = []
        self.energy_bolts = []
        self.warp_particles = []