import random
import time
import math
from typing import Dict, List, Tuple, Optional, Any
from colorsys import hsv_to_rgb

class ColorEngine:
    """Intelligent color palette engine for dynamic light shows"""
    
    def __init__(self):
        # Color state
        self.current_palette = "warm"
        self.favorite_color = "blue"
        self.palette_change_time = 0
        self.palette_duration = 120.0  # Much longer duration for stable colors (2 minutes)
        
        # Color animation state
        self.color_cycle_position = 0.0
        
        # Song color usage - normal balanced percentage
        self.song_color_usage_chance = 0.65  # 65% usage for good balance with palette variety
        self.song_color_chance_time = 0
        self.song_color_chance_duration = 180.0  # Change song color usage chance every 3 minutes
        
        # Secondary color switching - alternate between primary and secondary based on tempo
        self.secondary_color_switch_time = 0
        self.base_switch_duration = 2.2  # Medium mode base duration for responsive color changes
        self.current_switch_duration = 2.2  # Actual duration (adjusted by tempo)
        self.use_secondary_color = False  # Track current preference
        
        # Color caching to avoid redundant calculations and light updates
        self.last_returned_color = None
        self.last_color_context = None  # Track context that affects color selection
        self.color_change_time = time.time()
        self.same_color_count = 0
        
        # Frame counter for debug logging
        self.frame_count = 0
        
        # Define color palettes
        self.palettes = {
            'complementary': {
                'description': 'Complementary colors to favorite',
                'colors': self._get_complementary_palette(),
            },
            'warm': {
                'description': 'Warm colors (reds, oranges, yellows)',
                'colors': [(255, 50, 20), (255, 140, 0), (255, 200, 50), (200, 100, 30)],
            },
            'cool': {
                'description': 'Cool colors (blues, greens, purples)',
                'colors': [(20, 100, 255), (50, 255, 150), (150, 50, 255), (0, 200, 200)],
            },
            'rainbow': {
                'description': 'Full spectrum cycling',
                'colors': self._get_rainbow_colors(),
            },
        }
        
    def _get_complementary_palette(self) -> List[Tuple[int, int, int]]:
        """Get colors complementary to favorite color"""
        base_color = self._color_name_to_rgb(self.favorite_color)
        comp_color = self._get_complementary_color(base_color)
        
        return [
            base_color,
            comp_color,
            self._blend_colors(base_color, comp_color, 0.3),
            self._blend_colors(base_color, comp_color, 0.7),
            (255, 255, 255),  # White for accent
            (200, 200, 200)   # Light gray
        ]
        
    def _get_rainbow_colors(self) -> List[Tuple[int, int, int]]:
        """Get rainbow spectrum colors"""
        colors = []
        for hue in [0, 60, 120, 180, 240, 300]:  # Red, Yellow, Green, Cyan, Blue, Magenta
            r, g, b = hsv_to_rgb(hue/360.0, 1.0, 1.0)
            colors.append((int(r * 255), int(g * 255), int(b * 255)))
        return colors
    
    def get_color_usage_stats(self) -> Dict[str, Any]:
        """Get statistics about color usage and caching efficiency"""
        return {
            'song_color_usage_chance': f"{self.song_color_usage_chance:.0%}",
            'current_palette': self.current_palette,
            'use_secondary_color': self.use_secondary_color,
            'cache_efficiency': f"{self.same_color_count} consecutive cached returns",
            'time_since_color_change': f"{time.time() - self.color_change_time:.1f}s ago"
        }
        
    def _color_name_to_rgb(self, color_name: str) -> Tuple[int, int, int]:
        """Convert color name to RGB"""
        colors = {
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'purple': (128, 0, 128),
            'yellow': (255, 255, 0),
            'orange': (255, 165, 0),
            'pink': (255, 192, 203),
            'white': (255, 255, 255)
        }
        return colors.get(color_name.lower(), (255, 255, 255))
        
    def _get_complementary_color(self, rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Get complementary color"""
        r, g, b = rgb
        return (255 - r, 255 - g, 255 - b)
        
    def _blend_colors(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int], ratio: float) -> Tuple[int, int, int]:
        """Blend two colors with given ratio"""
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        
        return (
            int(r1 * (1 - ratio) + r2 * ratio),
            int(g1 * (1 - ratio) + g2 * ratio),
            int(b1 * (1 - ratio) + b2 * ratio)
        )
        
    def set_favorite_color(self, color: str):
        """Set favorite color and regenerate palettes"""
        self.favorite_color = color
        self.palettes['complementary']['colors'] = self._get_complementary_palette()
        
    def choose_palette_for_music(self, music_info: dict) -> str:
        """Choose color palette based on music characteristics"""
        energy = music_info.get('current_level', 0.5)
        is_quiet = music_info.get('is_quiet', False)

        if is_quiet or energy < 0.3:
            return 'cool'
        elif energy > 0.7:
            return 'warm'
        else:
            return random.choice(['complementary', 'rainbow'])

    def get_color_for_music(self, music_info: dict, light_id: str = None) -> Dict[str, int]:
        """Get color based on music analysis with proper variety"""
        # If a frame color is already set, use it consistently for this frame
        if 'frame_color' in music_info:
            return music_info['frame_color']
            
        current_time = time.time()
        self.frame_count += 1  # Increment frame counter for debug logging
        
        # Create context for color caching - factors that affect color selection
        color_context = {
            'song_color': music_info.get('song_color'),
            'song_secondary_color': music_info.get('song_secondary_color'),
            'use_secondary': self.use_secondary_color,
            'current_palette': self.current_palette,
            'favorite_color': self.favorite_color
        }
        
        # Check if color context changed or enough time passed for potential color change
        context_changed = self.last_color_context != color_context
        time_for_change = (current_time - self.color_change_time) > 0.5  # Allow changes every 500ms
        
        # If context is same and we recently returned a color, return cached color
        if not context_changed and self.last_returned_color is not None and not time_for_change:
            self.same_color_count += 1
            # Only log excessive same color usage occasionally to track efficiency
            if self.same_color_count > 0 and self.same_color_count % 100 == 0:
                print(f"🔄 Color cache: returned same color {self.same_color_count} times")
            return self.last_returned_color

        # Adjust palette change frequency based on reactivity mode
        reactivity_mode = music_info.get('reactivity_mode', 'medium')
        if reactivity_mode == 'easy':
            palette_duration = self.palette_duration  # 2 minutes (default)
        elif reactivity_mode == 'medium':
            palette_duration = self.palette_duration * 0.7  # 1.4 minutes (more changes)
        else:  # very_reactive
            palette_duration = self.palette_duration * 0.4  # 48 seconds (frequent changes)
            
        if current_time - self.palette_change_time > palette_duration:
            old_palette = self.current_palette
            suggested_palette = self.choose_palette_for_music(music_info)
            
            # Only change palette if no song colors are configured
            song_color = music_info.get('song_color')
            if not song_color or song_color == 'auto':
                self.current_palette = suggested_palette
                self.palette_change_time = current_time
                
                # Log palette changes
                if old_palette != self.current_palette:
                    print(f"Palette changed: {old_palette} → {self.current_palette} ({reactivity_mode} mode)")
            else:
                print(f"Keeping palette {self.current_palette} - song colors configured ({song_color})")

        # Check if song has custom random color percentage setting
        current_song = music_info.get('song_config', {})
        custom_random_percentage = current_song.get('random_color_percentage', None)
        
        if custom_random_percentage is not None:
            # Use custom per-song setting (convert from random percentage to song color percentage)
            # If random_color_percentage is 30%, then song_color_usage_chance should be 70%
            old_chance = self.song_color_usage_chance
            self.song_color_usage_chance = (100 - custom_random_percentage) / 100.0
            
            # Show immediate feedback when settings change
            if abs(old_chance - self.song_color_usage_chance) > 0.05:  # Significant change
                print(f"RANDOM COLOR % ACTIVE: {custom_random_percentage}% random colors, {self.song_color_usage_chance:.0%} song colors")
            
            # Show this more frequently so user can see the effect
            if current_time - self.song_color_chance_time > 30.0:  # Every 30 seconds instead of 3 minutes
                print(f"RANDOM COLOR %: {custom_random_percentage}% random colors, {self.song_color_usage_chance:.0%} song colors")
                self.song_color_chance_time = current_time
        else:
            # Use automatic reactivity-based color chance
            if current_time - self.song_color_chance_time > self.song_color_chance_duration:
                old_chance = self.song_color_usage_chance
                
                # Get reactivity mode from music info
                reactivity_mode = music_info.get('reactivity_mode', 'medium')
                
                if reactivity_mode == 'easy':
                    # Easy mode: higher chance for song colors (more predictable)
                    self.song_color_usage_chance = random.uniform(0.6, 0.85)  # 60-85%
                elif reactivity_mode == 'medium':
                    # Medium mode: moderate chance, more variety 
                    self.song_color_usage_chance = random.uniform(0.4, 0.7)   # 40-70%
                else:  # very_reactive or high reactivity
                    # High reactivity: lower chance for song colors, more randomness
                    self.song_color_usage_chance = random.uniform(0.25, 0.55)  # 25-55%
                    
                self.song_color_chance_time = current_time
                if abs(old_chance - self.song_color_usage_chance) > 0.1:  # Only log significant changes
                    print(f"🎨 {reactivity_mode} mode: {self.song_color_usage_chance:.0%} chance for song colors")

        # Adjust switch duration based on tempo - much slower across all tempos for calmer shows
        tempo = music_info.get('tempo', 120)
        if tempo < 80:
            # Very slow music - longer duration
            self.current_switch_duration = self.base_switch_duration * 1.8  # ~4.0 seconds
        elif tempo < 100:
            # Slow music - moderately longer duration
            self.current_switch_duration = self.base_switch_duration * 1.4  # ~3.1 seconds
        elif tempo < 140:
            # Medium tempo - base duration (as documented: 2.2s for medium mode)
            self.current_switch_duration = self.base_switch_duration  # 2.2 seconds
        else:
            # Fast tempo - shorter for more responsive changes
            self.current_switch_duration = self.base_switch_duration * 0.7  # ~1.5 seconds

        # Update secondary color switching based on tempo-adjusted duration
        if current_time - self.secondary_color_switch_time > self.current_switch_duration:
            self.use_secondary_color = not self.use_secondary_color  # Toggle
            self.secondary_color_switch_time = current_time
            # Log the switch with tempo info
            song_color = music_info.get('song_color')
            secondary_color = music_info.get('song_secondary_color')
            preferred_color = secondary_color if self.use_secondary_color else song_color
            print(f"Color switching: now preferring {preferred_color} (tempo: {tempo}bpm, duration: {self.current_switch_duration:.0f}s)")

        # Color selection priority:
        # 1. Random 33-66% chance to use song config color (if available)
        # 2. 15% chance to use the favorite color  
        # 3. Otherwise use current palette
        
        random_choice = random.random()
        
        # Removed excessive debug path logging
        
        # Check for song config color first (using persistent chance)
        if random_choice < self.song_color_usage_chance:
            song_color = music_info.get('song_color')
            secondary_color = music_info.get('song_secondary_color')
            
            # Show when song colors are being used (occasionally)
            if self.frame_count % 120 == 0:  # Every 2 seconds
                color_choice = secondary_color if (secondary_color and secondary_color != 'none' and self.use_secondary_color) else song_color
                print(f"COLOR CHOICE: Using SONG color '{color_choice}' (roll {random_choice:.2f} < {self.song_color_usage_chance:.2f})")
            
            if song_color and song_color != 'auto':
                # Determine which color to use based on time-based preference and availability
                if secondary_color and secondary_color != 'none' and self.use_secondary_color:
                    # Use secondary color when it's available and preferred
                    color_tuple = self._color_name_to_rgb(secondary_color)
                    # Color selection visible in DMX simulator - no logging needed
                    result_color = {'r': color_tuple[0], 'g': color_tuple[1], 'b': color_tuple[2]}
                    self.last_returned_color = result_color
                    self.last_color_context = color_context
                    self.color_change_time = current_time
                    self.same_color_count = 0
                    return result_color
                else:
                    # Use primary song color (either no secondary color or primary is preferred)
                    color_tuple = self._color_name_to_rgb(song_color)
                    # Color selection visible in DMX simulator - no logging needed
                    result_color = {'r': color_tuple[0], 'g': color_tuple[1], 'b': color_tuple[2]}
                    self.last_returned_color = result_color
                    self.last_color_context = color_context
                    self.color_change_time = current_time
                    self.same_color_count = 0
                    return result_color
        
        # 15% chance to use the favorite color (after song color chance)
        if random_choice < self.song_color_usage_chance + 0.15:
            color_tuple = self._color_name_to_rgb(self.favorite_color)
            if self.frame_count % 120 == 0:  # Every 2 seconds
                print(f"COLOR CHOICE: Using FAVORITE color '{self.favorite_color}' (roll {random_choice:.2f})")
        else:
            # Use random palette color
            palette = self.palettes[self.current_palette]['colors']
            color_tuple = random.choice(palette)
            if self.frame_count % 120 == 0:  # Every 2 seconds
                print(f"COLOR CHOICE: Using RANDOM palette '{self.current_palette}' color {color_tuple} (roll {random_choice:.2f})")

        # Cache the result and update context
        result_color = {'r': color_tuple[0], 'g': color_tuple[1], 'b': color_tuple[2]}
        self.last_returned_color = result_color
        self.last_color_context = color_context
        self.color_change_time = current_time
        self.same_color_count = 0  # Reset counter when we compute a new color
        
        return result_color