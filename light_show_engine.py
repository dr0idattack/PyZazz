import time
import random
import math
from typing import Dict, List, Optional, Tuple
from color_engine import ColorEngine

class LightShowEngine:
    """Classic rock-style lighting engine with dramatic, impactful effects."""
    
    def __init__(self, color_engine: ColorEngine):
        self.color_engine = color_engine
        self.light_groups = {'wash': [], 'par': [], 'accent': []}
        
        # State variables
        self.current_effect = "darkness"
        self.effect_start_time = 0
        self.effect_duration = 8.0  # Much shorter duration for more variety
        
        self.current_states = {}  # Combined state for color and intensity
        self.target_states = {}
        
        self.fade_speeds = {
            'slow': 0.70,     # Slow, smooth transitions (70% per frame)
            'medium': 0.85,   # Medium fade (85% per frame) 
            'fast': 0.95,     # Fast but not instant transitions (95% per frame)
            'instant': 1.0,   # Instant for strobes
            'wash_smooth': 0.60  # Extra smooth transitions specifically for wash lights
        }
        self.current_fade_speed = 'medium'  # Default to medium for calmer color transitions
        
        # Maximum step sizes per frame for smooth increments
        self.max_step_sizes = {
            'slow': 8,        # Max 8 units per frame for very smooth ramps
            'medium': 15,     # Max 15 units per frame for moderate changes
            'fast': 30,       # Max 30 units per frame for faster changes
            'instant': 255,   # No limit for instant changes
            'wash_smooth': 6  # Max 6 units per frame for ultra-smooth wash transitions
        }
        
        self.show_phase = 'intro'
        self.phase_start_time = 0
        self.last_beat_time = 0
        self.strobe_active = False
        
        # Beat pulsing system - alternating on/off for PARs and washes
        self.beat_count = 0
        self.beat_pulse_active = False
        self.beat_pulse_duration = 0.15  # How long each beat flash lasts (150ms - longer for visibility)
        self.last_beat_pulse_time = 0
        
        # Beat-synchronized strobe system
        self.beat_strobe_active = False
        self.beat_strobe_duration = 0.15  # How long each beat strobe lasts (150ms)

        self.effects = {
            'darkness': self._effect_darkness,
            'static_scene': self._effect_static_scene,
            'par_impact': self._effect_par_impact,
            'wash_pulse': self._effect_wash_pulse,
            'color_chase': self._effect_color_chase,
            'full_on': self._effect_full_on,
            'gentle_fade_in': self._effect_gentle_fade_in,
            'slow_color_build': self._effect_slow_color_build,
            'gentle_ambient': self._effect_gentle_ambient,
            'soft_pulse': self._effect_soft_pulse,
        }
        
        # Flag to control whether light show engine is active
        self.engine_active = False
        
        # Frequency change detection for dynamic color changes
        self.previous_freq_bands = {'bass': 0, 'mid': 0, 'treble': 0}
        self.last_freq_change_time = 0
        self.freq_change_threshold = 0.3  # 30% change triggers color change
        
        # PAR color cycling when treble is low
        self.par_color_cycle_time = 0
        self.par_cycle_duration = 4.0  # Much slower cycling - every 4 seconds
        self.par_use_secondary = False  # Track which color to use
        
        # Wash light color cycling for alternation
        self.wash_color_cycle_time = 0
        self.wash_cycle_duration = 3.0  # Wash color alternation every 3 seconds
        self.wash_use_secondary = False  # Track which wash color to use
        
        # PAR slow fade system for "easy" reactive mode
        self.par_fade_states = {}  # Track individual PAR fade states
        self.par_fade_beat_count = 0  # Track beats for alternating pattern
        self.par_fade_last_beat_time = 0  # Track timing for fade transitions
        self.par_fade_skip_next_beat = False  # Skip every other beat pattern
        
        # 5-minute slow cycle system
        self.show_start_time = 0  # Track when show started for intro effects
        self.last_status_log = 0  # For periodic status logging
        self.slow_cycle_mode = False  # Track if we're in 5-minute slow cycle mode
        self.slow_cycle_start_time = 0  # When slow cycle mode started
    
    def _get_random_color_assignment(self, music_info: dict) -> dict:
        """Get stable color assignment for PAR and wash lights"""
        # Use the frame color that was pre-determined for consistency
        frame_color = music_info.get('frame_color', {'r': 255, 'g': 255, 'b': 255})
        
        # Use stable strategy - heavily favor consistent color assignment
        strategy = random.choices(
            ['all_same', 'group_different', 'individual_random', 'paired_random'],
            weights=[70, 20, 5, 5]  # 70% all same, 20% group different, 5% each random
        )[0]
        
        # Log color strategy occasionally for debugging
        if random.random() < 0.1:  # 10% chance to log
            print(f"COLOR STRATEGY: {strategy}")
        
        colors = {}
        
        if strategy == 'all_same':
            # All lights same color - use the consistent frame color
            colors['wash'] = [frame_color] * len(self.light_groups.get('wash', []))
            colors['par'] = [frame_color] * len(self.light_groups.get('par', []))
            
        elif strategy == 'group_different':
            # Wash group one color, PAR group another color - use complementary colors
            # Generate a complementary color from the frame color
            complement_color = {
                'r': 255 - frame_color['r'],
                'g': 255 - frame_color['g'], 
                'b': 255 - frame_color['b']
            }
            colors['wash'] = [frame_color] * len(self.light_groups.get('wash', []))
            colors['par'] = [complement_color] * len(self.light_groups.get('par', []))
            
        elif strategy == 'individual_random':
            # Each light gets its own random color - but from a limited palette for consistency
            # Create variations of the frame color
            variations = [frame_color]
            for i in range(3):
                variations.append({
                    'r': max(0, min(255, frame_color['r'] + random.randint(-50, 50))),
                    'g': max(0, min(255, frame_color['g'] + random.randint(-50, 50))),
                    'b': max(0, min(255, frame_color['b'] + random.randint(-50, 50)))
                })
            
            colors['wash'] = [variations[i % len(variations)] for i in range(len(self.light_groups.get('wash', [])))]
            colors['par'] = [variations[i % len(variations)] for i in range(len(self.light_groups.get('par', [])))]
            
        elif strategy == 'paired_random':
            # Random pairing: some PARs and washes match, others are different
            num_wash = len(self.light_groups.get('wash', []))
            num_par = len(self.light_groups.get('par', []))
            
            # Create a small palette based on frame color
            palette = [frame_color]
            palette.append({  # Brighter version
                'r': min(255, int(frame_color['r'] * 1.3)),
                'g': min(255, int(frame_color['g'] * 1.3)),
                'b': min(255, int(frame_color['b'] * 1.3))
            })
            palette.append({  # Dimmer version  
                'r': int(frame_color['r'] * 0.7),
                'g': int(frame_color['g'] * 0.7),
                'b': int(frame_color['b'] * 0.7)
            })
            
            colors['wash'] = []
            colors['par'] = []
            
            # Assign wash colors
            for i in range(num_wash):
                colors['wash'].append(palette[i % len(palette)])
            
            # Assign PAR colors with some matching wash colors
            for i in range(num_par):
                if random.random() < 0.4 and colors['wash']:
                    # 40% chance to match a wash color
                    colors['par'].append(random.choice(colors['wash']))
                else:
                    colors['par'].append(palette[i % len(palette)])
        
        return colors
    
    def _get_par_color_for_low_treble(self, music_info: dict, par_index: int) -> dict:
        """Get alternating primary/secondary colors for PARs when treble is low"""
        current_time = time.time()

        # Reactivity-aware color cycling
        current_song = music_info.get('song_config', {})
        reactivity_mode = current_song.get('reactivity_mode', 'medium')
        
        # Adjust cycling speed based on reactivity mode
        cycle_duration = self.par_cycle_duration
        if reactivity_mode == 'easy':
            cycle_duration = 2.5  # 2.5 seconds for easy mode - much calmer
        elif reactivity_mode == 'medium':
            cycle_duration = 2.2  # 2.2 seconds for medium mode - more responsive than default
        elif reactivity_mode == 'very_reactive':
            cycle_duration = 2.0  # 2.0 seconds for very reactive mode - fastest alternation

        # Update color cycling timer
        if current_time - self.par_color_cycle_time > cycle_duration:
            self.par_use_secondary = not self.par_use_secondary
            self.par_color_cycle_time = current_time
            # Only log color switches occasionally
            if random.random() < 0.3:  # 30% chance
                print(f"PAR color switch: {'secondary' if self.par_use_secondary else 'primary'}")
        
        # Get song colors
        song_color = music_info.get('song_color')
        secondary_color = music_info.get('song_secondary_color')
        
        # Alternate between primary and secondary colors, with each PAR getting opposite color
        use_secondary_for_this_par = self.par_use_secondary
        if par_index % 2 == 1:  # Odd indexed PARs get opposite color
            use_secondary_for_this_par = not use_secondary_for_this_par
        
        if secondary_color and secondary_color != 'none' and use_secondary_for_this_par:
            from color_engine import ColorEngine
            temp_engine = ColorEngine()
            color_tuple = temp_engine._color_name_to_rgb(secondary_color)
            return {'r': color_tuple[0], 'g': color_tuple[1], 'b': color_tuple[2]}
        elif song_color and song_color != 'auto':
            from color_engine import ColorEngine
            temp_engine = ColorEngine()
            color_tuple = temp_engine._color_name_to_rgb(song_color)
            return {'r': color_tuple[0], 'g': color_tuple[1], 'b': color_tuple[2]}
        else:
            # Fallback to frame color
            return music_info.get('frame_color', {'r': 255, 'g': 255, 'b': 255})
    
    def _get_wash_color_for_alternation(self, music_info: dict, wash_index: int) -> dict:
        """Get alternating primary/secondary colors for wash lights"""
        current_time = time.time()

        # Reactivity-aware color cycling for wash lights
        current_song = music_info.get('song_config', {})
        reactivity_mode = current_song.get('reactivity_mode', 'medium')
        
        # Adjust cycling speed based on reactivity mode
        cycle_duration = self.wash_cycle_duration
        if reactivity_mode == 'easy':
            cycle_duration = 2.5  # 2.5 seconds for easy mode - more frequent color changes
        elif reactivity_mode == 'medium':
            cycle_duration = 2.2  # 2.2 seconds for medium mode - more responsive than default
        elif reactivity_mode == 'very_reactive':
            cycle_duration = 2.0  # 2 seconds for very reactive mode - most dynamic

        # Update wash color cycling timer
        if current_time - self.wash_color_cycle_time > cycle_duration:
            self.wash_use_secondary = not self.wash_use_secondary
            self.wash_color_cycle_time = current_time
            # Only log color switches occasionally
            if random.random() < 0.3:  # 30% chance
                print(f"Wash color switch: {'secondary' if self.wash_use_secondary else 'primary'}")
        
        # Get song colors
        song_color = music_info.get('song_color')
        secondary_color = music_info.get('song_secondary_color')
        
        # Alternate between primary and secondary colors, with each wash getting opposite color
        use_secondary_for_this_wash = self.wash_use_secondary
        if wash_index % 2 == 1:  # Odd indexed washes get opposite color
            use_secondary_for_this_wash = not use_secondary_for_this_wash
        
        if secondary_color and secondary_color != 'none' and use_secondary_for_this_wash:
            from color_engine import ColorEngine
            temp_engine = ColorEngine()
            color_tuple = temp_engine._color_name_to_rgb(secondary_color)
            return {'r': color_tuple[0], 'g': color_tuple[1], 'b': color_tuple[2]}
        elif song_color and song_color != 'auto':
            from color_engine import ColorEngine
            temp_engine = ColorEngine()
            color_tuple = temp_engine._color_name_to_rgb(song_color)
            return {'r': color_tuple[0], 'g': color_tuple[1], 'b': color_tuple[2]}
        else:
            # Fallback to frame color
            return music_info.get('frame_color', {'r': 255, 'g': 255, 'b': 255})
    
    def _detect_frequency_change(self, music_info: dict) -> bool:
        """Detect significant changes in frequency spectrum to trigger color changes"""
        current_time = time.time()
        freq_bands = music_info.get('frequency_bands', {})
        
        if not freq_bands:
            return False
            
        # Don't check too frequently
        if current_time - self.last_freq_change_time < 2.0:
            return False
            
        current_bass = freq_bands.get('bass', 0)
        current_mid = freq_bands.get('mid', 0)
        current_treble = freq_bands.get('treble', 0)
        
        # Calculate changes from previous readings
        bass_change = abs(current_bass - self.previous_freq_bands['bass'])
        mid_change = abs(current_mid - self.previous_freq_bands['mid'])
        treble_change = abs(current_treble - self.previous_freq_bands['treble'])
        
        # Check if any frequency band had a significant change
        freq_changed = (bass_change > self.freq_change_threshold or 
                       mid_change > self.freq_change_threshold or
                       treble_change > self.freq_change_threshold)
        
        # Update previous readings
        self.previous_freq_bands = {
            'bass': current_bass,
            'mid': current_mid,
            'treble': current_treble
        }
        
        if freq_changed:
            self.last_freq_change_time = current_time
            dominant_freq = "bass" if bass_change > mid_change and bass_change > treble_change else \
                          "treble" if treble_change > mid_change else "mid"
            print(f"FREQUENCY CHANGE DETECTED! {dominant_freq.upper()} shifted by {max(bass_change, mid_change, treble_change):.3f} - triggering color change")
            
        return freq_changed
    
    def _update_par_fade_system(self, beat_detected: bool, music_info: dict = None):
        """Update PAR fade system for easy/medium/very_reactive modes"""
        current_time = time.time()
        
        # Get reactivity mode to determine pattern
        current_song = music_info.get('song_config', {}) if music_info else {}
        reactivity_mode = current_song.get('reactivity_mode', 'medium')
        
        if beat_detected:
            self.par_fade_beat_count += 1
            self.par_fade_last_beat_time = current_time
            
            # Initialize PAR states if needed
            for i, light_id in enumerate(self.light_groups['par']):
                if light_id not in self.par_fade_states:
                    self.par_fade_states[light_id] = {
                        'phase': 'off',  # 'off', 'fading_on', 'on', 'fading_off'
                        'fade_start_time': 0,
                        'target_intensity': 0,
                        'current_intensity': 0,
                        'par_index': i  # Track which PAR this is (0, 1, 2, etc.)
                    }
            
            # Different patterns based on reactivity mode
            if reactivity_mode == 'easy':
                self._apply_easy_fade_pattern(current_time)
            elif reactivity_mode == 'medium':
                self._apply_medium_fade_pattern(current_time)
            elif reactivity_mode == 'very_reactive':
                self._apply_very_reactive_fade_pattern(current_time)
                
    def _apply_easy_fade_pattern(self, current_time):
        """Easy mode: 12-beat sequence with long fades"""
        # Beat 1: Both PARs fade on
        # Beat 3: PAR 0 fades off
        # Beat 5: PAR 0 fades on
        # Beat 7: PAR 1 fades off  
        # Beat 9: PAR 1 fades on
        # Beat 11: Both PARs fade off
        # Beat 13: Sequence repeats (both fade on)
        
        beat_in_sequence = ((self.par_fade_beat_count - 1) % 12) + 1  # 1-12 cycle
        
        for light_id in self.light_groups['par']:
            par_state = self.par_fade_states[light_id]
            # Ensure par_index exists (backward compatibility)
            if 'par_index' not in par_state:
                par_state['par_index'] = list(self.light_groups['par']).index(light_id)
            par_index = par_state['par_index']
            
            if beat_in_sequence == 1:  # Beat 1: Both PARs start fading on
                par_state['phase'] = 'fading_on'
                par_state['fade_start_time'] = current_time
            elif beat_in_sequence == 3 and par_index == 0:  # Beat 3: PAR 0 fades off
                par_state['phase'] = 'fading_off'
                par_state['fade_start_time'] = current_time
            elif beat_in_sequence == 5 and par_index == 0:  # Beat 5: PAR 0 fades on
                par_state['phase'] = 'fading_on'
                par_state['fade_start_time'] = current_time
            elif beat_in_sequence == 7 and par_index == 1:  # Beat 7: PAR 1 fades off
                par_state['phase'] = 'fading_off'
                par_state['fade_start_time'] = current_time
            elif beat_in_sequence == 9 and par_index == 1:  # Beat 9: PAR 1 fades on
                par_state['phase'] = 'fading_on'
                par_state['fade_start_time'] = current_time
            elif beat_in_sequence == 11:  # Beat 11: Both PARs fade off
                par_state['phase'] = 'fading_off'
                par_state['fade_start_time'] = current_time
                
        # Reduced logging - only log occasionally
        if random.random() < 0.1:  # 10% chance
            print(f"PAR Easy fade: beat #{self.par_fade_beat_count}")
        
    def _apply_medium_fade_pattern(self, current_time):
        """Medium mode: 6-beat sequence with more frequent blinking"""
        # Beat 1: Both PARs fade on
        # Beat 2: PAR 0 fades off  
        # Beat 3: PAR 1 fades off
        # Beat 4: Both PARs fade on
        # Beat 5: PAR 0 fades off
        # Beat 6: PAR 1 fades off
        # Beat 7: Sequence repeats (more frequent cycling)
        
        beat_in_sequence = ((self.par_fade_beat_count - 1) % 6) + 1  # 1-6 cycle
        
        for light_id in self.light_groups['par']:
            par_state = self.par_fade_states[light_id]
            if 'par_index' not in par_state:
                par_state['par_index'] = list(self.light_groups['par']).index(light_id)
            par_index = par_state['par_index']
            
            if beat_in_sequence == 1:  # Beat 1: Both PARs fade on
                par_state['phase'] = 'fading_on'
                par_state['fade_start_time'] = current_time
            elif beat_in_sequence == 2 and par_index == 0:  # Beat 2: PAR 0 fades off
                par_state['phase'] = 'fading_off'
                par_state['fade_start_time'] = current_time
            elif beat_in_sequence == 3 and par_index == 1:  # Beat 3: PAR 1 fades off
                par_state['phase'] = 'fading_off'
                par_state['fade_start_time'] = current_time
            elif beat_in_sequence == 4:  # Beat 4: Both PARs fade on
                par_state['phase'] = 'fading_on'
                par_state['fade_start_time'] = current_time
            elif beat_in_sequence == 5 and par_index == 0:  # Beat 5: PAR 0 fades off
                par_state['phase'] = 'fading_off'
                par_state['fade_start_time'] = current_time
            elif beat_in_sequence == 6 and par_index == 1:  # Beat 6: PAR 1 fades off
                par_state['phase'] = 'fading_off'
                par_state['fade_start_time'] = current_time
                
        # Reduced logging - only log occasionally
        if random.random() < 0.1:  # 10% chance
            print(f"PAR Medium fade: beat #{self.par_fade_beat_count}")
        
    def _apply_very_reactive_fade_pattern(self, current_time):
        """Very reactive mode: 4-beat sequence with rapid alternation"""
        # Beat 1: Both PARs fade on
        # Beat 2: PARs alternate (PAR 0 off, PAR 1 on or vice versa)
        # Beat 3: Reverse alternation 
        # Beat 4: Both PARs fade off
        # Beat 5: Sequence repeats
        
        beat_in_sequence = ((self.par_fade_beat_count - 1) % 4) + 1  # 1-4 cycle
        
        for light_id in self.light_groups['par']:
            par_state = self.par_fade_states[light_id]
            if 'par_index' not in par_state:
                par_state['par_index'] = list(self.light_groups['par']).index(light_id)
            par_index = par_state['par_index']
            
            if beat_in_sequence == 1:  # Beat 1: Both PARs fade on
                par_state['phase'] = 'fading_on'
                par_state['fade_start_time'] = current_time
            elif beat_in_sequence == 2:  # Beat 2: Alternate (PAR 0 off, PAR 1 stays on)
                if par_index == 0:
                    par_state['phase'] = 'fading_off'
                    par_state['fade_start_time'] = current_time
            elif beat_in_sequence == 3:  # Beat 3: Reverse (PAR 0 on, PAR 1 off)
                if par_index == 0:
                    par_state['phase'] = 'fading_on'
                    par_state['fade_start_time'] = current_time
                elif par_index == 1:
                    par_state['phase'] = 'fading_off'
                    par_state['fade_start_time'] = current_time
            elif beat_in_sequence == 4:  # Beat 4: Both PARs fade off
                par_state['phase'] = 'fading_off'
                par_state['fade_start_time'] = current_time
                
        # Reduced logging - only log occasionally
        if random.random() < 0.1:  # 10% chance
            print(f"PAR VeryReactive fade: beat #{self.par_fade_beat_count}")
    
    def _apply_par_slow_fade(self, base_intensity: int, light_id: str, music_info: dict) -> int:
        """Apply fade pattern for PAR lights in easy/medium/very_reactive modes"""
        current_song = music_info.get('song_config', {})
        reactivity_mode = current_song.get('reactivity_mode', 'medium')
        
        # Only apply fade system to these modes (not to the old beat pulse)
        if reactivity_mode not in ['easy', 'medium', 'very_reactive']:
            return base_intensity
            
        current_time = time.time()
        
        # Initialize PAR state if needed
        if light_id not in self.par_fade_states:
            # Find the index of this PAR in the light group
            par_index = list(self.light_groups['par']).index(light_id) if light_id in self.light_groups['par'] else 0
            self.par_fade_states[light_id] = {
                'phase': 'off',
                'fade_start_time': 0,
                'target_intensity': 0,
                'current_intensity': 0,
                'par_index': par_index
            }
        
        # Ensure par_index exists (backward compatibility)
        if 'par_index' not in self.par_fade_states[light_id]:
            par_index = list(self.light_groups['par']).index(light_id) if light_id in self.light_groups['par'] else 0
            self.par_fade_states[light_id]['par_index'] = par_index
        
        par_state = self.par_fade_states[light_id]
        
        # Different fade speeds based on reactivity mode - much faster for high reactivity
        if reactivity_mode == 'easy':
            fade_duration = 1.2  # 1.2 second fade time for much slower, smoother transition
        elif reactivity_mode == 'medium':
            # Make medium mode more blinky: faster fades for more frequent changes
            energy = music_info.get('current_level', 0.5)
            base_fade_time = 0.3  # Reduced from 0.5 for more blinking
            # Scale fade time: 0.5s for low energy, 0.2s for high energy (faster range)
            energy_factor = 0.5 - (energy * 0.3)  # Range: 0.5 to 0.2
            fade_duration = max(0.2, min(0.5, energy_factor))
        else:  # very_reactive
            fade_duration = 0.08  # Ultra-fast 0.08s fade time for maximum responsiveness (was 0.15s)
        
        # Calculate fade progress based on current phase
        if par_state['phase'] == 'fading_on':
            elapsed = current_time - par_state['fade_start_time']
            progress = min(elapsed / fade_duration, 1.0)
            # Ultra-smooth S-curve for gradual fade in
            smooth_progress = self._smooth_step_curve(progress)
            fade_intensity = int(smooth_progress * base_intensity)
            
            if progress >= 1.0:
                par_state['phase'] = 'on'
                par_state['current_intensity'] = base_intensity
            else:
                par_state['current_intensity'] = fade_intensity
                
        elif par_state['phase'] == 'fading_off':
            elapsed = current_time - par_state['fade_start_time']
            progress = min(elapsed / fade_duration, 1.0)
            # Ultra-smooth S-curve for gradual fade out
            smooth_progress = self._smooth_step_curve(progress)
            fade_intensity = int((1.0 - smooth_progress) * base_intensity)
            
            if progress >= 1.0:
                par_state['phase'] = 'off'
                par_state['current_intensity'] = 0
            else:
                par_state['current_intensity'] = fade_intensity
                
        elif par_state['phase'] == 'on':
            par_state['current_intensity'] = base_intensity
            
        else:  # 'off'
            par_state['current_intensity'] = 0
        
        # Ensure minimum visibility
        final_intensity = max(5, par_state['current_intensity']) if par_state['current_intensity'] > 0 else 0
        
        # Reduce debug frequency - only log occasionally to prevent log spam
        if light_id == list(self.light_groups['par'])[0] if self.light_groups['par'] else None:
            beat_in_sequence = ((self.par_fade_beat_count - 1) % 12) + 1
            # Only log every 5 seconds instead of every beat
            if beat_in_sequence == 1 and hasattr(self, '_last_par_debug') and time.time() - self._last_par_debug > 5.0:
                self._last_par_debug = time.time()
                # Reduced logging - only log occasionally
                if random.random() < 0.02:  # 2% chance
                    print(f"PAR {light_id}: {par_state['phase']}, intensity={final_intensity}")
            elif not hasattr(self, '_last_par_debug'):
                self._last_par_debug = time.time()
        
        return final_intensity
    
    def _apply_wash_pulse_with_reactivity(self, intensity: int, light_id: str, lights_config: dict, music_info: dict) -> int:
        """Apply wash pulsing with reactivity mode detection"""
        current_song = music_info.get('song_config', {})
        reactivity_mode = current_song.get('reactivity_mode', 'medium')
        return self._apply_smooth_wash_pulse(intensity, light_id, lights_config, reactivity_mode)
    
    def _apply_smooth_wash_pulse(self, intensity: int, light_id: str, lights_config: dict, reactivity_mode: str = 'medium') -> int:
        """Apply beat pulsing for wash lights - smooth for easy/medium, reactive for very_reactive"""
        # Check if this light has beat pulse enabled
        light_config = lights_config.get('lights', {}).get(light_id, {})
        beat_pulse_enabled = light_config.get('beat_pulse_enabled', False)
        
        if not beat_pulse_enabled or light_id not in self.light_groups.get('wash', []):
            return intensity
            
        # Very reactive mode uses direct beat pulse for maximum responsiveness
        if reactivity_mode == 'very_reactive':
            return self._apply_beat_pulse(intensity, light_id, lights_config)
        
        # Smoother wash light patterns with longer transitions
        pattern_cycle = (self.beat_count // 6) % 2  # Change pattern every 6 beats for smoother transitions
        
        if pattern_cycle == 0:
            # Pattern 1: Alternating wash lights (wash 0 on odd beats, wash 1 on even beats)
            wash_index = list(self.light_groups['wash']).index(light_id) if light_id in self.light_groups['wash'] else 0
            wash_should_be_bright = (self.beat_count % 2) == (wash_index % 2)
        else:
            # Pattern 2: All wash lights pulse together every other beat
            wash_should_be_bright = (self.beat_count % 2) == 1
        
        if self.beat_pulse_active:
            # During beat flash - smoother transitions
            if wash_should_be_bright:
                # Use max_dimmer from config, or default to 255
                max_dimmer = light_config.get('max_dimmer', 255)
                return max_dimmer
            else:
                # Gentle fade to 30% instead of complete darkness for smoother look
                return int(intensity * 0.3)
        else:
            # Between beats - maintain gentle presence
            if wash_should_be_bright:
                return int(intensity * 0.7)  # Brighter between beats for smoother transitions
            else:
                return int(intensity * 0.4)  # Dimmed but still visible for smoothness

    def _update_beat_pulse(self, beat_detected: bool, music_info: dict = None):
        """Update the beat pulse system - alternating PAR/wash on/off on beats"""
        current_time = time.time()
        
        # Get reactivity mode for ultra-fast pulses in very reactive mode
        current_song = music_info.get('song_config', {}) if music_info else {}
        reactivity_mode = current_song.get('reactivity_mode', 'medium')
        
        # Adjust beat pulse duration based on reactivity mode and tempo
        tempo = music_info.get('tempo', 120) if music_info else 120
        
        if reactivity_mode == 'very_reactive':
            # Very reactive mode: ultra-fast pulses regardless of tempo
            current_beat_duration = self.beat_pulse_duration * 0.4  # 60ms - ultra-fast
        elif tempo < 80:
            # Very slow songs - hold lights longer for more impact
            current_beat_duration = self.beat_pulse_duration * 2.5  # 375ms
        elif tempo < 100:
            # Slow songs - moderate longer duration  
            current_beat_duration = self.beat_pulse_duration * 1.8  # 270ms
        elif tempo < 140:
            # Medium tempo - standard duration
            current_beat_duration = self.beat_pulse_duration  # 150ms
        else:
            # Fast tempo - shorter, snappier duration
            current_beat_duration = self.beat_pulse_duration * 0.7  # 105ms
        
        if beat_detected:
            # Increment beat counter for alternating pattern
            self.beat_count += 1
            self.last_beat_time = current_time
            self.last_beat_pulse_time = current_time
            
            # Activate beat pulse (lights go OFF during pulse)
            self.beat_pulse_active = True
            
            # Also activate strobe for PAR lights
            self.beat_strobe_active = True
            
            # print(f"BEAT #{self.beat_count} DETECTED! Lights FLASH BRIGHT for {current_beat_duration:.0f}ms (tempo: {tempo}bpm, time: {current_time:.2f})")
        
        # Check if beat pulse should turn off (lights go back ON)
        if self.beat_pulse_active and (current_time - self.last_beat_pulse_time) > current_beat_duration:
            self.beat_pulse_active = False
            # print(f"Beat flash ended - lights back to dim level (time: {current_time:.2f})")
        
        # Check if beat strobe should turn off
        if self.beat_strobe_active and (current_time - self.last_beat_time) > self.beat_strobe_duration:
            self.beat_strobe_active = False
    
    def _apply_beat_pulse(self, intensity: int, light_id: str, lights_config: dict) -> int:
        """Apply beat pulsing based on light configuration with interesting variations"""
        # Check if this light has beat pulse enabled
        light_config = lights_config.get('lights', {}).get(light_id, {})
        beat_pulse_enabled = light_config.get('beat_pulse_enabled', False)
        
        if not beat_pulse_enabled:
            return intensity
        
        is_par_light = light_id in self.light_groups.get('par', [])
        is_wash_light = light_id in self.light_groups.get('wash', [])
        
        # DYNAMIC BEAT PATTERNS: Mix up the patterns for more interesting effects
        # Pattern changes every 8 beats to keep things fresh
        pattern_cycle = (self.beat_count // 8) % 3  # 3 different patterns
        
        if pattern_cycle == 0:
            # Pattern 1: Traditional alternating (Pars on odd, Washes on even)
            par_should_flash = (self.beat_count % 2) == 1
            wash_should_flash = (self.beat_count % 2) == 0
        elif pattern_cycle == 1:
            # Pattern 2: Both flash together every other beat
            par_should_flash = (self.beat_count % 2) == 1
            wash_should_flash = (self.beat_count % 2) == 1
        else:
            # Pattern 3: Washes change half as often (every 2 beats), Pars every beat
            par_should_flash = True  # Pars flash every beat
            wash_should_flash = ((self.beat_count // 2) % 2) == 1  # Washes change every 2 beats
        
        if self.beat_pulse_active:
            # During beat flash
            if is_par_light:
                should_flash = par_should_flash
            elif is_wash_light:
                should_flash = wash_should_flash
            else:
                # Accent lights always flash
                should_flash = True
                
            if should_flash:
                # Make wash flashes extra bright to ensure they're visible
                if is_wash_light:
                    # Use max_dimmer from config, or default to 255
                    max_dimmer = light_config.get('max_dimmer', 255)
                    flash_intensity = max_dimmer
                    # print(f"{light_id.upper()} WASH FLASH MAX (beat #{self.beat_count}) -> intensity {flash_intensity}")
                else:
                    flash_intensity = min(255, int(intensity * 3.0))  # 3x brighter for others
                    # print(f"{light_id.upper()} FLASH BRIGHT (beat #{self.beat_count}) -> intensity {flash_intensity}")
                return flash_intensity
            else:
                # Allow PAR lights to go darker for better strobing
                if is_par_light:
                    return 0  # Go completely dark for maximum dramatic effect
                else:
                    # print(f"{light_id.upper()} OFF (beat #{self.beat_count}) -> intensity 0")
                    return 0
        else:
            # Between beats
            if is_par_light:
                should_be_on = par_should_flash
            elif is_wash_light:
                should_be_on = wash_should_flash
            else:
                should_be_on = True
                
            if should_be_on:
                # Dimmed but still visible
                if is_wash_light:
                    return int(intensity * 0.4)  # Washes slightly brighter between beats
                else:
                    return int(intensity * 0.2)  # Pars dimmer between beats for more contrast
            else:
                # Allow PAR lights to go very dark between beats for contrast
                if is_par_light:
                    return 0  # Go completely dark between beats for maximum contrast
                else:
                    # Stay completely off for other lights
                    return 0
    
    def _apply_beat_strobe_color(self, original_color: dict, light_id: str) -> dict:
        """Apply beat strobe coloring - white flash for PAR lights during strobe"""
        if self.beat_strobe_active and light_id in self.light_groups['par']:
            return {'r': 255, 'g': 255, 'b': 255}  # White strobe
        return original_color
    
    def activate_engine(self):
        """Activate the light show engine"""
        self.engine_active = True
        self.effect_start_time = 0  # Force immediate effect selection on first frame
        self.show_start_time = time.time()  # Record when show started
        self.last_status_log = self.show_start_time  # Reset status logging
        self.slow_cycle_mode = False  # Track if we're in 5-minute slow cycle mode
        self.slow_cycle_start_time = 0  # When slow cycle mode started
        print(f"LIGHT SHOW STARTED - Engine activated at {time.strftime('%H:%M:%S')}")
        print(f"   Effect duration: {self.effect_duration}s | Fade speed: {self.current_fade_speed}")
        print(f"   5-minute slow cycle: Will activate at {time.strftime('%H:%M:%S', time.localtime(self.show_start_time + 300))}")
        print(f"   Ready to generate dynamic lighting effects!")
    
    def deactivate_engine(self):
        """Deactivate the light show engine"""
        if self.engine_active and self.show_start_time > 0:
            show_duration = time.time() - self.show_start_time
            if self.slow_cycle_mode:
                slow_duration = time.time() - self.slow_cycle_start_time
                print(f"LIGHT SHOW ENDED - Duration: {show_duration:.1f} seconds ({show_duration/60:.1f} minutes)")
                print(f"   Slow cycle was active for: {slow_duration:.1f} seconds ({slow_duration/60:.1f} minutes)")
                print(f"   Final effect: '{self.current_effect}' | Show completed at {time.strftime('%H:%M:%S')}")
            else:
                print(f"LIGHT SHOW ENDED - Duration: {show_duration:.1f} seconds ({show_duration/60:.1f} minutes)")
                print(f"   Final effect: '{self.current_effect}' | Show completed at {time.strftime('%H:%M:%S')}")
        
        self.engine_active = False
        self.slow_cycle_mode = False  # Reset slow cycle mode
        self.slow_cycle_start_time = 0

    def setup_light_groups(self, lights_config: Dict):
        wash_keywords = ['wash', 'flood', 'panel', 'strip']
        par_keywords = ['par', 'spot', 'beam']
        self.light_groups = {'wash': [], 'par': [], 'accent': []}
        for light_id, light_info in lights_config.get('lights', {}).items():
            name = light_info.get('name', '').lower()
            if any(k in name for k in wash_keywords):
                self.light_groups['wash'].append(light_id)
            elif any(k in name for k in par_keywords):
                self.light_groups['par'].append(light_id)
            else:
                self.light_groups['accent'].append(light_id)

    def choose_effect_for_music(self, music_info: dict) -> str:
        energy = music_info.get('current_level', 0.5)
        beat_detected = music_info.get('beat_detected', False)
        current_time = time.time()
        
        # Show intro: first 6 seconds with faster transitions
        if self.show_start_time > 0 and current_time - self.show_start_time < 6.0:
            elapsed = current_time - self.show_start_time
            if elapsed < 1.5:
                return 'gentle_fade_in'
            elif elapsed < 3.0:
                return 'slow_color_build'
            elif elapsed < 4.5:
                return 'wash_pulse'
            else:
                return random.choice(['static_scene', 'par_impact'])  # More variety

        # Much more dynamic effect selection with variety
        if energy < 0.15:
            return random.choice(['gentle_ambient', 'soft_pulse'])  # Rotate even in low energy
        elif energy < 0.35:
            return random.choice(['soft_pulse', 'wash_pulse', 'static_scene'])  # More options
        elif energy < 0.55:
            return random.choice(['wash_pulse', 'static_scene', 'par_impact', 'color_chase'])
        elif beat_detected and energy > 0.65:
            return random.choice(['par_impact', 'full_on', 'color_chase'])  # High-energy options (strobe now built-in)
        elif energy > 0.5:
            return random.choice(['full_on', 'wash_pulse', 'par_impact', 'color_chase'])  # Rotate frequently
        else:
            return random.choice(['wash_pulse', 'static_scene', 'par_impact'])  # Always have variety

    def generate_light_frame(self, music_info: dict, lights_config: dict) -> Dict[str, Dict[str, int]]:
        current_time = time.time()
        
        # Check for 5-minute slow cycle activation
        show_duration = current_time - self.show_start_time if self.show_start_time > 0 else 0
        if show_duration >= 300 and not self.slow_cycle_mode:  # 5 minutes = 300 seconds
            self.slow_cycle_mode = True
            self.slow_cycle_start_time = current_time
            print(f"\n🕐 5-MINUTE SLOW CYCLE ACTIVATED at {time.strftime('%H:%M:%S')}")
            print(f"   Lights will now cycle slowly at 50 BPM (1.2 second intervals)")
            print(f"   Show duration: {show_duration/60:.1f} minutes\n")
        
        # Override beat detection and music info if in slow cycle mode
        if self.slow_cycle_mode:
            # Create artificial 50 BPM beat pattern (1.2 second intervals)
            slow_cycle_time = current_time - self.slow_cycle_start_time
            beat_interval = 1.2  # 50 BPM = 1.2 seconds per beat
            artificial_beat = (slow_cycle_time % beat_interval) < 0.1  # Beat pulse for first 100ms of each cycle
            
            # Override music info for slow cycling
            music_info = dict(music_info)  # Create a copy
            music_info['beat_detected'] = artificial_beat
            music_info['tempo'] = 50  # Force 50 BPM
            music_info['current_level'] = 0.3  # Moderate energy level for smooth cycling
            music_info['reactivity_mode'] = 'easy'  # Use easy mode for smoothest cycling
            
            beat_detected = artificial_beat
        else:
            # Update beat pulse system for dramatic PAR effects
            beat_detected = music_info.get('beat_detected', False)
        # Debug: Log beat detection and frequency band status occasionally
        if current_time % 5 < 0.1:  # Every 5 seconds roughly
            freq_bands = music_info.get('frequency_bands', {'bass': 0, 'mid': 0, 'treble': 0})
            # Debug disabled for cleaner output
        
        # Update both beat pulse and PAR fade systems
        self._update_beat_pulse(beat_detected, music_info)
        self._update_par_fade_system(beat_detected, music_info)
        
        # Check for frequency changes (disabled automatic palette forcing for stability)
        freq_changed = self._detect_frequency_change(music_info)
        # Note: Automatic palette forcing disabled to prevent rapid color changes
        # Palette changes now happen only on the natural 2-minute timer
        
        # Debug: Check if lights_config is the correct type
        if not isinstance(lights_config, dict):
            print(f"ERROR: lights_config is {type(lights_config)}, expected dict. Value: {lights_config}")
            return {}
            
        if 'lights' not in lights_config:
            print(f"ERROR: 'lights' key missing from lights_config. Keys: {list(lights_config.keys())}")
            return {}
        
        all_lights = list(lights_config.get('lights', {}).keys())

        # If engine is not active, return empty/off states for all lights
        if not self.engine_active:
            return {light_id: {'r': 0, 'g': 0, 'b': 0, 'intensity': 0} for light_id in all_lights}

        for light_id in all_lights:
            if light_id not in self.current_states:
                self.current_states[light_id] = {'r': 0, 'g': 0, 'b': 0, 'intensity': 0}
            if light_id not in self.target_states:
                self.target_states[light_id] = {'r': 255, 'g': 255, 'b': 255, 'intensity': 0}

        # Always choose effect on first call, or when duration expires
        if self.effect_start_time == 0 or current_time - self.effect_start_time > self.effect_duration:
            new_effect = self.choose_effect_for_music(music_info)
            if new_effect != self.current_effect:
                # Enhanced logging with comprehensive music data
                energy = music_info.get('current_level', 0)
                tempo = music_info.get('tempo', 0)
                beat_detected = music_info.get('beat_detected', False)
                is_fast_tempo = music_info.get('is_fast_tempo', False)
                is_building = music_info.get('is_building', False)
                is_quiet = music_info.get('is_quiet', False)
                
                print(f"EFFECT CHANGE: '{self.current_effect}' -> '{new_effect}'")
                print(f"   Energy: {energy:.3f} | Tempo: {tempo} BPM | Fast: {is_fast_tempo} | Beat: {'BEAT' if beat_detected else 'NO BEAT'}")
                duration_log = f"{(current_time - self.effect_start_time):.1f}s" if self.effect_start_time > 0 else "(new show)"
                print(f"   Building: {is_building} | Quiet: {is_quiet} | Duration: {duration_log}")
                
            self.current_effect = new_effect
            self.effect_start_time = current_time

        # Make sure light groups are set up
        if not any(self.light_groups.values()):
            self.setup_light_groups(lights_config)
            print(f"Light groups configured - wash: {len(self.light_groups['wash'])}, par: {len(self.light_groups['par'])}, accent: {len(self.light_groups['accent'])}")
        
        # Periodic status logging every 10 seconds
        if current_time - self.last_status_log > 10.0:
            self.last_status_log = current_time
            energy = music_info.get('current_level', 0)
            tempo = music_info.get('tempo', 0)
            beat_detected = music_info.get('beat_detected', False)
            is_fast_tempo = music_info.get('is_fast_tempo', False)
            
            # Calculate show runtime
            show_time = current_time - self.show_start_time if self.show_start_time > 0 else 0
            
            print(f"SHOW STATUS [{show_time:.0f}s]: Effect='{self.current_effect}' | Energy={energy:.3f} | Tempo={tempo}bpm | Fast={is_fast_tempo} | Beat={'BEAT' if beat_detected else 'NO BEAT'}")
        
        # Get a consistent color for this frame to avoid primary/secondary mixing within effects
        frame_color = self.color_engine.get_color_for_music(music_info)
        music_info['frame_color'] = frame_color  # Pass the consistent color to effects
        # print(f"DEBUG FRAME COLOR: Set frame_color to RGB({frame_color['r']}, {frame_color['g']}, {frame_color['b']})")
        
        # Check if this is a significant color change and adjust fade speed based on tempo and change
        if hasattr(self, 'last_frame_color'):
            color_distance = abs(frame_color['r'] - self.last_frame_color['r']) + \
                           abs(frame_color['g'] - self.last_frame_color['g']) + \
                           abs(frame_color['b'] - self.last_frame_color['b'])
            
            tempo = music_info.get('tempo', 120)
            
            # Adjust sensitivity based on tempo
            if tempo > 140:
                # Fast tempo - be more sensitive to changes, use faster fades
                threshold = 150
                fast_speed = 'fast'
            elif tempo < 80:
                # Slow tempo - less sensitive, but still smooth
                threshold = 300
                fast_speed = 'medium'
            else:
                # Medium tempo - standard behavior
                threshold = 200
                fast_speed = 'fast'
            
            if color_distance > threshold:
                self.current_fade_speed = fast_speed
                # print(f"DEBUG: Color change detected (distance={color_distance}, tempo={tempo}bpm), using '{fast_speed}' fade")
            else:
                # Use slower fade for subtle changes
                self.current_fade_speed = 'slow' if tempo < 80 else 'medium'
        
        self.last_frame_color = frame_color.copy()
        
        effect_function = self.effects.get(self.current_effect, self._effect_darkness)
        self.target_states = effect_function(music_info, lights_config)

        # Debug: Show color transitions every 15 seconds if there's a meaningful difference
        if not hasattr(self, '_last_target_current_log'):
            self._last_target_current_log = 0
            
        if current_time - self._last_target_current_log > 15.0 and self.target_states:  # Every 15 seconds
            sample_light = list(self.target_states.keys())[0]
            target_color = self.target_states[sample_light]
            current_color = self.current_states[sample_light]
            
            # Calculate color distance to see if there's a meaningful difference
            r_diff = abs(target_color.get('r', 0) - current_color.get('r', 0))
            g_diff = abs(target_color.get('g', 0) - current_color.get('g', 0))
            b_diff = abs(target_color.get('b', 0) - current_color.get('b', 0))
            total_diff = r_diff + g_diff + b_diff
            
            # Only log if there's a significant difference (more than 10 total RGB difference)
            if total_diff > 10:
                self._last_target_current_log = current_time
                print(f"{sample_light} transitioning: Target({target_color.get('r', 0)},{target_color.get('g', 0)},{target_color.get('b', 0)}) → Current({int(current_color.get('r', 0))},{int(current_color.get('g', 0))},{int(current_color.get('b', 0))})")

        fade_speed = self.fade_speeds[self.current_fade_speed]
        max_step = self.max_step_sizes[self.current_fade_speed]
        
        for light_id in all_lights:
            # Use extra smooth transitions for wash lights
            if light_id in self.light_groups.get('wash', []):
                wash_fade_speed = self.fade_speeds['wash_smooth']
                wash_max_step = self.max_step_sizes['wash_smooth']
            else:
                wash_fade_speed = fade_speed
                wash_max_step = max_step
                
            for key in self.current_states[light_id]:
                current = self.current_states[light_id][key]
                target = self.target_states.get(light_id, {}).get(key, 0)
                
                diff = target - current
                if abs(diff) < 1:  # Snap when very close
                    self.current_states[light_id][key] = target
                else:
                    # Calculate desired step with easing (use wash-specific speeds for wash lights)
                    current_fade_speed = wash_fade_speed if light_id in self.light_groups.get('wash', []) else fade_speed
                    current_max_step = wash_max_step if light_id in self.light_groups.get('wash', []) else max_step
                    
                    eased_speed = self._ease_out_quad(current_fade_speed)
                    desired_step = diff * eased_speed
                    
                    # Cap the step size for smooth increments
                    if abs(desired_step) > current_max_step:
                        # Preserve direction but limit magnitude
                        capped_step = current_max_step if desired_step > 0 else -current_max_step
                    else:
                        capped_step = desired_step
                    
                    self.current_states[light_id][key] += capped_step

        return {l_id: {k: int(v) for k, v in state.items()} for l_id, state in self.current_states.items()}

    def _effect_darkness(self, music_info: dict, lights_config: dict) -> Dict[str, Dict[str, int]]:
        return {light_id: {'r': 0, 'g': 0, 'b': 0, 'intensity': 0} for light_id in lights_config.get('lights', {})}

    def _effect_static_scene(self, music_info: dict, lights_config: dict) -> Dict[str, Dict[str, int]]:
        states = {}
        
        # Get music energy and frequency bands for reactivity
        energy = music_info.get('current_level', 0.5)
        beat_detected = music_info.get('beat_detected', False)
        freq_bands = music_info.get('frequency_bands', {'bass': 0, 'mid': 0, 'treble': 0})
        
        # Extract frequency levels
        bass_level = freq_bands.get('bass', 0)
        treble_level = freq_bands.get('treble', 0)
        
        # Even "static" scenes should be reactive and have variation
        energy_boost = 1.0 + energy * 0.6  # 1.0 to 1.6x boost - more reactive
        beat_boost = 2.0 if beat_detected else 1.3  # PARs get decent base intensity even without beats
        
        # Add subtle movement even to "static" scenes
        gentle_wave = math.sin(time.time() * 0.5) * 0.1 + 1.0  # Very gentle 10% variation
        
        # Get random color assignment for variety
        colors = self._get_random_color_assignment(music_info)
        
        # Wash lights - bass-reactive with subtle individual variation and smooth beat pulsing
        for i, light_id in enumerate(self.light_groups['wash']):
            individual_wave = math.sin(time.time() * 0.3 + i * 0.5) * 0.05 + 1.0  # 5% individual variation
            bass_boost = 1.0 + bass_level * 0.8  # Moderate bass response for static scenes
            wash_intensity = min(255, int(255 * energy_boost * beat_boost * individual_wave * bass_boost))
            
            # Apply beat pulsing based on configuration and reactivity mode
            wash_intensity = self._apply_wash_pulse_with_reactivity(wash_intensity, light_id, lights_config, music_info)
            
            # Use alternating colors for wash lights
            wash_color = self._get_wash_color_for_alternation(music_info, i)
            states[light_id] = {'r': wash_color['r'], 'g': wash_color['g'], 'b': wash_color['b'], 'intensity': wash_intensity}
        
        # PAR lights - treble-reactive with individual character and beat pulsing
        # Get reactivity mode from current song config
        current_song = music_info.get('song_config', {})
        reactivity_mode = current_song.get('reactivity_mode', 'medium')
        
        for i, light_id in enumerate(self.light_groups['par']):
            # REACTIVITY-AWARE PAR CALCULATION
            
            # For 'easy' mode, be much more likely to use primary/secondary colors
            treble_threshold = 0.4 if reactivity_mode == 'easy' else 0.3

            if treble_level < treble_threshold:
                # Low treble - base intensity varies by reactivity mode
                if reactivity_mode == 'very_reactive':
                    par_intensity = min(255, int(50 + energy * 205))  # 50-255 range - very reactive
                elif reactivity_mode == 'easy':
                    par_intensity = min(255, int(150 + energy * 50))  # 150-200 range - calmer
                else:  # medium
                    # Enhanced reactivity for medium mode - lower base, higher energy scaling
                    base_intensity = 80 if energy < 0.3 else 50  # Much lower base for higher energy response
                    par_intensity = min(255, int(base_intensity + energy * 205))  # 50-255 range - much more reactive
                par_color = self._get_par_color_for_low_treble(music_info, i)
            else:
                # High treble - varies by reactivity mode
                if reactivity_mode == 'very_reactive':
                    treble_boost = 30 + treble_level * 150  # 30-180 additional intensity - very reactive
                    par_intensity = min(255, int(25 + energy * 80 + treble_boost))  # Can go very low
                elif reactivity_mode == 'easy':
                    treble_boost = 40 + treble_level * 60  # 40-100 additional intensity - calmer
                    par_intensity = min(255, int(155 + energy * 40 + treble_boost))  # Higher base
                else:  # medium
                    # Enhanced treble responsiveness for medium mode
                    treble_boost = 50 + treble_level * 140  # 50-190 additional intensity - much more reactive
                    base_energy = 50 if energy < 0.4 else 25  # Much lower base for dramatic energy response
                    par_intensity = min(255, int(base_energy + energy * 120 + treble_boost))  # Much wider dynamic range
                par_color = colors['par'][i] if i < len(colors['par']) else music_info.get('frame_color', self.color_engine.get_color_for_music(music_info))
            
            # Apply appropriate pulsing based on reactivity mode
            if reactivity_mode == 'very_reactive':
                # Very reactive mode uses direct beat pulse for maximum responsiveness
                par_intensity = self._apply_beat_pulse(par_intensity, light_id, lights_config)
            elif reactivity_mode in ['easy', 'medium']:
                # Easy/medium modes use slow fade system for smoother transitions
                par_intensity = self._apply_par_slow_fade(par_intensity, light_id, music_info)
            else:
                # Fallback to old beat pulse system for any other modes
                par_intensity = self._apply_beat_pulse(par_intensity, light_id, lights_config)
            
            # Use the determined PAR color - PARs should always have color, never black
            strobe_color = self._apply_beat_strobe_color(par_color, light_id)
            
            # Minimum intensity depends on reactivity mode - allow strobing to go darker
            if reactivity_mode == 'very_reactive':
                min_intensity = 0  # Can go completely dark for dramatic effect
            elif reactivity_mode == 'easy':
                min_intensity = 30  # Never too dim
            else:  # medium
                min_intensity = 5  # Lower minimum for better contrast
                
            if par_intensity < min_intensity:
                par_intensity = min_intensity
            
            # Debug logging removed - use DMX simulator for visual feedback instead
            pass  # PAR intensity values are shown in the DMX simulator
            
            states[light_id] = {'r': strobe_color['r'], 'g': strobe_color['g'], 'b': strobe_color['b'], 'intensity': par_intensity}
        
        # Accent lights - subtle movement
        for i, light_id in enumerate(self.light_groups['accent']):
            accent_wave = math.sin(time.time() * 0.2 + i * 0.8) * 0.1 + 1.0
            accent_intensity = min(255, int(70 * energy_boost * beat_boost * accent_wave))
            states[light_id] = {'r': int(wash_color['r'] * 0.8), 'g': int(wash_color['g'] * 0.8), 'b': int(wash_color['b'] * 0.8), 'intensity': accent_intensity}
        
        return states

    def _effect_par_impact(self, music_info: dict, lights_config: dict) -> Dict[str, Dict[str, int]]:
        states = {}
        color = music_info.get('frame_color', self.color_engine.get_color_for_music(music_info))
        
        # Get music energy and frequency bands for impact scaling
        energy = music_info.get('current_level', 0.5)
        beat_detected = music_info.get('beat_detected', False)
        freq_bands = music_info.get('frequency_bands', {'bass': 0, 'mid': 0, 'treble': 0})
        
        # PARs react strongly to treble/guitar frequencies
        treble_level = freq_bands.get('treble', 0)
        par_reactivity = 0.4 + treble_level * 1.6  # Higher treble = more reactive PARs
        
        # Strong impact effect - more PARs light up with higher treble
        base_pars = int(2 + energy * 2)  # 2-4 base PARs
        treble_bonus_pars = int(treble_level * 2)  # 0-2 additional PARs for high treble
        num_pars_to_light = min(len(self.light_groups['par']), max(1, base_pars + treble_bonus_pars))
        selected_pars = random.sample(self.light_groups['par'], num_pars_to_light) if self.light_groups['par'] else []
        
        # All lights start dark
        for light_id in lights_config.get('lights', {}):
            states[light_id] = {'r': 0, 'g': 0, 'b': 0, 'intensity': 0}
            
        # Get reactivity mode for appropriate pulsing
        current_song = music_info.get('song_config', {})
        reactivity_mode = current_song.get('reactivity_mode', 'medium')
        treble_threshold = 0.4 if reactivity_mode == 'easy' else 0.3
        
        # Light PARs - either all (if low treble) or selected (if high treble)  
        if treble_level < treble_threshold:
            # Low treble - keep all PARs on with cycling colors for visibility
            pars_to_use = self.light_groups['par']
            base_intensity = int(180 + energy * 75)  # 180-255 based on energy
            # Reduced logging - only log occasionally
            if random.random() < 0.05:  # 5% chance
                print(f"Low treble mode: cycling colors on {len(pars_to_use)} PARs")
        else:
            # High treble - use selected PARs with treble-reactive brightness
            pars_to_use = selected_pars
            base_intensity = int(200 + treble_level * 55)  # 200-255 based on treble
            
        for i, par_id in enumerate(pars_to_use):
            if reactivity_mode == 'very_reactive':
                # Very reactive mode uses direct beat pulse for maximum responsiveness
                par_intensity = self._apply_beat_pulse(base_intensity, par_id, lights_config)
            elif reactivity_mode in ['easy', 'medium']:
                # Easy/medium modes use slow fade system for smoother transitions
                par_intensity = self._apply_par_slow_fade(base_intensity, par_id, music_info)
            else:
                # Fallback to old beat pulse system for any other modes
                par_intensity = self._apply_beat_pulse(base_intensity, par_id, lights_config)
            
            # Choose color based on treble level
            if treble_level < treble_threshold:
                # Low treble - use cycling primary/secondary colors
                par_color = self._get_par_color_for_low_treble(music_info, i)
                strobe_color = self._apply_beat_strobe_color(par_color, par_id)
            else:
                # High treble - use standard frame color
                strobe_color = self._apply_beat_strobe_color(color, par_id)
            
            # Ensure PAR lights never go completely dark
            if par_intensity < 5:
                par_intensity = 5  # Minimum 5 intensity for PARs
                
            states[par_id] = {'r': strobe_color['r'], 'g': strobe_color['g'], 'b': strobe_color['b'], 'intensity': par_intensity}
            
        # Add wash light ambiance that reacts to bass frequencies and beats
        bass_level = freq_bands.get('bass', 0)
        wash_trigger_threshold = 0.4 - bass_level * 0.3  # Lower threshold with more bass
        
        if energy > wash_trigger_threshold or bass_level > 0.3:
            # Wash intensity scales with bass + energy 
            base_wash_intensity = int(180 + bass_level * 75)  # 180-255 based on bass
            
            for i, light_id in enumerate(self.light_groups['wash']):
                # Apply smoother alternating beat pulsing to wash lights
                wash_intensity = self._apply_wash_pulse_with_reactivity(base_wash_intensity, light_id, lights_config, music_info)
                # Use alternating colors for wash lights
                wash_color = self._get_wash_color_for_alternation(music_info, i)
                wash_color_intensity = 0.2 + bass_level * 0.3  # 0.2-0.5 based on bass
                states[light_id] = {
                    'r': int(wash_color['r'] * wash_color_intensity), 
                    'g': int(wash_color['g'] * wash_color_intensity), 
                    'b': int(wash_color['b'] * wash_color_intensity), 
                    'intensity': wash_intensity
                }
                
        return states

    def _effect_wash_pulse(self, music_info: dict, lights_config: dict) -> Dict[str, Dict[str, int]]:
        states = {}
        
        # Get music reactivity data including frequency bands
        energy = music_info.get('current_level', 0.5)
        beat_detected = music_info.get('beat_detected', False)
        freq_bands = music_info.get('frequency_bands', {'bass': 0, 'mid': 0, 'treble': 0})
        
        # Wash lights highly reactive to bass and beats
        bass_level = freq_bands.get('bass', 0)
        treble_level = freq_bands.get('treble', 0)
        
        # Strong bass response for wash lights + standard energy
        energy_multiplier = 0.8 + energy * 1.0 + bass_level * 1.2  # Bass boost for washes
        beat_multiplier = 2.5 if beat_detected else 1.0  # Very strong beat response
        bass_multiplier = 1.0 + bass_level * 1.5  # Additional bass-specific boost
        
        # Get random color assignment for variety
        colors = self._get_random_color_assignment(music_info)
        
        # Base pulsing with bass-reactive speed and variation
        pulse_speed = 2 + energy * 4 + bass_level * 3  # Faster pulsing with higher energy/bass
        pulse_base = math.sin(time.time() * pulse_speed) * 0.5 + 0.5  # 0 to 1
        pulse_smooth = self._ease_in_out(pulse_base)
        
        # Wash lights - bass-reactive with individual variation and smooth beat pulsing
        for i, light_id in enumerate(self.light_groups['wash']):
            # Slight phase offset for each wash light to create wave effect
            phase_offset = i * 0.5
            wash_pulse = math.sin(time.time() * pulse_speed + phase_offset) * 0.5 + 0.5
            wash_smooth = self._ease_in_out(wash_pulse)
            wash_base = int(150 + wash_smooth * 105)  # Base 150 to 255
            
            # Bass-reactive intensity calculation
            wash_intensity = min(255, int(wash_base * energy_multiplier * beat_multiplier * bass_multiplier))
            
            # Apply smoother alternating beat pulsing to wash lights
            wash_intensity = self._apply_wash_pulse_with_reactivity(wash_intensity, light_id, lights_config, music_info)
            
            # Use alternating colors for wash lights
            wash_color = self._get_wash_color_for_alternation(music_info, i)
            states[light_id] = {'r': wash_color['r'], 'g': wash_color['g'], 'b': wash_color['b'], 'intensity': wash_intensity}
        
        # PAR lights - treble-reactive with individual variation and beat pulsing
        for i, light_id in enumerate(self.light_groups['par']):
            # Each PAR can have different timing for more dynamic look
            par_phase = 1.5 + i * 0.8 + treble_level * 2.0  # Treble affects timing
            par_pulse = math.sin(time.time() * pulse_speed + par_phase) * 0.5 + 0.5
            par_smooth = self._ease_in_out(par_pulse)
            par_base = int(150 + par_smooth * 105)  # Base 150 to 255
            
            if treble_level < 0.3:
                # Low treble - ensure PARs stay on with moderate intensity and cycling colors
                par_intensity = min(255, int(par_base * 1.2 * beat_multiplier))  # Moderate consistent brightness
                par_color = self._get_par_color_for_low_treble(music_info, i)
            else:
                # High treble - use treble-reactive intensity and assigned colors
                treble_multiplier = 1.0 + treble_level * 1.8  # Strong treble response for PARs
                par_energy_multiplier = 0.6 + energy * 0.8 + treble_level * 1.4  # Treble boost for PARs
                par_intensity = min(255, int(par_base * par_energy_multiplier * beat_multiplier * treble_multiplier))
                par_color = colors['par'][i] if i < len(colors['par']) else music_info.get('frame_color', self.color_engine.get_color_for_music(music_info))
            
            # Apply appropriate pulsing based on reactivity mode
            current_song = music_info.get('song_config', {})
            reactivity_mode = current_song.get('reactivity_mode', 'medium')
            
            if reactivity_mode == 'very_reactive':
                # Very reactive mode uses direct beat pulse for maximum responsiveness
                par_intensity = self._apply_beat_pulse(par_intensity, light_id, lights_config)
            elif reactivity_mode in ['easy', 'medium']:
                # Easy/medium modes use slow fade system for smoother transitions
                par_intensity = self._apply_par_slow_fade(par_intensity, light_id, music_info)
            else:
                # Fallback to old beat pulse system for any other modes
                par_intensity = self._apply_beat_pulse(par_intensity, light_id, lights_config)
            
            # Use the determined PAR color - PARs should always have color, never black
            strobe_color = self._apply_beat_strobe_color(par_color, light_id)
            
            # Ensure PAR lights never go completely dark
            if par_intensity < 5:
                par_intensity = 5  # Minimum 5 intensity for PARs
                
            states[light_id] = {'r': strobe_color['r'], 'g': strobe_color['g'], 'b': strobe_color['b'], 'intensity': par_intensity}
            
        # Accent lights with individual timing
        for i, light_id in enumerate(self.light_groups['accent']):
            accent_pulse = math.sin(time.time() * (1.5 + energy) + i * 0.3) * 0.5 + 0.5
            accent_smooth = self._ease_in_out(accent_pulse)
            accent_base = int(60 + accent_smooth * 80)
            accent_intensity = min(255, int(accent_base * energy_multiplier * beat_multiplier))
            states[light_id] = {'r': int(wash_color['r'] * 0.9), 'g': int(wash_color['g'] * 0.9), 'b': int(wash_color['b'] * 0.9), 'intensity': accent_intensity}
            
        return states

    def _effect_color_chase(self, music_info: dict, lights_config: dict) -> Dict[str, Dict[str, int]]:
        states = {}
        
        # Get music reactivity
        energy = music_info.get('current_level', 0.5)
        beat_detected = music_info.get('beat_detected', False)
        
        # Dynamic chase speed based on energy
        chase_speed = 50 + energy * 100  # 50 to 150 speed
        beat_boost = 2.2 if beat_detected else 1.3  # Good base intensity even without beats
        
        # PAR lights color chase with dramatic beat pulsing
        num_pars = len(self.light_groups['par'])
        if num_pars > 0:
            for i, light_id in enumerate(self.light_groups['par']):
                hue = (time.time() * chase_speed + i * (360 / num_pars)) % 360
                rgb = hsv_to_rgb(hue / 360.0, 1.0, 1.0)
                intensity = min(255, int(255 * beat_boost))
                
                # Apply alternating on/off beat pulsing with individual variation
                intensity = self._apply_beat_pulse(intensity, light_id, lights_config)
                
                states[light_id] = {'r': int(rgb[0]*255), 'g': int(rgb[1]*255), 'b': int(rgb[2]*255), 'intensity': intensity}
        
        # Wash lights - complementary chase (opposite direction)
        num_wash = len(self.light_groups['wash'])
        if num_wash > 0:
            for i, light_id in enumerate(self.light_groups['wash']):
                # Chase in opposite direction with offset
                hue = (-time.time() * chase_speed * 0.7 + i * (360 / num_wash) + 180) % 360
                rgb = hsv_to_rgb(hue / 360.0, 0.8, 1.0)  # Slightly less saturated
                intensity = 255  # Maximum brightness for wash lights
                states[light_id] = {'r': int(rgb[0]*255), 'g': int(rgb[1]*255), 'b': int(rgb[2]*255), 'intensity': intensity}
        
        # Accent lights - subtle complementary colors
        for i, light_id in enumerate(self.light_groups['accent']):
            hue = (time.time() * chase_speed * 0.5 + i * 120 + 90) % 360  # Slower, different offset
            rgb = hsv_to_rgb(hue / 360.0, 0.6, 0.8)
            intensity = min(255, int(100 * (1.0 + energy * 0.5) * beat_boost))
            states[light_id] = {'r': int(rgb[0]*255), 'g': int(rgb[1]*255), 'b': int(rgb[2]*255), 'intensity': intensity}
        
        return states


    def _effect_full_on(self, music_info: dict, lights_config: dict) -> Dict[str, Dict[str, int]]:
        states = {}
        
        # Get random color assignment for variety
        colors = self._get_random_color_assignment(music_info)
        
        par_index = 0  # Track PAR index for individual variation
        wash_index = 0  # Track wash index for individual variation
        
        for light_id in lights_config.get('lights', {}):
            intensity = 255
            current_color = {'r': 255, 'g': 255, 'b': 255}  # Default white
            
            # Apply appropriate pulsing for PAR lights based on reactivity mode
            if light_id in self.light_groups['par']:
                current_song = music_info.get('song_config', {})
                reactivity_mode = current_song.get('reactivity_mode', 'medium')
                
                if reactivity_mode == 'very_reactive':
                    # Very reactive mode uses direct beat pulse for maximum responsiveness
                    intensity = self._apply_beat_pulse(intensity, light_id, lights_config)
                elif reactivity_mode in ['easy', 'medium']:
                    # Easy/medium modes use slow fade system for smoother transitions
                    intensity = self._apply_par_slow_fade(intensity, light_id, music_info)
                else:
                    # Fallback to old beat pulse system for any other modes
                    intensity = self._apply_beat_pulse(intensity, light_id, lights_config)
                # Ensure PAR lights never go completely dark
                if intensity < 5:
                    intensity = 5
                    
                par_color = colors['par'][par_index] if par_index < len(colors['par']) else music_info.get('frame_color', self.color_engine.get_color_for_music(music_info))
                current_color = self._apply_beat_strobe_color(par_color, light_id)
                par_index += 1
                
            # Apply smooth alternating beat pulsing for wash lights with color alternation
            elif light_id in self.light_groups['wash']:
                intensity = self._apply_wash_pulse_with_reactivity(intensity, light_id, lights_config, music_info)
                if intensity > 0:
                    current_color = self._get_wash_color_for_alternation(music_info, wash_index)
                wash_index += 1
                
            states[light_id] = {'r': current_color['r'], 'g': current_color['g'], 'b': current_color['b'], 'intensity': intensity}
        return states

    def _effect_gentle_fade_in(self, music_info: dict, lights_config: dict) -> Dict[str, Dict[str, int]]:
        """Gentle fade-in effect for show intro (first 2 seconds)"""
        current_time = time.time()
        elapsed = current_time - self.show_start_time
        
        # Smoother fade curve using easeInOut function
        fade_progress = min(elapsed / 2.0, 1.0)
        smooth_progress = self._ease_in_out(fade_progress)
        
        # Music reactivity even during fade-in
        energy = music_info.get('current_level', 0.5)
        beat_detected = music_info.get('beat_detected', False)
        energy_boost = 1.0 + energy * 0.5  # 1.0 to 1.5x boost based on energy
        beat_boost = 2.0 if beat_detected else 1.3  # PARs get decent base intensity even without beats
        
        states = {}
        color = music_info.get('frame_color', self.color_engine.get_color_for_music(music_info))
        
        # Start with wash lights - brighter and more reactive with alternating colors
        for i, light_id in enumerate(self.light_groups['wash']):
            # Maximum brightness for wash lights
            intensity = 255
            wash_color = self._get_wash_color_for_alternation(music_info, i)
            states[light_id] = {
                'r': int(wash_color['r'] * (0.6 + smooth_progress * 0.4)),  # Start at 60% brightness
                'g': int(wash_color['g'] * (0.6 + smooth_progress * 0.4)), 
                'b': int(wash_color['b'] * (0.6 + smooth_progress * 0.4)),
                'intensity': intensity
            }
        
        # Activate PAR lights early with strong reactivity and dramatic beat pulsing
        for i, light_id in enumerate(self.light_groups['par']):
            # PAR lights start at 20% of fade progress for much earlier activation
            par_progress = max(0, (fade_progress - 0.2) / 0.8)  # Start at 20% through fade
            par_smooth = self._ease_in_out(par_progress)
            base_intensity = int(par_smooth * 80)  # Build to 80% intensity (much brighter)
            intensity = min(255, int(base_intensity * energy_boost * beat_boost))
            
            # Apply appropriate pulsing based on reactivity mode
            current_song = music_info.get('song_config', {})
            reactivity_mode = current_song.get('reactivity_mode', 'medium')
            
            if reactivity_mode == 'very_reactive':
                intensity = self._apply_beat_pulse(intensity, light_id, lights_config)
            elif reactivity_mode == 'easy':
                # Use slow fade system for easy mode
                intensity = self._apply_par_slow_fade(intensity, light_id, music_info)
            states[light_id] = {
                'r': int(color['r'] * par_smooth * 0.8),  # Brighter PAR colors
                'g': int(color['g'] * par_smooth * 0.8),
                'b': int(color['b'] * par_smooth * 0.8),
                'intensity': intensity
            }
        
        # Keep accent lights off during gentle fade-in
        for light_id in self.light_groups['accent']:
            states[light_id] = {'r': 0, 'g': 0, 'b': 0, 'intensity': 0}
            
        return states

    def _effect_slow_color_build(self, music_info: dict, lights_config: dict) -> Dict[str, Dict[str, int]]:
        """Slow color building effect (seconds 2-4 of intro)"""
        current_time = time.time()
        elapsed = current_time - self.show_start_time - 2.0  # Start after fade-in
        
        # Build intensity over 2 seconds with smooth curve
        build_progress = min(elapsed / 2.0, 1.0)
        smooth_build = self._ease_in_out(build_progress)
        
        # Strong music reactivity during build phase
        energy = music_info.get('current_level', 0.5)
        beat_detected = music_info.get('beat_detected', False)
        energy_boost = 1.0 + energy * 0.8  # 1.0 to 1.8x boost - more reactive
        beat_boost = 2.2 if beat_detected else 1.3  # Good base intensity even without beats  # Stronger beat response
        
        states = {}
        color = music_info.get('frame_color', self.color_engine.get_color_for_music(music_info))
        
        # Continue with wash lights - much brighter and more reactive with alternating colors
        for i, light_id in enumerate(self.light_groups['wash']):
            # Maximum brightness for wash lights
            intensity = 255
            wash_color = self._get_wash_color_for_alternation(music_info, i)
            states[light_id] = {
                'r': int(wash_color['r'] * (0.8 + smooth_build * 0.2)),
                'g': int(wash_color['g'] * (0.8 + smooth_build * 0.2)),
                'b': int(wash_color['b'] * (0.8 + smooth_build * 0.2)),
                'intensity': intensity
            }
        
        # PAR lights with very strong presence, high reactivity, and dramatic beat pulsing
        for i, light_id in enumerate(self.light_groups['par']):
            base_intensity = int(80 + smooth_build * 120)  # Build from 80% to 200% - very bright
            intensity = min(255, int(base_intensity * energy_boost * beat_boost))
            
            # Apply appropriate pulsing based on reactivity mode
            current_song = music_info.get('song_config', {})
            reactivity_mode = current_song.get('reactivity_mode', 'medium')
            
            if reactivity_mode == 'very_reactive':
                intensity = self._apply_beat_pulse(intensity, light_id, lights_config)
            elif reactivity_mode == 'easy':
                # Use slow fade system for easy mode
                intensity = self._apply_par_slow_fade(intensity, light_id, music_info)
            
            states[light_id] = {
                'r': int(color['r'] * (0.7 + smooth_build * 0.3)),
                'g': int(color['g'] * (0.7 + smooth_build * 0.3)),
                'b': int(color['b'] * (0.7 + smooth_build * 0.3)),
                'intensity': intensity
            }
        
        # Accent lights with energy reactivity
        for light_id in self.light_groups['accent']:
            base_intensity = int(smooth_build * 80)
            intensity = min(255, int(base_intensity * energy_boost * beat_boost))
            states[light_id] = {
                'r': int(color['r'] * smooth_build * 0.8),
                'g': int(color['g'] * smooth_build * 0.8),
                'b': int(color['b'] * smooth_build * 0.8),
                'intensity': intensity
            }
            
        return states

    def _effect_gentle_ambient(self, music_info: dict, lights_config: dict) -> Dict[str, Dict[str, int]]:
        """Gentle breathing ambient effect for very low energy"""
        current_time = time.time()
        
        # Get music data for subtle reactivity even in ambient mode
        energy = music_info.get('current_level', 0.3)  # Default to low energy for ambient
        beat_detected = music_info.get('beat_detected', False)
        
        # Breathing effect with subtle music influence
        breathe_speed = 0.785 + energy * 0.3  # Slightly faster breathing with energy
        breathe_cycle = math.sin(current_time * breathe_speed) * 0.5 + 0.5
        breathe_smooth = self._ease_in_out(breathe_cycle)
        
        # Subtle energy boost even in ambient
        energy_factor = 1.0 + energy * 0.3  # 1.0 to 1.3x boost
        beat_factor = 1.1 if beat_detected else 1.0  # Very subtle beat response
        
        states = {}
        color = music_info.get('frame_color', self.color_engine.get_color_for_music(music_info))
        
        # Wash lights - brighter base for gentle ambient with smooth alternating beat pulsing
        wash_base = int(40 + breathe_smooth * 40)  # 40 to 80 intensity
        base_wash_intensity = 255  # Maximum brightness for wash lights
        
        # Apply smooth alternating beat pulsing to wash lights with color alternation
        for i, light_id in enumerate(self.light_groups['wash']):
            wash_intensity = self._apply_wash_pulse_with_reactivity(base_wash_intensity, light_id, lights_config, music_info)
            wash_color = self._get_wash_color_for_alternation(music_info, i)
            states[light_id] = {
                'r': int(wash_color['r'] * 0.6),  # Brighter ambient colors
                'g': int(wash_color['g'] * 0.7),
                'b': int(wash_color['b'] * 0.5),
                'intensity': wash_intensity
            }
        
        # PAR lights - visible presence even in ambient mode with subtle beat pulsing
        par_base = int(40 + breathe_smooth * 60)  # 40 to 100 intensity
        base_par_intensity = min(255, int(par_base * energy_factor * beat_factor))
        
        # Apply appropriate pulsing even in ambient mode
        for i, light_id in enumerate(self.light_groups['par']):
            current_song = music_info.get('song_config', {})
            reactivity_mode = current_song.get('reactivity_mode', 'medium')
            
            if reactivity_mode == 'very_reactive':
                # Very reactive mode uses direct beat pulse for maximum responsiveness
                par_intensity = self._apply_beat_pulse(base_par_intensity, light_id, lights_config)
            elif reactivity_mode in ['easy', 'medium']:
                # Easy/medium modes use slow fade system for smoother transitions
                par_intensity = self._apply_par_slow_fade(base_par_intensity, light_id, music_info)
            else:
                # Fallback to old beat pulse system for any other modes
                par_intensity = self._apply_beat_pulse(base_par_intensity, light_id, lights_config)
            states[light_id] = {
                'r': int(color['r'] * 0.4),  # Visible PAR presence
                'g': int(color['g'] * 0.5),
                'b': int(color['b'] * 0.3), 
                'intensity': par_intensity
            }
            
        # Keep accent lights off for gentle effect
        for light_id in self.light_groups['accent']:
            states[light_id] = {'r': 0, 'g': 0, 'b': 0, 'intensity': 0}
            
        return states

    def _effect_soft_pulse(self, music_info: dict, lights_config: dict) -> Dict[str, Dict[str, int]]:
        """Soft pulsing effect for low energy"""
        current_time = time.time()
        
        # Get music reactivity data
        energy = music_info.get('current_level', 0.4)  # Default to low-medium energy
        beat_detected = music_info.get('beat_detected', False)
        
        # Music-reactive soft pulse speed
        pulse_speed = 1.57 + energy * 1.0  # Faster with more energy
        pulse_cycle = math.sin(current_time * pulse_speed) * 0.5 + 0.5
        pulse_smooth = self._ease_in_out(pulse_cycle)
        
        # Energy responsiveness
        energy_factor = 1.0 + energy * 0.6  # 1.0 to 1.6x boost
        beat_factor = 1.3 if beat_detected else 1.0
        
        states = {}
        color = music_info.get('frame_color', self.color_engine.get_color_for_music(music_info))
        
        # Wash lights - brighter soft pulsing with smooth alternating beat pulsing
        wash_base = int(80 + pulse_smooth * 120)  # 80 to 200 intensity
        base_wash_intensity = 255  # Maximum brightness for wash lights
        
        # Apply smooth alternating beat pulsing to wash lights with color alternation
        for i, light_id in enumerate(self.light_groups['wash']):
            wash_intensity = self._apply_wash_pulse_with_reactivity(base_wash_intensity, light_id, lights_config, music_info)
            wash_color = self._get_wash_color_for_alternation(music_info, i)
            states[light_id] = {
                'r': int(wash_color['r'] * (0.7 + pulse_smooth * 0.3)),
                'g': int(wash_color['g'] * (0.7 + pulse_smooth * 0.3)),
                'b': int(wash_color['b'] * (0.7 + pulse_smooth * 0.3)),
                'intensity': wash_intensity
            }
        
        # PAR lights - prominent presence in soft pulse with dramatic beat pulsing
        par_base = int(80 + pulse_smooth * 120)  # 80 to 200 intensity  
        base_par_intensity = min(255, int(par_base * energy_factor * beat_factor))
        
        # Apply appropriate pulsing with individual variation
        for i, light_id in enumerate(self.light_groups['par']):
            current_song = music_info.get('song_config', {})
            reactivity_mode = current_song.get('reactivity_mode', 'medium')
            
            if reactivity_mode == 'very_reactive':
                # Very reactive mode uses direct beat pulse for maximum responsiveness
                par_intensity = self._apply_beat_pulse(base_par_intensity, light_id, lights_config)
            elif reactivity_mode in ['easy', 'medium']:
                # Easy/medium modes use slow fade system for smoother transitions
                par_intensity = self._apply_par_slow_fade(base_par_intensity, light_id, music_info)
            else:
                # Fallback to old beat pulse system for any other modes
                par_intensity = self._apply_beat_pulse(base_par_intensity, light_id, lights_config)
            states[light_id] = {
                'r': int(color['r'] * (0.6 + pulse_smooth * 0.4)),
                'g': int(color['g'] * (0.6 + pulse_smooth * 0.4)),
                'b': int(color['b'] * (0.6 + pulse_smooth * 0.4)),
                'intensity': par_intensity
            }
        
        # Accent lights with energy reactivity
        accent_base = int(30 + pulse_smooth * 50)
        accent_intensity = min(255, int(accent_base * energy_factor * beat_factor))
        for light_id in self.light_groups['accent']:
            states[light_id] = {
                'r': int(color['r'] * pulse_smooth * 0.6),
                'g': int(color['g'] * pulse_smooth * 0.7),
                'b': int(color['b'] * pulse_smooth * 0.5),
                'intensity': accent_intensity
            }
            
        return states
    
    def _ease_in_out(self, t: float) -> float:
        """Smooth easing function for natural transitions"""
        if t < 0.5:
            return 2 * t * t
        return 1 - 2 * (1 - t) * (1 - t)
    
    def _ease_out_quad(self, t: float) -> float:
        """Ease-out quadratic function for smooth, fast fade endings"""
        return 1 - (1 - t) * (1 - t)
    
    def _smooth_step_curve(self, t: float) -> float:
        """Ultra-smooth S-curve for very gradual PAR fades (smoothstep function)"""
        # Clamp t to [0, 1]
        t = max(0.0, min(1.0, t))
        # 3t² - 2t³ smoothstep formula for ultra-smooth transitions
        return t * t * (3.0 - 2.0 * t)


def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[float, float, float]:
    """Convert HSV color space to RGB. All values 0.0-1.0"""
    if s == 0.0:
        return v, v, v
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    if i == 5:
        return v, p, q
