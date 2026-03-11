"""
Enhanced Bubbles visualization with realistic physics and audio reactivity
"""

import math
import random
import time
import colorsys
from typing import List, Dict, Any
from .base_visualization import BaseVisualization


class BubblesVisualization(BaseVisualization):
    """Beautiful underwater bubble scene with realistic physics"""
    
    def __init__(self):
        super().__init__()
        self.bubbles = []
        self.start_time = None
        self.bubble_spawn_timer = 0
        # Performance optimization caches
        self.background_cache_time = 0
        self.background_cache_interval = 0.1  # Redraw background every 100ms instead of every frame
        self.wind_cache = {'time': 0, 'values': {}}
        self.frame_skip_counter = 0
        # Frame rate monitoring
        self.frame_times = []
        self.last_fps_report = 0
        
    def initialize(self):
        """Initialize bubble system"""
        super().initialize()
        self.bubbles = []
        self.start_time = time.time()
        self.bubble_spawn_timer = 0
        
        # Create initial bubbles across the screen
        for _ in range(50):
            bubble = self._create_bubble()
            # Spread initial bubbles across the screen
            bubble['y'] = random.uniform(0, self.height)
            bubble['age'] = random.uniform(0, 8)  # Varied ages
            self.bubbles.append(bubble)
    
    def _get_bubble_color_type(self):
        """Determine bubble color type based on song's random color percentage"""
        # Get the random color percentage from song config (0-100%)
        random_percent = getattr(self, 'random_color_percentage', 25)  # Default 25%
        
        # Roll for color type
        roll = random.uniform(0, 100)
        
        if roll < random_percent:
            # Use random palette color
            return 'random'
        else:
            # Use song colors (primary/secondary)
            # If secondary is available, choose between primary and secondary
            if self.song_secondary_color and self.song_secondary_color != 'none':
                # 60% primary, 40% secondary when both are available
                return 'primary' if random.random() < 0.6 else 'secondary'
            else:
                # Only primary available
                return 'primary'
    
    def _create_bubble(self):
        """Create a new bubble with realistic properties"""
        bubble_size = random.choices(
            ['small', 'medium', 'large'], 
            weights=[50, 35, 15], 
            k=1
        )[0]
        
        if bubble_size == 'small':
            radius = random.uniform(5, 15)
            speed_mult = 1.5
        elif bubble_size == 'medium':
            radius = random.uniform(15, 30)
            speed_mult = 1.0
        else:  # large
            radius = random.uniform(30, 50)
            speed_mult = 0.7
        
        # Determine color type using song config's random percentage
        color_type = self._get_bubble_color_type()
        
        return {
            'x': random.uniform(radius, self.width - radius),
            'y': self.height + random.uniform(0, 100),
            'radius': radius,
            'base_radius': radius,
            'vx': random.uniform(-0.3, 0.3) * speed_mult,  # Gentler initial horizontal drift
            'vy': random.uniform(-25, -15) * speed_mult,   # MUCH slower upward float
            'birth_time': time.time(),
            'age': 0,
            'wobble_phase': random.uniform(0, 2 * math.pi),
            'wobble_speed': random.uniform(0.5, 1.5),  # MUCH slower wobble to reduce flashing
            'shimmer_phase': random.uniform(0, 2 * math.pi),
            'shimmer_speed': random.uniform(1, 2.5),  # MUCH slower shimmer to reduce flashing
            'color_type': color_type,  # 'primary', 'secondary', or 'random'
            'glow_intensity': random.uniform(0.5, 1.0),
            'size': bubble_size,
            # Wind and turbulence properties for smooth movement
            'wind_resistance': random.uniform(0.5, 1.0),  # How much wind affects this bubble
            'turbulence_phase': random.uniform(0, 2 * math.pi),
            'drift_phase': random.uniform(0, 2 * math.pi),
            'spiral_phase': random.uniform(0, 2 * math.pi),
            'chaos_factor': random.uniform(0.3, 1.0),  # How wild this bubble moves
        }
    
    def _render_frame(self):
        """Override base render frame to eliminate flicker"""
        if not self.canvas or not self.is_running:
            return
        
        try:
            # Check if canvas still exists
            if not self.canvas.winfo_exists():
                return
            
            # ANTI-FLICKER: Clear canvas every few frames only, not every frame
            if not hasattr(self, '_clear_counter'):
                self._clear_counter = 0
            
            self._clear_counter += 1
            if self._clear_counter >= 3:  # Clear every 3rd frame instead of every frame
                self.canvas.delete("all")
                self._clear_counter = 0
            
            # Render normally
            self.render()
            
        except Exception as e:
            if self.is_running:
                print(f"Bubbles render frame error: {e}")

    def render(self):
        """Render beautiful bubble visualization with smooth animation"""
        if not self.canvas or not self._validate_canvas():
            return
            
        try:
            current_time = time.time()
            
            # Calculate smooth delta time for consistent animation
            if not hasattr(self, 'last_render_time'):
                self.last_render_time = current_time
            
            dt = min(0.033, current_time - self.last_render_time)  # Cap at 33ms for stability
            self.last_render_time = current_time
            
            # Update bubbles with smooth timing
            self._update_bubbles(current_time, dt)
            
            # Spawn new bubbles
            self._spawn_new_bubbles(current_time)
            
            # Draw everything
            self._draw_underwater_background()
            self._draw_all_bubbles(current_time)
            self._draw_surface_effects(current_time)
            
            # Performance monitoring
            self._monitor_performance(current_time)
            
        except Exception as e:
            if self.is_running:
                print(f"Bubbles render error: {e}")
    
    def _monitor_performance(self, current_time):
        """Monitor frame rate and detect threading issues"""
        self.frame_times.append(current_time)
        
        # Keep only last 60 frames
        if len(self.frame_times) > 60:
            self.frame_times.pop(0)
        
        # Report performance every 5 seconds
        if current_time - self.last_fps_report > 5.0:
            if len(self.frame_times) > 10:
                frame_deltas = [self.frame_times[i] - self.frame_times[i-1] 
                               for i in range(1, len(self.frame_times))]
                avg_fps = 1.0 / (sum(frame_deltas) / len(frame_deltas))
                max_frame_time = max(frame_deltas) * 1000  # Convert to ms
                
                # Warn about performance issues
                if avg_fps < 45:
                    print(f"BUBBLES PERFORMANCE: Low FPS {avg_fps:.1f}, max frame time: {max_frame_time:.1f}ms, bubbles: {len(self.bubbles)}")
                elif max_frame_time > 50:  # Frame time spike > 50ms
                    print(f"BUBBLES PERFORMANCE: Frame spike detected: {max_frame_time:.1f}ms, avg FPS: {avg_fps:.1f}")
                    
            self.last_fps_report = current_time
    
    def _update_bubbles(self, current_time, dt):
        """Update bubble physics with wild wind-driven movement"""
        # Calculate music-driven wind forces - with safe defaults
        bass_wind = self.freq_bands.get('bass', 0.0) if hasattr(self, 'freq_bands') else 0.0
        mid_wind = self.freq_bands.get('mid', 0.0) if hasattr(self, 'freq_bands') else 0.0
        treble_wind = self.freq_bands.get('treble', 0.0) if hasattr(self, 'freq_bands') else 0.0

        # Cache expensive trigonometric calculations for 10ms to improve performance
        if current_time - self.wind_cache['time'] > 0.01:
            self.wind_cache['values'] = {
                'bass_sin': bass_wind * 80 * math.sin(current_time * 2.5),
                'mid_cos': mid_wind * 60 * math.cos(current_time * 1.8),
                'treble_sin': treble_wind * 40 * math.sin(current_time * 4.2),
                'bass_cos_y': bass_wind * 30 * math.cos(current_time * 1.3),
                'mid_sin_y': mid_wind * 25 * math.sin(current_time * 2.1),
                'bass_wind': bass_wind,
                'mid_wind': mid_wind,
                'treble_wind': treble_wind
            }
            self.wind_cache['time'] = current_time
        
        # Use cached wind values
        wind_vals = self.wind_cache['values']
        global_wind_x = wind_vals['bass_sin'] + wind_vals['mid_cos'] + wind_vals['treble_sin']
        global_wind_y = wind_vals['bass_cos_y'] + wind_vals['mid_sin_y']
        
        # Simplified beat gusts (less expensive)
        if self.beat_detected and not hasattr(self, '_last_gust_time') or (current_time - getattr(self, '_last_gust_time', 0) > 0.2):
            gust_strength = 100 + wind_vals['bass_wind'] * 150
            gust_angle = random.uniform(0, 2 * math.pi)
            global_wind_x += math.cos(gust_angle) * gust_strength
            global_wind_y += math.sin(gust_angle) * gust_strength * 0.3
            self._last_gust_time = current_time
        
        # BATCHED bubble processing for better performance
        for bubble in self.bubbles[:]:  # Copy for safe removal
            bubble['age'] = current_time - bubble['birth_time']
            
            # Use cached wind values for performance
            wind_vals = self.wind_cache['values']
            
            # SMOOTHER base movement - more realistic floating
            audio_speed = 0.7 + self.current_level * 1.0
            beat_boost = 1.3 if self.beat_detected else 1.0
            
            # Smooth position update with frame rate compensation
            frame_multiplier = dt * 60  # Normalize to 60fps equivalent
            bubble['x'] += bubble['vx'] * frame_multiplier * audio_speed
            bubble['y'] += bubble['vy'] * frame_multiplier * audio_speed * beat_boost
            
            # OPTIMIZED WIND EFFECTS - use cached values
            wind_force_x = global_wind_x * bubble['wind_resistance'] * bubble['chaos_factor']
            wind_force_y = global_wind_y * bubble['wind_resistance'] * bubble['chaos_factor'] * 0.4
            
            # Apply wind forces to velocity (smoother integration)
            bubble['vx'] += wind_force_x * dt * 0.5
            bubble['vy'] += wind_force_y * dt * 0.4
            
            # Individual bubble turbulence patterns (use cached wind values)
            bubble['turbulence_phase'] += dt * (2 + wind_vals['treble_wind'] * 5)
            bubble['drift_phase'] += dt * (1.5 + wind_vals['mid_wind'] * 3)
            bubble['spiral_phase'] += dt * (1 + wind_vals['bass_wind'] * 2.5)
            
            # OPTIMIZED multi-layered movement - use cached wind values
            # Pre-calculate common values to reduce repeated calculations
            chaos_factor = bubble['chaos_factor']
            
            # 1. Turbulence (gentle random movement)
            turbulence_x = math.sin(bubble['turbulence_phase']) * wind_vals['treble_wind'] * 15 * chaos_factor
            turbulence_y = math.cos(bubble['turbulence_phase'] * 1.3) * wind_vals['treble_wind'] * 8 * chaos_factor
            
            # 2. Drift (slow sweeping motion)  
            drift_x = math.sin(bubble['drift_phase']) * wind_vals['mid_wind'] * 25 * chaos_factor
            drift_y = math.cos(bubble['drift_phase'] * 0.7) * wind_vals['mid_wind'] * 10 * chaos_factor
            
            # 3. Spiral motion (gentle circular motions)
            spiral_radius = 8 + wind_vals['bass_wind'] * 20
            spiral_x = math.cos(bubble['spiral_phase']) * spiral_radius * chaos_factor
            spiral_y = math.sin(bubble['spiral_phase']) * spiral_radius * 0.3 * chaos_factor
            
            # Apply all movement forces (smoothly integrated)
            bubble['vx'] += (turbulence_x + drift_x) * dt * 0.3  # Reduced for smoothness
            bubble['vy'] += (turbulence_y + drift_y) * dt * 0.2
            bubble['x'] += spiral_x * dt * 0.2  # Gentler spiral motion
            bubble['y'] += spiral_y * dt * 0.15
            
            # SMOOTHER wobble with reduced intensity to prevent flashing
            bubble['wobble_phase'] += bubble['wobble_speed'] * dt * (1 + self.current_level * 0.5)  # Much less audio effect
            wobble_intensity = 4 + bubble['base_radius'] * 0.1 + bass_wind * 8  # Reduced wobble intensity
            bubble['x'] += math.sin(bubble['wobble_phase']) * wobble_intensity * dt * bubble['chaos_factor'] * 0.5  # Half intensity
            
            # REDUCED chaotic velocity bursts to prevent erratic movement
            if self.current_level > 0.8:  # Higher threshold
                chaos_burst_x = random.uniform(-20, 20) * bubble['chaos_factor'] * self.current_level  # Much smaller bursts
                chaos_burst_y = random.uniform(-15, 15) * bubble['chaos_factor'] * self.current_level
                bubble['vx'] += chaos_burst_x * dt * 0.05  # Reduced impact
                bubble['vy'] += chaos_burst_y * dt * 0.05
            
            # MUCH smoother shimmer effect - reduce rapid changes
            bubble['shimmer_phase'] += bubble['shimmer_speed'] * dt * (1 + treble_wind * 0.3)  # Reduced treble effect
            shimmer = 0.95 + 0.05 * math.sin(bubble['shimmer_phase'])  # Much gentler size variation
            bubble['radius'] = bubble['base_radius'] * shimmer
            
            # GENTLER audio-reactive size pulsing to reduce flashing
            if self.beat_detected:
                bubble['radius'] *= 1.1  # Much gentler beat response (was 1.4)
            
            # Smoother bass pulsing
            bass_pulse = 1.0 + bass_wind * 0.2  # Reduced from 0.5 to 0.2
            bubble['radius'] *= bass_pulse
            
            # GENTLER buoyancy - slower rise
            base_buoyancy = -8 - bubble['base_radius'] * 0.2  # Reduced from -10 and -0.3
            # Large bubbles still rise faster, but not as dramatically
            bubble['vy'] += base_buoyancy * dt
            
            # Air resistance/drag - varies with bubble size
            drag_x = 0.95 - bubble['base_radius'] * 0.001  # Larger bubbles have more drag
            drag_y = 0.98 - bubble['base_radius'] * 0.0005
            bubble['vx'] *= drag_x
            bubble['vy'] *= drag_y
            
            # Velocity limits to prevent bubbles from moving too fast
            max_velocity = 50 + bubble['base_radius']
            if abs(bubble['vx']) > max_velocity:
                bubble['vx'] = max_velocity if bubble['vx'] > 0 else -max_velocity
            if abs(bubble['vy']) > max_velocity * 1.5:  # Allow faster vertical movement
                bubble['vy'] = max_velocity * 1.5 if bubble['vy'] > 0 else -max_velocity * 1.5
            
            # Softer boundary interactions
            margin = bubble['radius'] * 1.2
            if bubble['x'] < margin:
                bubble['x'] = margin
                bubble['vx'] = abs(bubble['vx']) * 0.4  # Gentler bounce
            elif bubble['x'] > self.width - margin:
                bubble['x'] = self.width - margin
                bubble['vx'] = -abs(bubble['vx']) * 0.4
            
            # Remove bubbles that drift too far or are too old
            if bubble['y'] < -100 or bubble['age'] > 25:  # Longer lifespan for slower movement
                self.bubbles.remove(bubble)
                continue
                
            # Reduced random popping since bubbles move slower
            if bubble['size'] == 'small' and random.random() < 0.0002:  # Less frequent
                self.bubbles.remove(bubble)
    
    def _spawn_new_bubbles(self, current_time):
        """Spawn new bubbles with wild characteristics based on audio"""
        # Spawn rate calculation - more controlled for slower movement
        base_rate = 1.5  # Slightly reduced since bubbles live longer
        audio_rate = self.current_level * 4.0
        bass_rate = self.freq_bands.get('bass', 0.0) * 6.0
        beat_rate = 8.0 if self.beat_detected else 0.0
        total_rate = base_rate + audio_rate + bass_rate + beat_rate
        
        if current_time - self.bubble_spawn_timer > (1.0 / total_rate):
            if len(self.bubbles) < 100:  # Slightly reduced limit
                # Audio-driven bubble characteristics
                bass = self.freq_bands.get('bass', 0.0)
                mid = self.freq_bands.get('mid', 0.0)
                treble = self.freq_bands.get('treble', 0.0)
                
                # Spawn different bubble types based on audio content
                if bass > 0.6:  # Heavy bass = slow, large, chaotic bubbles
                    spawn_count = random.randint(2, 4)
                    for _ in range(spawn_count):
                        bubble = self._create_bubble()
                        bubble['chaos_factor'] = random.uniform(0.8, 1.2)  # Extra chaotic
                        bubble['wind_resistance'] = random.uniform(0.8, 1.0)  # Highly wind-affected
                        # Bias toward larger sizes for bass
                        if random.random() < 0.4:
                            bubble['size'] = 'large'
                            bubble['base_radius'] = random.uniform(35, 55)
                            bubble['radius'] = bubble['base_radius']
                        # Bass bubbles tend to be more colorful (higher chance of random colors)
                        if random.random() < 0.3:  # 30% chance to override color type
                            bubble['color_type'] = 'random'
                        self.bubbles.append(bubble)
                        
                elif treble > 0.5:  # High treble = fast, tiny, twitchy bubbles
                    spawn_count = random.randint(3, 6)  # Lots of tiny ones
                    for _ in range(spawn_count):
                        bubble = self._create_bubble()
                        bubble['chaos_factor'] = random.uniform(1.2, 1.5)  # Super chaotic
                        bubble['wind_resistance'] = random.uniform(0.9, 1.0)  # Maximum wind effect
                        # Bias toward tiny bubbles for treble
                        bubble['size'] = 'small'
                        bubble['base_radius'] = random.uniform(3, 12)
                        bubble['radius'] = bubble['base_radius']
                        bubble['wobble_speed'] = random.uniform(3, 6)  # Faster wobble (reduced for smoothness)
                        # Treble bubbles are often sparkly/random colored
                        if random.random() < 0.4:  # 40% chance for random colors on treble
                            bubble['color_type'] = 'random'
                        self.bubbles.append(bubble)
                        
                elif mid > 0.4:  # Mids = smooth, flowing, graceful bubbles  
                    spawn_count = random.randint(1, 3)
                    for _ in range(spawn_count):
                        bubble = self._create_bubble()
                        bubble['chaos_factor'] = random.uniform(0.4, 0.8)  # More graceful
                        bubble['wind_resistance'] = random.uniform(0.6, 0.9)  # Moderate wind
                        bubble['wobble_speed'] = random.uniform(1, 2)  # Gentle wobble
                        self.bubbles.append(bubble)
                        
                else:  # Normal spawning
                    bubble = self._create_bubble()
                    # Random wildness variation
                    bubble['chaos_factor'] = random.uniform(0.3, 1.0)
                    bubble['wind_resistance'] = random.uniform(0.5, 1.0)
                    self.bubbles.append(bubble)
            
            self.bubble_spawn_timer = current_time
    
    def _draw_underwater_background(self):
        """Draw cached underwater gradient background for performance"""
        if not self.canvas:
            return
            
        current_time = time.time()
        
        # PERFORMANCE: Only redraw background every 100ms instead of every frame
        if current_time - self.background_cache_time < self.background_cache_interval:
            return
        
        self.background_cache_time = current_time
            
        try:
            # REDUCED gradient steps for better performance
            steps = 12  # Reduced from 20 to 12
            step_height = self.height / steps
            
            for step in range(steps):
                y_pos = step * step_height
                depth_ratio = step / steps
                
                # STABLE underwater colors - no beat flashing
                base_intensity = 0.15 + (1.0 - depth_ratio) * 0.35
                audio_boost = self.current_level * 0.1
                intensity = base_intensity + audio_boost
                
                # Simplified color selection for performance
                if step % 3 == 0:
                    color = self._get_pure_song_color(primary=True, intensity=intensity)
                elif step % 3 == 1 and self.song_secondary_color != 'none':
                    color = self._get_pure_song_color(primary=False, intensity=intensity * 0.8)
                else:
                    # Create deep blue-green for underwater feel
                    color = self._get_underwater_color(intensity)
                
                self.canvas.create_rectangle(
                    0, int(y_pos), self.width, int(y_pos + step_height + 2),  # Slight overlap to prevent gaps
                    fill=color, outline=""
                )
        except:
            pass
    
    def _draw_all_bubbles(self, current_time):
        """Draw all bubbles with optimized rendering"""
        if not self.canvas:
            return
            
        try:
            # PERFORMANCE: Skip expensive sorting most of the time
            self.frame_skip_counter += 1
            if self.frame_skip_counter % 3 == 0:  # Only sort every 3rd frame
                self.bubbles.sort(key=lambda b: b['base_radius'], reverse=True)
            
            # Draw bubbles in current order (mostly sorted)
            for bubble in self.bubbles:
                self._draw_single_bubble(bubble, current_time)
        except:
            pass
    
    def _draw_single_bubble(self, bubble, current_time):
        """Draw a single bubble with realistic effects"""
        if not self.canvas:
            return
            
        try:
            # Age-based transparency
            age = bubble['age']
            if age < 0.3:
                alpha = age / 0.3
            elif age > 12:
                alpha = max(0.2, 1.0 - (age - 12) / 3)
            else:
                alpha = 1.0
            
            final_alpha = alpha * bubble['glow_intensity']
            radius = bubble['radius']
            
            # Choose bubble color based on color type from song config
            if bubble['color_type'] == 'random':
                # Use random palette color
                bubble_color = self._get_random_palette_color(intensity=0.7 * final_alpha)
                outline_color = self._get_random_palette_color(intensity=0.9 * final_alpha)
            elif bubble['color_type'] == 'secondary':
                # Use secondary song color
                bubble_color = self._get_pure_song_color(primary=False, intensity=0.7 * final_alpha)
                outline_color = self._get_pure_song_color(primary=False, intensity=0.9 * final_alpha)
            else:  # 'primary'
                # Use primary song color
                bubble_color = self._get_pure_song_color(primary=True, intensity=0.7 * final_alpha)
                outline_color = self._get_pure_song_color(primary=True, intensity=0.9 * final_alpha)
            
            # OPTIMIZED bubble rendering - fewer draw calls for small bubbles
            if radius < 12:
                # Small bubbles: simplified rendering (1 draw call instead of 3-4)
                self.canvas.create_oval(
                    bubble['x'] - radius, bubble['y'] - radius,
                    bubble['x'] + radius, bubble['y'] + radius,
                    fill=bubble_color, outline=outline_color, width=1
                )
            else:
                # Large bubbles: full effect rendering
                # Outer glow (complementary to main color)
                glow_radius = radius * 1.2  # Slightly smaller glow for performance
                if bubble['color_type'] == 'random':
                    glow_color = self._get_random_palette_color(intensity=0.3 * final_alpha)
                elif bubble['color_type'] == 'secondary':
                    glow_color = self._get_pure_song_color(primary=True, intensity=0.3 * final_alpha)
                else:  # 'primary'
                    glow_color = self._get_pure_song_color(primary=False, intensity=0.3 * final_alpha) if self.song_secondary_color != 'none' else bubble_color
                
                self.canvas.create_oval(
                    bubble['x'] - glow_radius, bubble['y'] - glow_radius,
                    bubble['x'] + glow_radius, bubble['y'] + glow_radius,
                    fill=glow_color, outline="", stipple="gray25"
                )
                
                # Main bubble
                self.canvas.create_oval(
                    bubble['x'] - radius, bubble['y'] - radius,
                    bubble['x'] + radius, bubble['y'] + radius,
                    fill=bubble_color, outline=outline_color, width=1
                )
            
            # OPTIMIZED highlight - only for large bubbles, simplified rendering
            if radius > 18:  # Only very large bubbles get highlights
                highlight_size = radius * 0.2  # Smaller highlight
                highlight_x = bubble['x'] - radius * 0.25
                highlight_y = bubble['y'] - radius * 0.3
                
                highlight_intensity = min(1.0, final_alpha * 0.6)  # Further reduced
                highlight_color = f"#{int(180*highlight_intensity):02x}{int(180*highlight_intensity):02x}{int(180*highlight_intensity):02x}"
                
                self.canvas.create_oval(
                    highlight_x - highlight_size, highlight_y - highlight_size,
                    highlight_x + highlight_size, highlight_y + highlight_size,
                    fill=highlight_color, outline=""
                )
        except:
            pass
    
    def _draw_surface_effects(self, current_time):
        """Draw water surface effects at the top"""
        if not self.canvas:
            return
            
        try:
            # Animated surface ripples
            wave_count = 6
            for i in range(wave_count):
                wave_phase = (current_time * 1.5 + i * math.pi / 3) % (2 * math.pi)
                wave_height = 8 + self.current_level * 15
                wave_y = 15 + math.sin(wave_phase) * wave_height
                
                wave_intensity = 0.4 + self.current_level * 0.15  # Reduced effect (was 0.3)
                # REMOVED beat flashing from surface waves
                
                wave_color = self._get_pure_song_color(
                    primary=(i % 2 == 0), 
                    intensity=wave_intensity
                )
                
                wave_width = self.width // wave_count
                self.canvas.create_rectangle(
                    i * wave_width, 0,
                    (i + 1) * wave_width, int(wave_y),
                    fill=wave_color, outline="", stipple="gray75"
                )
        except:
            pass
    
    # Color methods
    def _get_pure_song_color(self, primary: bool = True, intensity: float = 1.0) -> str:
        """Get pure primary or secondary song color"""
        color_name = self.song_primary_color if primary else self.song_secondary_color
        
        # Handle auto/none cases - use dynamic colors
        if (self.song_primary_color == 'auto' or not self.song_primary_color) and (self.song_secondary_color == 'none' or not self.song_secondary_color):
            return self._get_dynamic_song_color(0.5, intensity)
        
        if color_name == 'auto' or color_name == 'none' or not color_name:
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
        
        return "#ffffff"
    
    def _get_dynamic_song_color(self, hue_offset: float, intensity: float) -> str:
        """Generate dynamic audio-reactive colors"""
        base_hue = (time.time() * 0.1 + hue_offset) % 1.0
        
        # Add audio-reactive color shifts
        bass_shift = self.freq_bands.get('bass', 0.0) * 0.2
        mid_shift = self.freq_bands.get('mid', 0.0) * 0.15
        treble_shift = self.freq_bands.get('treble', 0.0) * 0.1
        
        final_hue = (base_hue + bass_shift + mid_shift + treble_shift) % 1.0
        
        r, g, b = colorsys.hsv_to_rgb(final_hue, 0.8, intensity)
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
    
    def _get_random_palette_color(self, intensity: float) -> str:
        """Get stable random color from palette - prevents flashing"""
        # Use bubble's birth time as seed for consistent color per bubble
        if not hasattr(self, '_color_seed'):
            self._color_seed = random.uniform(0, 1)
        
        # MUCH slower color cycling to prevent flashing
        base_hue = (time.time() * 0.02 + self._color_seed) % 1.0  # 5x slower (was 0.1)
        
        # Minimal audio-reactive variation to prevent rapid color changes
        bass_shift = self.freq_bands.get('bass', 0.0) * 0.05  # Much smaller shifts
        mid_shift = self.freq_bands.get('mid', 0.0) * 0.03
        treble_shift = self.freq_bands.get('treble', 0.0) * 0.02
        
        final_hue = (base_hue + bass_shift + mid_shift + treble_shift) % 1.0
        
        # Stable saturation and value to prevent flashing
        saturation = 0.8  # Fixed saturation (removed random)
        value = min(1.0, intensity)  # Stable value (removed random)
        
        r, g, b = colorsys.hsv_to_rgb(final_hue, saturation, value)
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
    
    def _get_underwater_color(self, intensity: float) -> str:
        """Get deep underwater blue-green colors"""
        # Create realistic underwater colors
        blue_intensity = intensity * 0.8
        green_intensity = intensity * 0.6
        red_intensity = intensity * 0.2
        
        return f"#{int(red_intensity * 255):02x}{int(green_intensity * 255):02x}{int(blue_intensity * 255):02x}"
    
    def cleanup(self):
        """Clean up bubble resources"""
        self.bubbles = []