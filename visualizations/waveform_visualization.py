"""
Waveform visualization with morphing instrument shapes and enhanced effects
"""

import math
import time
import random
from typing import List, Dict, Any, Tuple
from .base_visualization import BaseVisualization


class WaveformVisualization(BaseVisualization):
    """Waveform visualization with morphing into instrument shapes"""
    
    def __init__(self):
        super().__init__()
        
        # Waveform-specific state
        self.waveform_rotation_active = False
        self.waveform_rotation_angle = 0.0
        self.waveform_rotation_speed = 1.0
        self.waveform_rotation_start_time = 0.0
        self.waveform_rotation_duration = 0.0
        
        # Morphing system
        self.waveform_morph_mode = 'normal'
        self.waveform_morph_progress = 0.0
        self.waveform_morph_start_time = 0.0
        self.waveform_morph_duration = 3.0  # 3 seconds to morph
        self.waveform_shape_hold_duration = 8.0  # 8 seconds to hold shape
        self.waveform_shape_cycle_time = 0.0
        self.waveform_shape_index = 0
        self.waveform_shape_sequence = [
            'guitar', 'drums', 'microphone', 'keyboard', 'violin',
            'saxophone', 'star', 'heart', 'spiral'
        ]
        
        # Smoke particle system
        self.smoke_particles = []
        self.visualization_start_time = None
        
    def initialize(self):
        """Initialize waveform visualization"""
        super().initialize()
        self.smoke_particles = []
        self.waveform_rotation_active = False
        self.waveform_rotation_angle = 0.0
        self.visualization_start_time = time.time()
        
        # Initialize shape morphing - START WITH NORMAL WAVEFORM
        self.waveform_shape_cycle_time = 0.0
        self.waveform_shape_index = 0
        self.waveform_morph_progress = 0.0
        self.waveform_morph_mode = 'normal'  # Start with normal waveform, not morphed

    def render(self):
        """Render waveform visualization with rotation, morphing, and smoke effects"""
        if not self.canvas or not self._validate_canvas():
            return
            
        try:
            center_x = self.width // 2
            center_y = self.height // 2
            
            # Update all animation states before rendering
            self._update_smoke_particles()
            self._update_waveform_rotation()
            self._maybe_trigger_waveform_rotation()
            self._update_waveform_morphing()
            
            # Generate waveform points with dramatic audio-reactive response (optimized)
            points = []
            num_points = 60  # Reduced from 100 for better performance
            
            # Get audio data with proper scaling for visual impact
            current_level = self.current_level
            bass = self.freq_bands.get('bass', 0.0)
            mid = self.freq_bands.get('mid', 0.0) 
            treble = self.freq_bands.get('treble', 0.0)
            
            # LOWERED base amplitude for more visible effects at quiet levels
            base_amplitude = 15  # Even smaller base for maximum audio effect visibility
            
            # ENHANCED AUDIO-REACTIVE SCALING - Much more dramatic pulsing at lower levels!
            audio_multiplier = 800  # Higher multiplier for quiet audio visibility
            level_amplitude = current_level * audio_multiplier  # Overall level pulsing
            bass_amplitude = bass * 600   # MASSIVE bass response for big drops
            mid_amplitude = mid * 500     # Strong mid response for vocals  
            treble_amplitude = treble * 550  # High treble for guitar solos and cymbals
            
            # ENHANCED beat effects with SNARE AND BASS DRUM DETECTION
            # Detect snare hits: high mid-frequency content with sharp transient
            snare_threshold = 0.45  # Higher threshold for more accurate snare detection
            snare_ratio_threshold = 1.7  # Stronger ratio - mid must clearly dominate bass
            snare_detected = (mid > snare_threshold and 
                             mid > bass * snare_ratio_threshold and 
                             treble > 0.35 and  # More high-freq content required
                             mid > treble * 0.8 and  # Mid should be strong relative to treble
                             self.beat_detected)  # Must also be a beat
            
            # Detect bass/kick drum hits: high bass content with lower mid/treble
            bass_threshold = 0.6  # Increased threshold - must be significant bass
            kick_ratio_threshold = 1.8  # Much stronger ratio requirement - bass must dominate
            kick_detected = (bass > bass_threshold and 
                            bass > mid * kick_ratio_threshold and 
                            bass > treble * 1.5 and  # Bass must be significantly stronger than treble
                            self.beat_detected and  # Must be a beat
                            not snare_detected)  # Not a snare hit
            
            if snare_detected:
                # MASSIVE snare pulse - much stronger than regular beats
                beat_multiplier = 500  # Huge snare pulse
                beat_burst = 300  # Massive burst for snare hits
                snare_amplitude = 400  # Additional snare-specific amplitude
                kick_amplitude = 0
                print(f"SNARE DETECTED! mid={mid:.3f}, bass={bass:.3f}, treble={treble:.3f}")
            elif kick_detected:
                # BASS/KICK drum pulse - different characteristics than snare
                beat_multiplier = 400  # Strong kick pulse
                beat_burst = 200  # Good burst for kick hits
                snare_amplitude = 0
                kick_amplitude = 350  # Additional kick-specific amplitude
                print(f"KICK DETECTED! bass={bass:.3f}, mid={mid:.3f}, treble={treble:.3f}")
            elif self.beat_detected:
                # Other beat (hi-hat, cymbal, etc.)
                beat_multiplier = 300  # Regular beat pulse
                beat_burst = 150  # Regular burst effect
                snare_amplitude = 0
                kick_amplitude = 0
            else:
                # No beat detected
                beat_multiplier = 80   # Gentle baseline
                beat_burst = 0
                snare_amplitude = 0
                kick_amplitude = 0
            
            beat_amplitude = self.beat_pulse * beat_multiplier
            burst_amplitude = beat_burst if self.beat_detected else 0
            
            # Total amplitude combines all audio effects INCLUDING snare AND kick pulses
            total_amplitude = (base_amplitude + level_amplitude + bass_amplitude + 
                             mid_amplitude + treble_amplitude + beat_amplitude + burst_amplitude + 
                             snare_amplitude + kick_amplitude)
            
            # Debug audio reactivity occasionally  
            if self.frame_count % 300 == 0:  # Every 5 seconds (reduced debug frequency)
                print(f"WAVEFORM AUDIO: level={current_level:.3f}, bass={bass:.3f}, mid={mid:.3f}, treble={treble:.3f}")
                print(f"WAVEFORM AMPLITUDES: base={base_amplitude}, level={level_amplitude:.1f}, bass={bass_amplitude:.1f}, total={total_amplitude:.1f}")
                print(f"WAVEFORM BEAT: pulse={self.beat_pulse:.3f}, detected={self.beat_detected}")
                print(f"WAVEFORM DEBUG: frame_count={self.frame_count}, is_running={self.is_running}, canvas={self.canvas is not None}")
            
            # Generate base waveform points with morphing
            for i in range(num_points):
                x = (i / num_points) * self.width
                
                # Create multiple layered waveforms for richer visualization
                current_time = time.time()
                
                # FUNKY MULTI-LAYERED WAVEFORM WITH DIFFERENT FREQUENCIES
                # Base wave with subtle animation
                base_wave = math.sin((i / 8) + (current_time * 2.0)) * base_amplitude
                
                # BASS WAVE - slow, deep, massive movements
                bass_wave1 = math.sin((i / 35) + (current_time * 1.2)) * bass_amplitude * (0.5 + bass * 0.5)
                bass_wave2 = math.cos((i / 28) + (current_time * 0.8)) * bass_amplitude * bass * 0.3
                combined_bass = bass_wave1 + bass_wave2
                
                # MID WAVE - vocals and instruments with enhanced vocal pulsing
                vocal_pulse_intensity = 1.0 + mid * 3.0  # Vocals drive strong pulsing
                mid_wave1 = math.sin((i / 12) + (current_time * 3.0)) * mid_amplitude * vocal_pulse_intensity * (0.4 + mid * 0.6)
                mid_wave2 = math.sin((i / 8) + (current_time * 2.3)) * mid_amplitude * vocal_pulse_intensity * mid * 0.4
                # Add vocal-specific harmonic for richness
                vocal_harmonic = math.sin((i / 6) + (current_time * 1.8)) * mid_amplitude * mid * 0.3 * vocal_pulse_intensity
                combined_mid = mid_wave1 + mid_wave2 + vocal_harmonic
                
                # TREBLE WAVE - fast, sharp spikes for high frequencies
                treble_spike_intensity = 1.0 + treble * 4.0  # High treble creates dramatic spikes
                treble_wave1 = math.sin((i / 3) + (current_time * 6.0)) * treble_amplitude * treble_spike_intensity * (0.3 + treble * 0.7)
                treble_wave2 = math.sin((i / 2) + (current_time * 8.5)) * treble_amplitude * treble_spike_intensity * treble * 0.5  
                treble_wave3 = math.cos((i / 1.5) + (current_time * 12.0)) * treble_amplitude * treble_spike_intensity * treble * 0.2
                # Add sharp spikes for high treble content
                if treble > 0.4:  # High treble content
                    treble_spike = math.sin(i * 0.1 + (current_time * 15.0)) * treble_amplitude * treble * 2.0
                    treble_wave3 += treble_spike
                combined_treble = treble_wave1 + treble_wave2 + treble_wave3
                
                # ENHANCED BEAT EXPLOSION EFFECTS with SNARE AND KICK DETECTION
                beat_explosion = 0
                beat_pulse_wave = 0
                beat_harmonic = 0
                snare_crack = 0
                snare_reverb = 0
                kick_thump = 0
                kick_sub = 0
                
                if snare_detected:
                    # MASSIVE SNARE EXPLOSION - much sharper and more intense than regular beats
                    beat_explosion = math.sin(i / 1.5) * beat_amplitude * math.exp(-((current_time - self.last_beat_time) * 8))
                    
                    # SNARE CRACK - sharp, high-frequency component
                    snare_crack = (math.sin(i * 0.8) * snare_amplitude * 
                                  math.exp(-((current_time - self.last_beat_time) * 12)))  # Very sharp decay
                    
                    # SNARE REVERB - wider, sustained tail
                    snare_reverb = (math.sin((i / 6) + (current_time * 8)) * snare_amplitude * 0.4 * 
                                   math.exp(-((current_time - self.last_beat_time) * 2)))  # Longer tail
                    
                    # Enhanced pulse wave for snare hits
                    beat_pulse_wave = (math.sin((i / 3) + (current_time * 6)) * burst_amplitude * 
                                      math.exp(-((current_time - self.last_beat_time) * 4)))
                    
                    # Snare harmonics - sharper and more cutting
                    beat_harmonic = math.cos(i / 2) * (beat_amplitude * 0.7) * math.exp(-((current_time - self.last_beat_time) * 15))
                    
                elif kick_detected:
                    # MASSIVE KICK/BASS DRUM EXPLOSION - deep, wide, powerful
                    beat_explosion = math.sin(i / 4) * beat_amplitude * math.exp(-((current_time - self.last_beat_time) * 5))
                    
                    # KICK THUMP - deep, low-frequency foundation
                    kick_thump = (math.sin((i / 8) + (current_time * 2)) * kick_amplitude * 
                                 math.exp(-((current_time - self.last_beat_time) * 4)))  # Slower decay for bass
                    
                    # KICK SUB - ultra-low rumble effect
                    kick_sub = (math.sin((i / 12) + (current_time * 1.5)) * kick_amplitude * 0.6 * 
                               math.exp(-((current_time - self.last_beat_time) * 3)))  # Long sustain
                    
                    # Enhanced pulse wave for kick hits - broader and deeper
                    beat_pulse_wave = (math.sin((i / 5) + (current_time * 3)) * burst_amplitude * 
                                      math.exp(-((current_time - self.last_beat_time) * 2.5)))
                    
                    # Kick harmonics - deeper and wider than snare
                    beat_harmonic = math.cos(i / 4) * (beat_amplitude * 0.8) * math.exp(-((current_time - self.last_beat_time) * 6))
                    
                elif self.beat_detected:
                    # Other beat explosion (hi-hat, cymbal, etc.)
                    beat_explosion = math.sin(i / 2) * beat_amplitude * math.exp(-((current_time - self.last_beat_time) * 6))
                    
                    # Regular beat pulse wave
                    beat_pulse_wave = (math.sin((i / 4) + (current_time * 4)) * burst_amplitude * 
                                      math.exp(-((current_time - self.last_beat_time) * 3)))
                    
                    # Regular beat harmonics
                    beat_harmonic = math.cos(i / 3) * (beat_amplitude * 0.5) * math.exp(-((current_time - self.last_beat_time) * 10))
                
                # LEVEL-BASED WAVE MODULATION - overall energy affects everything
                level_modulation1 = level_amplitude * math.sin((i / 6) + (current_time * 2.5))
                level_modulation2 = level_amplitude * math.cos((i / 10) + (current_time * 1.8)) * 0.6
                
                # COMBINE ALL WAVE COMPONENTS INCLUDING SNARE AND KICK EFFECTS
                normal_y = (center_y + base_wave + combined_bass + combined_mid + combined_treble + 
                           beat_explosion + beat_pulse_wave + beat_harmonic + snare_crack + snare_reverb +
                           kick_thump + kick_sub + level_modulation1 + level_modulation2)
                
                # Apply morphing to create instrument shapes
                morph_offset = self._calculate_morph_offset(i, num_points, center_x, center_y, x, normal_y)
                y = normal_y + morph_offset
                
                # Apply rotation if active
                if self.waveform_rotation_active:
                    # Translate to center, rotate, translate back
                    rel_x = x - center_x
                    rel_y = y - center_y
                    cos_angle = math.cos(self.waveform_rotation_angle)
                    sin_angle = math.sin(self.waveform_rotation_angle)
                    
                    rotated_x = rel_x * cos_angle - rel_y * sin_angle + center_x
                    rotated_y = rel_x * sin_angle + rel_y * cos_angle + center_y
                    points.extend([rotated_x, rotated_y])
                    
                    # Debug rotation state very occasionally
                    if i == 0 and self.frame_count % 600 == 0:  # Print every 10 seconds only
                        print(f"ROTATING: angle={self.waveform_rotation_angle:.2f}, active={self.waveform_rotation_active}")
                else:
                    points.extend([x, y])
        
            # Render high-fidelity smoke effects
            self._render_smoke_effects()
            
            # Draw waveform with dynamic colors - primary with random related variations
            if len(points) >= 4:
                # Get base color
                if self.song_primary_color == 'yellow':
                    base_color = (255, 255, 0)
                elif self.song_primary_color == 'red':
                    base_color = (255, 0, 0)
                elif self.song_primary_color == 'blue':
                    base_color = (0, 0, 255)
                elif self.song_primary_color == 'white':
                    base_color = (255, 255, 255)
                elif self.song_primary_color == 'green':
                    base_color = (0, 255, 0)
                elif self.song_primary_color == 'orange':
                    base_color = (255, 128, 0)
                elif self.song_primary_color == 'purple':
                    base_color = (128, 0, 255)
                elif self.song_primary_color == 'pink':
                    base_color = (255, 0, 128)
                else:
                    base_color = (255, 255, 255)  # Default to white
                
                # Add enhanced color variation with beat reactivity
                color_variation = self._get_waveform_color_variation(base_color)
                
                # ENHANCED beat-reactive color intensity with SNARE AND KICK DETECTION
                if snare_detected:
                    # MASSIVE color intensity for snare hits
                    intensity_boost = 1.8  # Much higher base boost for snare
                    time_since_beat = current_time - self.last_beat_time
                    snare_pulse_intensity = max(0, 1.0 - (time_since_beat * 5))  # Faster fade for snare
                    extra_boost = snare_pulse_intensity * 1.0  # Bigger extra boost for snare
                    total_boost = intensity_boost + extra_boost
                    
                    # SUPER boost for snare - make it really pop
                    boosted_color = (
                        min(255, int(color_variation[0] * total_boost)),
                        min(255, int(color_variation[1] * total_boost)),
                        min(255, int(color_variation[2] * total_boost))
                    )
                    color_variation = boosted_color
                elif kick_detected:
                    # DEEP color intensity for kick/bass drum hits
                    intensity_boost = 1.6  # Strong boost for kick
                    time_since_beat = current_time - self.last_beat_time
                    kick_pulse_intensity = max(0, 1.0 - (time_since_beat * 3.5))  # Slower fade for bass
                    extra_boost = kick_pulse_intensity * 0.8  # Good extra boost for kick
                    total_boost = intensity_boost + extra_boost
                    
                    # Deep boost for kick - emphasis on warmth
                    boosted_color = (
                        min(255, int(color_variation[0] * total_boost)),
                        min(255, int(color_variation[1] * total_boost * 0.9)),  # Slightly less green
                        min(255, int(color_variation[2] * total_boost * 0.8))   # Less blue for warmth
                    )
                    color_variation = boosted_color
                elif self.beat_detected:
                    # Other beat color intensity
                    intensity_boost = 1.4
                    time_since_beat = current_time - self.last_beat_time
                    pulse_intensity = max(0, 1.0 - (time_since_beat * 3))  # Fade over 0.33 seconds
                    extra_boost = pulse_intensity * 0.6
                    total_boost = intensity_boost + extra_boost
                    
                    # Boost each color channel but cap at 255
                    boosted_color = (
                        min(255, int(color_variation[0] * total_boost)),
                        min(255, int(color_variation[1] * total_boost)),
                        min(255, int(color_variation[2] * total_boost))
                    )
                    color_variation = boosted_color
                
                color = f"#{color_variation[0]:02x}{color_variation[1]:02x}{color_variation[2]:02x}"
                
                # Debug color output occasionally (reduced frequency)
                if self.frame_count % 600 == 0:  # Every 10 seconds
                    print(f"WAVEFORM: primary='{self.song_primary_color}', base={base_color}, varied={color_variation}")
                    print(f"WAVEFORM: Color shift from base: R{color_variation[0]-base_color[0]:+d}, G{color_variation[1]-base_color[1]:+d}, B{color_variation[2]-base_color[2]:+d}")
                
                # OPTIMIZED MULTI-LAYER WAVEFORM RENDERING 
                # Pre-calculate colors once per frame instead of per layer
                outline_color = self._get_outline_color(base_color)
                outline_hex = f"#{outline_color[0]:02x}{outline_color[1]:02x}{outline_color[2]:02x}"
                
                # ENHANCED Beat-reactive width changes with VOCAL and TREBLE responsiveness
                if snare_detected:
                    base_width = 24  # MASSIVE thickness for snare hits
                    time_since_beat = current_time - self.last_beat_time
                    snare_pulse_decay = max(0, 1.0 - (time_since_beat * 6))  # Faster decay for snare
                    extra_width = int(snare_pulse_decay * 16)  # Up to 16 additional pixels for snare
                    base_width += extra_width
                elif kick_detected:
                    base_width = 20  # HUGE thickness for kick/bass drum hits
                    time_since_beat = current_time - self.last_beat_time
                    kick_pulse_decay = max(0, 1.0 - (time_since_beat * 4))  # Slower decay for bass
                    extra_width = int(kick_pulse_decay * 12)  # Up to 12 additional pixels for kick
                    base_width += extra_width
                elif treble > 0.5:  # HIGH TREBLE SPIKES - sharp and dramatic
                    base_width = 18 + int(treble * 20)  # Treble makes waveform thicker and spiky
                    print(f"TREBLE SPIKE: base_width={base_width}, treble={treble:.3f}")
                elif mid > 0.4:  # VOCAL PULSING - smooth and flowing
                    vocal_pulse = 1.0 + math.sin(current_time * 6) * 0.5  # Smooth pulsing
                    base_width = 8 + int(mid * 15 * vocal_pulse)  # Vocals make waveform flow and pulse
                    print(f"VOCAL PULSE: base_width={base_width}, mid={mid:.3f}, pulse={vocal_pulse:.3f}")
                elif self.beat_detected:
                    base_width = 16  # Regular beat thickness
                    time_since_beat = current_time - self.last_beat_time
                    pulse_decay = max(0, 1.0 - (time_since_beat * 4))  # Decay over 0.25 seconds
                    extra_width = int(pulse_decay * 8)  # Up to 8 additional pixels
                    base_width += extra_width
                else:
                    # Dynamic baseline that responds to overall audio
                    base_width = 4 + int(self.current_level * 8)  # Responsive baseline
                
                glow_width = int(base_width * 2.2)  # Even wider glow
                mid_width = int(base_width * 1.5)   # Bigger mid layer
                core_width = int(base_width * 0.9)  # Slightly bigger core
                
                # Optimized: Draw fewer layers to reduce CPU load
                self.canvas.create_line(points, fill=outline_hex, width=glow_width)  # Outer glow
                self.canvas.create_line(points, fill=color, width=mid_width)  # Main layer  
                self.canvas.create_line(points, fill="#FFFFFF", width=core_width)  # Bright core
                
                # Optimized: Reduce random segments frequency for better performance
                if len(points) >= 20 and self.frame_count % 3 == 0:  # Only every 3rd frame
                    # Draw fewer random colored segments
                    segment_length = 12  # Larger segments, fewer draws
                    for i in range(0, len(points) - segment_length, segment_length * 2):  # Skip more
                        if random.random() < 0.2:  # Reduced from 30% to 20%
                            segment_points = points[i:i + segment_length + 2]
                            if len(segment_points) >= 4:
                                random_color = self._get_waveform_color_variation(base_color)
                                random_hex = f"#{random_color[0]:02x}{random_color[1]:02x}{random_color[2]:02x}"
                                self.canvas.create_line(segment_points, fill=random_hex, width=8)
                
                # DRAMATIC AUDIO-REACTIVE SPARKLE EXPLOSIONS
                if len(points) >= 6:
                    sparkle_intensity = self.current_level + (1.0 if self.beat_detected else 0.2)
                    sparkle_color = self._get_sparkle_color(base_color)
                    sparkle_hex = f"#{sparkle_color[0]:02x}{sparkle_color[1]:02x}{sparkle_color[2]:02x}"

                    # More sparkles with higher audio levels
                    sparkle_count = int(3 + sparkle_intensity * 10)
                    for i in range(0, len(points), max(1, len(points) // sparkle_count)):
                        if i + 1 < len(points):
                            # Bigger sparkles on beats and high levels
                            sparkle_size = 1 + int(sparkle_intensity * 4) + (2 if self.beat_detected else 0)

                            # Draw sparkle bursts - multiple overlapping circles
                            for burst in range(2 if self.beat_detected else 1):
                                burst_size = sparkle_size - burst * 1
                                if burst_size > 0:
                                    self.canvas.create_oval(
                                        points[i] - burst_size, points[i + 1] - burst_size,
                                        points[i] + burst_size, points[i + 1] + burst_size,
                                        fill=sparkle_hex if burst == 0 else "#FFFFFF",
                                        outline=""
                                    )

                # MASSIVE BEAT PULSE RINGS - dramatic expanding circles on beats
                if self.beat_detected and len(points) >= 4:
                    time_since_beat = current_time - self.last_beat_time
                    if time_since_beat < 0.3:  # Show pulse rings for 0.3 seconds after beat
                        # Calculate center point of waveform
                        center_point_x = points[len(points) // 2]
                        center_point_y = points[len(points) // 2 + 1] if len(points) // 2 + 1 < len(points) else center_y

                        # Create expanding rings
                        for ring in range(2):
                            ring_progress = (time_since_beat * 5) + (ring * 0.2)  # Stagger the rings
                            if ring_progress < 1.0:
                                ring_radius = int(ring_progress * 100 * (1.0 + bass + mid))  # Audio-reactive size
                                ring_alpha = max(0, 1.0 - ring_progress)  # Fade out as it expands

                                # Ring color based on audio content - LOWERED THRESHOLDS
                                if bass > 0.2:  # Much more sensitive to bass
                                    ring_color = "#FF4444"  # Red for bass
                                elif mid > 0.2:  # Much more sensitive to mids
                                    ring_color = "#44FF44"  # Green for mids
                                elif treble > 0.2:  # Much more sensitive to treble
                                    ring_color = "#4444FF"  # Blue for treble
                                else:
                                    ring_color = "#FFFFFF"  # White default

                                # Draw expanding ring
                                if ring_radius > 2:
                                    self.canvas.create_oval(
                                        center_point_x - ring_radius, center_point_y - ring_radius,
                                        center_point_x + ring_radius, center_point_y + ring_radius,
                                        outline=ring_color, width=max(1, int(4 * ring_alpha)), fill=""
                                    )
                
                
            
        except Exception as e:
            # Ignore canvas errors during shutdown
            pass
    
    def _update_waveform_rotation(self):
        """Update waveform rotation state"""
        current_time = time.time()
        
        if self.waveform_rotation_active:
            # Update rotation angle
            self.waveform_rotation_angle += self.waveform_rotation_speed * 0.016  # Assume ~60fps
            
            # Check if rotation duration has expired
            if current_time - self.waveform_rotation_start_time >= self.waveform_rotation_duration:
                self.waveform_rotation_active = False
                self.waveform_rotation_angle = 0.0
                print("Waveform rotation completed")
     
    def _maybe_trigger_waveform_rotation(self):
        """Randomly trigger waveform rotation based on music intensity"""
        if self.waveform_rotation_active:
            return
            
        current_time = time.time()
        
        # Chance increases over time (starts normal, then gets more likely to rotate)
        # Wait at least 10 seconds before any rotation can start, then gradually increase chance
        if self.visualization_start_time is None:
            time_since_start = 0
        else:
            time_since_start = current_time - self.visualization_start_time
        
        # No rotation for first 10 seconds, then gradually increase chance over next 20 seconds
        if time_since_start < 10.0:
            time_factor = 0.0  # No rotation for first 10 seconds
        else:
            time_factor = min(1.0, (time_since_start - 10.0) / 20.0)  # 0 to 1 over next 20 seconds
        
        # REDUCED base chance for less spinning
        base_chance = 0.001 * time_factor  # 0% to 0.1% chance per frame (reduced from 0.5%)
        
        # REDUCED audio chance for less spinning
        audio_chance = self.current_level * 0.005  # Up to 0.5% with audio (reduced from 1%)
        
        # REDUCED beat chance for less spinning
        beat_chance = 0.01 if self.beat_detected else 0.0  # 1% extra on beats (reduced from 3%)
        
        total_chance = base_chance + audio_chance + beat_chance
        
        if random.random() < total_chance:
            # Start rotation with SLOWER speed
            self.waveform_rotation_active = True
            self.waveform_rotation_start_time = current_time
            self.waveform_rotation_speed = random.uniform(0.3, 1.0)  # MUCH slower rotation (reduced from 1.0-3.0)
            self.waveform_rotation_duration = random.uniform(4.0, 8.0)  # 4-8 seconds
            print(f"Starting waveform rotation: speed={self.waveform_rotation_speed:.2f}, duration={self.waveform_rotation_duration:.1f}s")
    
    def _update_waveform_morphing(self):
        """Update waveform shape morphing animation"""
        current_time = time.time()
        
        # Initialize shape cycle timer if needed
        if self.waveform_shape_cycle_time == 0.0:
            self.waveform_shape_cycle_time = current_time
        
        # DELAY MORPHING - Start with 15 seconds of normal waveform
        initial_delay = 15.0  # 15 seconds before any morphing starts
        if (current_time - self.waveform_shape_cycle_time) < initial_delay:
            self.waveform_morph_mode = 'normal'
            self.waveform_morph_progress = 0.0
            return
        
        # Check if it's time to advance to next shape
        cycle_elapsed = (current_time - self.waveform_shape_cycle_time) - initial_delay
        total_cycle_time = self.waveform_shape_hold_duration + self.waveform_morph_duration
        
        if cycle_elapsed >= total_cycle_time:
            # Advance to next shape in sequence
            self.waveform_shape_index = (self.waveform_shape_index + 1) % len(self.waveform_shape_sequence)
            next_shape = self.waveform_shape_sequence[self.waveform_shape_index]
            
            # Start morphing to new shape
            self.waveform_morph_mode = next_shape
            self.waveform_morph_start_time = current_time
            self.waveform_shape_cycle_time = current_time
            self.waveform_morph_progress = 0.0
            
            print(f"Waveform morphing to: {next_shape}")
        
        # Update morph progress during transition
        if cycle_elapsed < self.waveform_morph_duration:
            # Currently morphing
            self.waveform_morph_progress = cycle_elapsed / self.waveform_morph_duration
            # Smooth easing function
            self.waveform_morph_progress = self._ease_in_out_cubic(self.waveform_morph_progress)
        else:
            # Holding current shape
            self.waveform_morph_progress = 1.0
    
    def _ease_in_out_cubic(self, t: float) -> float:
        """Smooth easing function for morphing transitions"""
        return 3 * t * t - 2 * t * t * t
    
    def _calculate_morph_offset(self, point_index: int, total_points: int, center_x: float, center_y: float, x: float, y: float) -> float:
        """Calculate offset to morph waveform into instrument shapes"""
        if self.waveform_morph_progress == 0.0:
            return 0.0  # No morphing
        
        # Get the shape offset based on current morph mode
        if self.waveform_morph_mode == 'guitar':
            offset = self._get_guitar_shape_offset(point_index, total_points, center_x, center_y, x, y)
        elif self.waveform_morph_mode == 'drums':
            offset = self._get_drum_shape_offset(point_index, total_points, center_x, center_y, x, y)
        elif self.waveform_morph_mode == 'microphone':
            offset = self._get_microphone_shape_offset(point_index, total_points, center_x, center_y, x, y)
        elif self.waveform_morph_mode == 'keyboard':
            offset = self._get_keyboard_shape_offset(point_index, total_points, center_x, center_y, x, y)
        elif self.waveform_morph_mode == 'violin':
            offset = self._get_violin_shape_offset(point_index, total_points, center_x, center_y, x, y)
        elif self.waveform_morph_mode == 'saxophone':
            offset = self._get_saxophone_shape_offset(point_index, total_points, center_x, center_y, x, y)
        elif self.waveform_morph_mode == 'star':
            offset = self._get_star_shape_offset(point_index, total_points, center_x, center_y, x, y)
        elif self.waveform_morph_mode == 'heart':
            offset = self._get_heart_shape_offset(point_index, total_points, center_x, center_y, x, y)
        elif self.waveform_morph_mode == 'spiral':
            offset = self._get_spiral_shape_offset(point_index, total_points, center_x, center_y, x, y)
        else:
            offset = 0.0  # Normal waveform
        
        # Apply morph progress for smooth transition
        return offset * self.waveform_morph_progress
    
    def _get_guitar_shape_offset(self, point_index: int, total_points: int, center_x: float, center_y: float, x: float, y: float) -> float:
        """Calculate offset to create guitar silhouette"""
        # Normalize position (0.0 to 1.0)
        pos = point_index / total_points
        
        # Guitar body sections
        if pos < 0.2:  # Headstock
            body_width = 0.1 + (pos / 0.2) * 0.15  # Narrow headstock
        elif pos < 0.4:  # Neck
            body_width = 0.08  # Thin neck
        elif pos < 0.7:  # Upper bout
            progress = (pos - 0.4) / 0.3
            body_width = 0.08 + progress * 0.35  # Widening to body
        else:  # Lower bout
            progress = (pos - 0.7) / 0.3
            body_width = 0.43 - progress * 0.15  # Guitar body curve
        
        # Create guitar outline
        scale = self.height * 0.3  # Guitar size
        target_y = center_y + math.sin(pos * math.pi) * body_width * scale
        
        # Add some curvature for realism
        if pos > 0.4:  # Body area
            curve = math.sin((pos - 0.4) * math.pi / 0.6) * 0.8
            target_y += curve * scale * 0.1
        
        return (target_y - y) * 0.7  # 70% morph strength
    
    def _get_drum_shape_offset(self, point_index: int, total_points: int, center_x: float, center_y: float, x: float, y: float) -> float:
        """Calculate offset to create drum kit silhouette"""
        pos = point_index / total_points
        
        # Drum kit sections
        if pos < 0.15:  # Hi-hat
            drum_height = 0.4 + math.sin(pos * 20) * 0.1
        elif pos < 0.35:  # Crash cymbal
            drum_height = 0.5 + math.sin((pos - 0.15) * 15) * 0.15
        elif pos < 0.55:  # Toms
            tom_pos = (pos - 0.35) / 0.2
            drum_height = 0.3 - tom_pos * 0.1 + math.sin(tom_pos * math.pi * 3) * 0.2
        elif pos < 0.75:  # Snare and kick
            drum_height = 0.1 + math.sin((pos - 0.55) * math.pi / 0.2) * 0.4
        else:  # Floor tom and ride cymbal
            drum_height = 0.25 + math.sin((pos - 0.75) * 12) * 0.2
        
        scale = self.height * 0.25
        target_y = center_y - drum_height * scale
        
        # Add kick drum emphasis
        if 0.55 < pos < 0.65:
            kick_emphasis = math.sin((pos - 0.55) * math.pi / 0.1) * 0.3
            target_y -= kick_emphasis * scale
        
        return (target_y - y) * 0.8  # 80% morph strength
    
    def _get_microphone_shape_offset(self, point_index: int, total_points: int, center_x: float, center_y: float, x: float, y: float) -> float:
        """Calculate offset to create microphone silhouette"""
        pos = point_index / total_points
        
        # Microphone sections
        if pos < 0.3:  # Base/stand
            mic_width = 0.05 + (0.3 - pos) * 0.15  # Wider base
        elif pos < 0.7:  # Stand pole
            mic_width = 0.02  # Thin pole
        elif pos < 0.85:  # Microphone body
            body_pos = (pos - 0.7) / 0.15
            mic_width = 0.02 + body_pos * 0.25  # Expanding to mic head
        else:  # Microphone head
            head_pos = (pos - 0.85) / 0.15
            mic_width = 0.27 - head_pos * 0.05  # Slightly tapered head
        
        # Add microphone grille texture
        if pos > 0.75:
            grille_pattern = math.sin((pos - 0.75) * 50) * 0.03
            mic_width += grille_pattern
        
        scale = self.height * 0.35
        target_y = center_y + math.sin(pos * math.pi) * mic_width * scale
        
        return (target_y - y) * 0.9  # 90% morph strength
    
    def _get_keyboard_shape_offset(self, point_index: int, total_points: int, center_x: float, center_y: float, x: float, y: float) -> float:
        """Calculate offset to create keyboard/piano silhouette"""
        pos = point_index / total_points
        
        # Keyboard sections
        if pos < 0.1 or pos > 0.9:  # Side panels
            key_height = 0.15
        else:  # Main keyboard area with keys
            key_pos = (pos - 0.1) / 0.8
            # Create white and black key pattern
            key_pattern = int(key_pos * 28) % 7  # 28 keys, 7-key pattern
            if key_pattern in [1, 2, 4, 5, 6]:  # Black key positions
                key_height = 0.25 + math.sin(key_pos * 28 * math.pi) * 0.05
            else:  # White keys
                key_height = 0.18 + math.sin(key_pos * 28 * math.pi) * 0.03
        
        scale = self.height * 0.3
        target_y = center_y + math.sin(pos * math.pi) * key_height * scale
        
        return (target_y - y) * 0.85  # 85% morph strength
    
    def _get_violin_shape_offset(self, point_index: int, total_points: int, center_x: float, center_y: float, x: float, y: float) -> float:
        """Calculate offset to create violin silhouette"""
        pos = point_index / total_points
        
        # Violin body shape with curves
        if pos < 0.2:  # Bottom bout
            violin_width = 0.15 + pos * 0.15
        elif pos < 0.4:  # Waist (narrow part)
            waist_pos = (pos - 0.2) / 0.2
            violin_width = 0.30 - waist_pos * 0.18  # Narrow waist
        elif pos < 0.6:  # Upper bout
            bout_pos = (pos - 0.4) / 0.2
            violin_width = 0.12 + bout_pos * 0.15
        elif pos < 0.85:  # Neck
            violin_width = 0.08
        else:  # Scroll/head
            head_pos = (pos - 0.85) / 0.15
            violin_width = 0.08 + head_pos * 0.05 * math.sin(head_pos * math.pi * 3)
        
        # Add f-holes detail
        if 0.25 < pos < 0.55:
            f_hole = math.sin((pos - 0.25) * 15) * 0.02
            violin_width += f_hole
        
        scale = self.height * 0.35
        target_y = center_y + math.sin(pos * math.pi) * violin_width * scale
        
        return (target_y - y) * 0.88  # 88% morph strength
    
    def _get_saxophone_shape_offset(self, point_index: int, total_points: int, center_x: float, center_y: float, x: float, y: float) -> float:
        """Calculate offset to create saxophone silhouette"""
        pos = point_index / total_points
        
        # Saxophone curve - characteristic S-shape
        if pos < 0.3:  # Bell (wide end)
            bell_pos = pos / 0.3
            sax_width = 0.25 + bell_pos * 0.15 + math.sin(bell_pos * math.pi * 2) * 0.05
        elif pos < 0.6:  # Body tube (curved)
            body_pos = (pos - 0.3) / 0.3
            curve_factor = math.sin(body_pos * math.pi) * 0.3
            sax_width = 0.18 + curve_factor
        elif pos < 0.8:  # Neck
            sax_width = 0.12
        else:  # Mouthpiece
            mouth_pos = (pos - 0.8) / 0.2
            sax_width = 0.12 - mouth_pos * 0.08
        
        # Add key details
        if 0.2 < pos < 0.7:
            key_pattern = math.sin(pos * 30) * 0.02
            sax_width += key_pattern
        
        scale = self.height * 0.32
        # Create characteristic sax curve
        curve_offset = math.sin(pos * math.pi) * 0.2 * math.cos(pos * math.pi * 1.5)
        target_y = center_y + (math.sin(pos * math.pi) * sax_width + curve_offset) * scale
        
        return (target_y - y) * 0.83  # 83% morph strength
    
    def _get_star_shape_offset(self, point_index: int, total_points: int, center_x: float, center_y: float, x: float, y: float) -> float:
        """Calculate offset to create star shape"""
        pos = point_index / total_points
        
        # 5-pointed star
        angle = pos * math.pi * 2
        # Create star points using modulo
        star_angle = angle * 2.5  # 5 points
        radius_base = 0.25
        
        # Alternate between outer points and inner valleys
        point_phase = math.cos(star_angle)
        if point_phase > 0:  # Outer points
            star_radius = radius_base + point_phase * 0.15
        else:  # Inner valleys
            star_radius = radius_base + point_phase * 0.08
        
        # Add sparkle effect
        sparkle = math.sin(angle * 15 + time.time() * 8) * 0.03
        star_radius += sparkle
        
        scale = self.height * 0.3
        target_y = center_y + math.sin(pos * math.pi) * star_radius * scale
        
        return (target_y - y) * 0.9  # 90% morph strength
    
    def _get_heart_shape_offset(self, point_index: int, total_points: int, center_x: float, center_y: float, x: float, y: float) -> float:
        """Calculate offset to create heart shape"""
        pos = point_index / total_points
        
        # Heart shape using parametric equations
        t = pos * math.pi * 2
        # Classic heart shape: x = 16sin³(t), y = 13cos(t) - 5cos(2t) - 2cos(3t) - cos(4t)
        heart_x = math.pow(math.sin(t), 3)
        heart_y = (13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)) / 16
        
        # Add gentle pulsing
        pulse = 1.0 + math.sin(time.time() * 3) * 0.1
        heart_radius = abs(heart_y) * 0.2 * pulse
        
        scale = self.height * 0.25
        target_y = center_y + math.sin(pos * math.pi) * heart_radius * scale
        
        return (target_y - y) * 0.85  # 85% morph strength
    
    def _get_spiral_shape_offset(self, point_index: int, total_points: int, center_x: float, center_y: float, x: float, y: float) -> float:
        """Calculate offset to create spiral shape"""
        pos = point_index / total_points
        
        # Logarithmic spiral
        spiral_turns = 3.0  # Number of spiral turns
        angle = pos * spiral_turns * math.pi * 2
        # Spiral radius grows/shrinks with position
        spiral_radius = 0.1 + pos * 0.25 + math.sin(angle) * 0.05
        
        # Add rotation over time for dynamic effect
        time_rotation = time.time() * 0.5
        final_angle = angle + time_rotation
        
        scale = self.height * 0.28
        target_y = center_y + math.sin(pos * math.pi) * spiral_radius * scale * math.cos(final_angle)
        
        return (target_y - y) * 0.8  # 80% morph strength
    
    def _get_waveform_color_variation(self, base_color):
        """Generate color variations based on base color and audio activity"""
        r, g, b = base_color
        
        # Audio-reactive color shifting
        bass_factor = self.freq_bands.get('bass', 0.0)
        mid_factor = self.freq_bands.get('mid', 0.0)
        treble_factor = self.freq_bands.get('treble', 0.0)
        
        # Create much more dramatic color variations
        variation_amount = 80  # Much larger maximum color shift
        
        # More dramatic shifts based on frequency content + time
        r_shift = int(bass_factor * variation_amount * math.sin(time.time() * 3) + 30 * math.cos(time.time() * 1.5))
        g_shift = int(mid_factor * variation_amount * math.sin(time.time() * 4) + 25 * math.sin(time.time() * 2.2))
        b_shift = int(treble_factor * variation_amount * math.sin(time.time() * 5) + 35 * math.cos(time.time() * 2.8))
        
        # Apply shifts with bounds checking
        new_r = max(0, min(255, r + r_shift))
        new_g = max(0, min(255, g + g_shift))
        new_b = max(0, min(255, b + b_shift))
        
        # Add much more frequent and dramatic random variations
        if random.random() < 0.7:  # 70% chance for extra variation (was 30%)
            hue_shift = random.randint(-50, 50)  # Much larger shifts
            new_r = max(0, min(255, new_r + hue_shift))
            new_g = max(0, min(255, new_g + hue_shift))
            new_b = max(0, min(255, new_b + hue_shift))
        
        # Add completely random color bursts occasionally
        if random.random() < 0.2:  # 20% chance for wild color burst
            burst_r = random.randint(0, 255)
            burst_g = random.randint(0, 255)
            burst_b = random.randint(0, 255)
            # Blend with current color
            blend_factor = 0.4
            new_r = int(new_r * (1 - blend_factor) + burst_r * blend_factor)
            new_g = int(new_g * (1 - blend_factor) + burst_g * blend_factor)
            new_b = int(new_b * (1 - blend_factor) + burst_b * blend_factor)
        
        return (new_r, new_g, new_b)
    
    def _get_sparkle_color(self, base_color):
        """Generate bright sparkle colors related to the base color"""
        r, g, b = base_color
        
        # Create brighter, more saturated versions
        sparkle_boost = 0.7  # Increase brightness
        new_r = min(255, int(r + (255 - r) * sparkle_boost))
        new_g = min(255, int(g + (255 - g) * sparkle_boost))
        new_b = min(255, int(b + (255 - b) * sparkle_boost))
        
        # Add much more varied sparkle colors
        if random.random() < 0.6:  # 60% chance for color variations (was 40%)
            if random.random() < 0.5:
                # Complementary colors
                comp_r = 255 - new_r
                comp_g = 255 - new_g
                comp_b = 255 - new_b
                blend = 0.4
                new_r = int(new_r * (1 - blend) + comp_r * blend)
                new_g = int(new_g * (1 - blend) + comp_g * blend)
                new_b = int(new_b * (1 - blend) + comp_b * blend)
            else:
                # Wild random sparkle colors
                wild_r = random.randint(100, 255)
                wild_g = random.randint(100, 255) 
                wild_b = random.randint(100, 255)
                blend = 0.5
                new_r = int(new_r * (1 - blend) + wild_r * blend)
                new_g = int(new_g * (1 - blend) + wild_g * blend)
                new_b = int(new_b * (1 - blend) + wild_b * blend)
        
        return (new_r, new_g, new_b)
    
    def _get_outline_color(self, base_color):
        """Generate darker outline colors for gradient effect"""
        r, g, b = base_color
        
        # Create darker versions for outline/glow effect
        darken_factor = 0.4
        outline_r = int(r * darken_factor)
        outline_g = int(g * darken_factor)
        outline_b = int(b * darken_factor)
        
        # Add subtle color shift for more interesting outline
        if self.beat_detected:
            # More dramatic outline during beats
            outline_r = min(255, outline_r + 30)
            outline_g = min(255, outline_g + 20)
            outline_b = min(255, outline_b + 40)
        
        return (outline_r, outline_g, outline_b)
    
    def _render_smoke_effects(self):
        """Render high-fidelity smoke particle system"""
        if not self.canvas:
            return
            
        try:
            current_time = time.time()
            center_x = self.width // 2
            center_y = self.height // 2
            
            
            # Create new smoke particles based on audio intensity WITH KICK DRUM BURSTS
            bass = self.freq_bands.get('bass', 0.0)
            mid = self.freq_bands.get('mid', 0.0) 
            treble = self.freq_bands.get('treble', 0.0)
            
            # Detect kick drum for particle bursts
            kick_detected = (bass > 0.4 and 
                            bass > mid * 1.3 and 
                            bass > treble and 
                            self.beat_detected)
            
            # PERSISTENT smoke that NEVER disappears but PULSES with bass
            vocal_intensity = mid * 1.5  # Vocals drive smoke intensity
            treble_burst = treble * 1.0  # High frequencies add sparkle to smoke
            bass_pulse = bass * 2.0  # BASS drives dramatic smoke pulsing
            
            # ALWAYS maintain minimum smoke - never fully disappear
            base_smoke_intensity = 0.8  # HIGHER baseline for persistent smoke
            smoke_intensity = base_smoke_intensity + vocal_intensity + treble_burst + bass_pulse
            
             # ALWAYS spawn smoke particles - never stop
            if True:  # Always spawn smoke
                # Enhanced particle spawning for different audio elements with BASS-RESPONSIVE PULSING
                if kick_detected:
                    spawn_rate = int(smoke_intensity * 20) + 15  # BIGGER kick burst (increased)
                    print(f"KICK PARTICLE BURST! Spawning {spawn_rate} particles")
                elif snare_detected:
                    spawn_rate = int(smoke_intensity * 15) + 12   # BIGGER snare burst (increased) 
                    print(f"SNARE PARTICLE BURST! Spawning {spawn_rate} particles")
                elif treble > 0.4:  # High treble creates sparkly smoke
                    spawn_rate = int(smoke_intensity * 12) + 8   # More treble sparkle (increased)
                elif mid > 0.3:  # Vocals create flowing smoke
                    spawn_rate = int(smoke_intensity * 10) + 6    # More vocal smoke flow (increased)
                elif self.beat_detected:
                    spawn_rate = int(smoke_intensity * 8) + 5    # More beat particles (increased)
                else:
                    # ALWAYS maintain baseline particles, but PULSE with bass
                    baseline = 4
                    bass_bonus = int(bass * 8)  # Bass adds 0-8 extra particles
                    spawn_rate = baseline + bass_bonus  # Always at least 4, up to 12 on bass hits
                
                for _ in range(spawn_rate):
                    # Determine particle color - 40% chance for random colors
                    use_random_color = random.random() < 0.4
                    if use_random_color:
                        # Use random vibrant colors
                        particle_color = {
                            'r': random.randint(80, 255),
                            'g': random.randint(80, 255), 
                            'b': random.randint(80, 255)
                        }
                        color_type = 'random'
                    else:
                        # Use song colors (will be determined during rendering)
                        particle_color = None
                        color_type = 'song'
                    
                    # KICK DRUM EXPLOSION EFFECTS - particles scatter dramatically
                    if kick_detected:
                        # EXPLOSIVE SCATTERING from center/bottom on kick hits
                        explosion_center_x = center_x + random.uniform(-self.width * 0.3, self.width * 0.3)
                        explosion_center_y = self.height * 0.8  # Lower on screen for kick
                        
                        # MASSIVE velocity spread for explosion effect
                        explosion_angle = random.uniform(0, math.pi * 2)  # Full 360-degree scatter
                        explosion_speed = random.uniform(80, 200)  # Much faster explosion velocities
                        
                        particle = {
                            'x': explosion_center_x,
                            'y': explosion_center_y,
                            'vx': math.cos(explosion_angle) * explosion_speed,
                            'vy': math.sin(explosion_angle) * explosion_speed - 50,  # Upward bias
                            'life': 1.0,
                            'decay': random.uniform(0.008, 0.015),  # Slower decay for longer effect
                            'size': random.uniform(12, 35),  # Bigger particles for kick
                            'growth': random.uniform(0.8, 1.5),  # Faster growth
                            'birth_time': current_time,
                            'swirl': random.uniform(1.5, 4.0),  # More intense swirl
                            'swirl_phase': random.uniform(0, math.pi * 2),
                            'color': particle_color,
                            'color_type': color_type,
                            'kick_particle': True  # Mark as kick-generated
                        }
                    elif treble > 0.4:
                        # Treble particles - sparkly, fast-rising from bottom
                        particle = {
                            'x': random.uniform(0, self.width),
                            'y': random.uniform(self.height * 0.85, self.height),  # Start near bottom
                            'vx': random.uniform(-20, 20),  # Gentle horizontal drift
                            'vy': random.uniform(-180, -120),  # Fast upward for sparkle effect
                            'life': 1.0,
                            'decay': random.uniform(0.008, 0.015),  # Longer life for sparkle
                            'size': random.uniform(6, 18),  # Smaller, more sparkly
                            'growth': random.uniform(0.2, 0.6),
                            'birth_time': current_time,
                            'swirl': random.uniform(0.3, 1.5),  # Light swirl for sparkle
                            'swirl_phase': random.uniform(0, math.pi * 2),
                            'color': particle_color,
                            'color_type': color_type,
                            'kick_particle': False,
                            'particle_type': 'treble'
                        }
                    elif mid > 0.3:
                        # Vocal particles - smooth, flowing upward
                        particle = {
                            'x': random.uniform(0, self.width),
                            'y': random.uniform(self.height * 0.7, self.height),  # Bottom 30%
                            'vx': random.uniform(-25, 25),  # Gentle sway
                            'vy': random.uniform(-140, -80),  # Smooth upward flow
                            'life': 1.0,
                            'decay': random.uniform(0.006, 0.012),  # Longer life for smooth flow
                            'size': random.uniform(10, 28),  # Medium to large
                            'growth': random.uniform(0.4, 0.9),  # Good growth for visibility
                            'birth_time': current_time,
                            'swirl': random.uniform(1.0, 2.5),  # Smooth swirl for vocals
                            'swirl_phase': random.uniform(0, math.pi * 2),
                            'color': particle_color,
                            'color_type': color_type,
                            'kick_particle': False,
                            'particle_type': 'vocal'
                        }
                    else:
                        # Regular particle behavior - ambient smoke with BASS RESPONSIVENESS
                        # Make ambient particles more responsive to bass
                        bass_velocity_boost = bass * 80  # Bass makes particles rise faster
                        bass_size_boost = bass * 10      # Bass makes particles bigger
                        
                        particle = {
                            'x': random.uniform(0, self.width),
                            'y': random.uniform(self.height * 0.85, self.height),  # Start from bottom
                            'vx': random.uniform(-15, 15),  # Gentle drift
                            'vy': random.uniform(-120 - bass_velocity_boost, -80 - bass_velocity_boost),  # BASS-responsive upward velocity
                            'life': 1.0,
                            'decay': random.uniform(0.008, 0.020),  # Slightly longer life
                            'size': random.uniform(12 + bass_size_boost, 20 + bass_size_boost),  # BASS-responsive size
                            'growth': random.uniform(0.3, 0.7) + (bass * 0.3),  # Bass increases growth rate
                            'birth_time': current_time,
                            'swirl': random.uniform(0.5, 1.8) + (bass * 1.0),  # Bass increases swirl intensity
                            'swirl_phase': random.uniform(0, math.pi * 2),
                            'color': particle_color,
                            'color_type': color_type,
                            'kick_particle': False,
                            'particle_type': 'ambient'
                        }
                    
                    self.smoke_particles.append(particle)
            
            # Render smoke particles with high fidelity
            for particle in self.smoke_particles:
                if particle['life'] > 0:
                    # Create realistic smoke appearance with multiple overlapping circles
                    alpha = particle['life']
                    size = particle['size']
                    
                    # ENHANCED layers for kick particles - more dramatic effect
                    layer_count = 4 if particle.get('kick_particle', False) else 3
                    for layer in range(layer_count):
                        # Kick particles get bigger, more dynamic sizing
                        if particle.get('kick_particle', False):
                            layer_size = size * (0.6 + layer * 0.20)  # Bigger size progression
                            layer_alpha = alpha * (0.9 - layer * 0.15)  # Better alpha progression
                        else:
                            layer_size = size * (0.7 + layer * 0.15)
                            layer_alpha = alpha * (0.8 - layer * 0.2)
                        
                        # Determine particle color based on type
                        if particle['color_type'] == 'random' and particle['color']:
                            # Use the random color assigned to this particle
                            particle_color = particle['color']
                            # Add some variation per layer
                            variation = layer * 20
                            r = max(0, min(255, particle_color['r'] + random.randint(-variation, variation)))
                            g = max(0, min(255, particle_color['g'] + random.randint(-variation, variation)))
                            b = max(0, min(255, particle_color['b'] + random.randint(-variation, variation)))
                            base_color = f"#{r:02x}{g:02x}{b:02x}"
                        else:
                            # Use song colors (alternates between primary and secondary)
                            if layer % 2 == 0 or self.song_secondary_color == 'none':
                                base_color = self._get_pure_song_color(primary=True, intensity=0.6)
                            else:
                                base_color = self._get_pure_song_color(primary=False, intensity=0.6)
                        
                        # Create soft, wispy smoke circles
                        self.canvas.create_oval(
                            particle['x'] - layer_size/2, particle['y'] - layer_size/2,
                            particle['x'] + layer_size/2, particle['y'] + layer_size/2,
                            fill=base_color, outline="", stipple="gray50" if layer > 0 else ""
                        )
            
            # Periodic debug for smoke particles (every 2 seconds for now)
            if hasattr(self, 'last_smoke_debug') and time.time() - self.last_smoke_debug > 2.0:
                print(f"Smoke system: {len(self.smoke_particles)} particles, intensity={self.effects.get('smoke_intensity', 0.8):.2f}, forced_min=0.8")
                self.last_smoke_debug = time.time()
            elif not hasattr(self, 'last_smoke_debug'):
                self.last_smoke_debug = time.time()
                
        except Exception as e:
            # Ignore canvas errors during shutdown
            pass
    
    def _update_smoke_particles(self):
        """Update smoke particle physics for upward animation"""
        current_time = time.time()
        
        for particle in self.smoke_particles[:]:  # Iterate over a copy for safe removal
            # Remove particles that are no longer visible or have expired
            if particle['life'] <= 0 or particle['y'] < 0:
                self.smoke_particles.remove(particle)
                continue
                
            # Update position with realistic physics
            age = current_time - particle['birth_time']
            
            # BASS-ENHANCED swirling motion - bass makes particles swirl like crazy!
            bass_swirl_boost = 1.0 + (self.freq_bands.get('bass', 0.0) * 3.0)  # Up to 4x swirl on bass hits
            enhanced_swirl = particle['swirl'] * bass_swirl_boost
            
            swirl_offset_x = math.sin(age * enhanced_swirl + particle['swirl_phase']) * 15 * bass_swirl_boost
            swirl_offset_y = math.cos(age * enhanced_swirl + particle['swirl_phase']) * 8 * bass_swirl_boost
            
            # Add bass-driven orbital motion around invisible centers
            if self.freq_bands.get('bass', 0.0) > 0.2:  # On bass hits
                orbital_radius = 25 * self.freq_bands.get('bass', 0.0)
                orbital_speed = age * 2 + particle['swirl_phase']
                orbit_x = math.cos(orbital_speed) * orbital_radius
                orbit_y = math.sin(orbital_speed) * orbital_radius * 0.5  # Elliptical orbit
                swirl_offset_x += orbit_x * 0.5
                swirl_offset_y += orbit_y * 0.5
            
            particle['x'] += particle['vx'] * 0.016 + swirl_offset_x * 0.016
            particle['y'] += particle['vy'] * 0.016 + swirl_offset_y * 0.016
            
            # ENHANCED physics for kick particles vs regular particles
            if particle.get('kick_particle', False):
                # Kick particles have different physics - more explosive, less buoyancy initially
                particle['vx'] *= 0.95  # More air resistance for dramatic slowdown
                particle['vy'] *= 0.99   # More drag
                particle['vy'] -= 5.0   # Less initial buoyancy (they rely on explosion velocity)
                
                # MASSIVE bass-reactive movement - particles dance to the bass!
                bass_pulse = self.freq_bands.get('bass', 0.0) * 150  # Much stronger bass effect!
                particle['vx'] += bass_pulse * 0.08 * math.sin(age * 6)  # 4x stronger pulsing motion
                particle['vy'] += bass_pulse * 0.04 * math.cos(age * 4)  # 4x stronger bass-reactive movement
                
                # Add chaotic bass-driven velocity spikes
                if self.freq_bands.get('bass', 0.0) > 0.3:  # On strong bass hits
                    chaos_x = random.uniform(-80, 80) * self.freq_bands.get('bass', 0.0)
                    chaos_y = random.uniform(-60, 60) * self.freq_bands.get('bass', 0.0)
                    particle['vx'] += chaos_x * 0.01
                    particle['vy'] += chaos_y * 0.01
            else:
                # ENHANCED regular particle physics with bass reactivity
                particle['vx'] *= 0.98  # Air resistance
                particle['vy'] *= 0.997  # Slight drag
                particle['vy'] -= 8.0  # Increased buoyancy to ensure particles reach the top
                
                # Regular particles also react to bass, just less dramatically
                bass_effect = self.freq_bands.get('bass', 0.0) * 80
                particle['vx'] += bass_effect * 0.03 * math.sin(age * 4)  # Bass-reactive wiggle
                particle['vy'] += bass_effect * 0.02 * math.cos(age * 3)  # Bass bounce effect
            
            # MASSIVE bass-driven wind effects - particles get blown around by bass hits!
            bass_wind = self.freq_bands.get('bass', 0.0) * 120  # Strong bass wind effect
            mid_wind = self.freq_bands.get('mid', 0.0) * 60     # Moderate mid-range wind
            treble_wind = self.freq_bands.get('treble', 0.0) * 40  # Light treble wind
            
            # Kick particles get hit by massive bass wind storms
            if particle.get('kick_particle', False):
                wind_multiplier = 4.0  # 4x stronger wind for kick particles
                # Multi-directional bass wind - creates swirling chaos
                bass_angle = age * 3 + particle['swirl_phase']
                wind_x = math.cos(bass_angle) * bass_wind * wind_multiplier * 0.025
                wind_y = math.sin(bass_angle) * bass_wind * wind_multiplier * 0.015
                particle['vx'] += wind_x
                particle['vy'] += wind_y
                
                # Additional chaotic mid/treble effects
                particle['vx'] += (mid_wind + treble_wind) * wind_multiplier * 0.02
            else:
                # Regular particles get moderate bass wind effects
                wind_multiplier = 2.0
                # Gentler but still noticeable bass wind for regular particles
                bass_angle = age * 2 + particle['swirl_phase']
                wind_x = math.cos(bass_angle) * bass_wind * 0.02
                wind_y = math.sin(bass_angle) * bass_wind * 0.01
                particle['vx'] += wind_x
                particle['vy'] += wind_y
                
                # Mid-range creates horizontal drift
                particle['vx'] += mid_wind * 0.025
            
            # Update particle properties
            particle['life'] -= particle['decay']
            
            # Kick particles grow faster and pulse with bass
            if particle.get('kick_particle', False):
                bass_growth_boost = self.freq_bands.get('bass', 0.0) * 0.5
                particle['size'] += (particle['growth'] + bass_growth_boost) * 0.016
            else:
                particle['size'] += particle['growth'] * 0.016
     
    def _get_pure_song_color(self, primary: bool = True, intensity: float = 1.0) -> str:
        """Get pure primary or secondary song color without blending"""
        color_name = self.song_primary_color if primary else self.song_secondary_color
        
        # Handle auto/none cases silently - use dynamic colors when no song colors set
        if (self.song_primary_color == 'auto' or not self.song_primary_color) and (self.song_secondary_color == 'none' or not self.song_secondary_color):
            # Use dynamic rainbow colors when no song colors configured
            return self._get_dynamic_song_color(0.5, intensity)
        
        if color_name == 'auto' or color_name == 'none' or not color_name:
            # Fallback to dynamic colors without debug spam
            return self._get_dynamic_song_color(0.5, intensity)
        
        color_hues = {
            'red': 0.0, 'orange': 0.08, 'yellow': 0.16, 'green': 0.33,
            'blue': 0.66, 'purple': 0.83, 'pink': 0.91, 'white': 0.0
        }
        
        if color_name in color_hues:
            hue = color_hues[color_name]
            if color_name == 'white':
                return f"#{int(255 * intensity):02x}{int(255 * intensity):02x}{int(255 * intensity):02x}"
            
            import colorsys
            r, g, b = colorsys.hsv_to_rgb(hue, 0.8, intensity)
            return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
        
        # Fallback if unknown color
        return "#ffffff"
     
    def _get_dynamic_song_color(self, hue_offset: float, intensity: float) -> str:
        """Generate dynamic color based on audio with enhanced visual appeal"""
        # Create color cycling based on time and audio
        base_hue = (time.time() * 0.1 + hue_offset) % 1.0
        
        # Add audio-reactive color variation
        bass_hue_shift = self.freq_bands.get('bass', 0.0) * 0.3
        mid_hue_shift = self.freq_bands.get('mid', 0.0) * 0.2
        treble_hue_shift = self.freq_bands.get('treble', 0.0) * 0.25
        
        # Combine base hue with audio-reactive shifts
        final_hue = (base_hue + bass_hue_shift + mid_hue_shift + treble_hue_shift) % 1.0
        
        # Use higher saturation and intensity for more vivid colors
        saturation = 0.9  # Higher saturation for vibrant colors
        value = min(1.0, 0.8 + intensity * 0.2)  # Ensure good brightness
        
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(final_hue, saturation, value)
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
    
    def cleanup(self):
        """Clean up waveform resources"""
        self.smoke_particles = []
        self.waveform_rotation_active = False