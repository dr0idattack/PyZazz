import tkinter as tk
import random
import math
import numpy as np
import colorsys
import time

class PsychedelicVisualizer:
    def __init__(self, root, audio_analyzer, color_engine, display_number=2):
        self.root = root
        self.audio_analyzer = audio_analyzer
        self.color_engine = color_engine

        import tkinter as tk
        import random
        import math
        import numpy as np
        import colorsys
        import time


        class PsychedelicVisualizer:
            def __init__(self, root, audio_analyzer, color_engine, display_number=2):
                self.root = root
                self.audio_analyzer = audio_analyzer
                self.color_engine = color_engine

                self.screen_width = root.winfo_screenwidth()
                self.screen_height = root.winfo_screenheight()

                self.window = tk.Toplevel(root)
                self.window.title("Psychedelic Visualizer")

                # Move to the specified display using proper multi-display detection
                geometry = self._get_display_geometry(display_number)
                if geometry:
                    self.window.geometry(geometry)
                else:
                    self.window.geometry(f"{self.screen_width}x{self.screen_height}+0+0")

                # Update and verify positioning
                self.window.update_idletasks()
                actual_x = self.window.winfo_x()
                if actual_x > self.screen_width:
                    print(f"✅ Psychedelic visualizer on external display")
                else:
                    print(f"❌ Psychedelic visualizer on primary display")

                self.window.attributes("-fullscreen", True)
                self.canvas = tk.Canvas(self.window, bg='black', highlightthickness=0)
                self.canvas.pack(fill=tk.BOTH, expand=True)

                self.modes = ['waveform', 'particles', 'tunnel', 'mandala']
                self.current_mode_index = 0
                self.current_mode = self.modes[self.current_mode_index]

                self.particles = []
                self.running = False

                self.window.bind("<Escape>", self.stop)
                self.window.bind("<space>", self.switch_mode)

            def start(self):
                self.running = True
                self.animate()

            def stop(self, event=None):
                self.running = False
                self.window.destroy()

            def switch_mode(self, event=None):
                self.current_mode_index = (self.current_mode_index + 1) % len(self.modes)
                self.current_mode = self.modes[self.current_mode_index]
                self.canvas.delete("all")
                self.particles = []

            def animate(self):
                if not self.running:
                    return

                self.canvas.delete("all")
                audio_level = self.audio_analyzer.get_audio_level()
                beat_detected = self.audio_analyzer.detect_beat()
                primary_color, secondary_color = self.color_engine.get_current_colors()

                if self.current_mode == 'waveform':
                    self.draw_waveform(audio_level, beat_detected, primary_color, secondary_color)
                elif self.current_mode == 'particles':
                    self.draw_particles(audio_level, beat_detected, primary_color, secondary_color)
                elif self.current_mode == 'tunnel':
                    self.draw_tunnel(audio_level, beat_detected, primary_color, secondary_color)
                elif self.current_mode == 'mandala':
                    self.draw_mandala(audio_level, beat_detected, primary_color, secondary_color)

                # show callback->UI age (ms) if analyzer supports it
                try:
                    age = self.audio_analyzer.get_last_callback_age()
                    if age is not None:
                        ms = int(age * 1000)
                        self.canvas.create_text(12, 12, anchor='nw', fill='white', text=f"latency: {ms} ms", font=('Arial', 14, 'bold'))
                except Exception:
                    pass

                # poll slightly faster for more responsive visuals (8 ms)
                self.root.after(8, self.animate)

            def draw_waveform(self, audio_level, beat_detected, primary_color, secondary_color):
                spectrum = self.audio_analyzer.get_frequency_spectrum()
                if spectrum is None:
                    return

                num_bars = 64
                bar_width = self.screen_width / num_bars
                max_height = self.screen_height * 0.8

                for i in range(num_bars):
                    # compute band energy safely
                    start = i * (len(spectrum) // num_bars)
                    end = (i + 1) * (len(spectrum) // num_bars)
                    band_energy = np.mean(spectrum[start:end]) if end > start else 0
                    height = min(max_height, band_energy * max_height * 0.1)
                    x1 = i * bar_width
                    y1 = self.screen_height / 2 - height / 2
                    x2 = x1 + bar_width
                    y2 = y1 + height

                    color = self.interpolate_color(primary_color, secondary_color, i / num_bars)
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

            def draw_particles(self, audio_level, beat_detected, primary_color, secondary_color):
                if beat_detected:
                    # spawn fewer particles for lower per-beat CPU
                    for _ in range(30):
                        self.particles.append(self.create_particle(primary_color, secondary_color))

                # Use list comprehension to avoid modifying list during iteration
                visible_particles = []
                for particle in self.particles:
                    self.move_particle(particle, audio_level)
                    if self.is_particle_visible(particle):
                        visible_particles.append(particle)
                self.particles = visible_particles

            def create_particle(self, primary_color, secondary_color):
                x = self.screen_width / 2
                y = self.screen_height / 2
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2, 10)
                size = random.uniform(2, 8)
                color = random.choice([primary_color, secondary_color])
                return {'x': x, 'y': y, 'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed, 'size': size, 'color': color}

            def move_particle(self, particle, audio_level):
                particle['x'] += particle['vx']
                particle['y'] += particle['vy']
                particle['vx'] *= 0.98
                particle['vy'] *= 0.98
                particle['vy'] += 0.1  # gravity
                self.canvas.create_oval(particle['x'], particle['y'], particle['x'] + particle['size'], particle['y'] + particle['size'], fill=particle['color'], outline="")

            def is_particle_visible(self, particle):
                return 0 < particle['x'] < self.screen_width and 0 < particle['y'] < self.screen_height

            def draw_tunnel(self, audio_level, beat_detected, primary_color, secondary_color):
                num_rings = 20
                center_x = self.screen_width / 2
                center_y = self.screen_height / 2
                max_radius = self.screen_width

                for i in range(num_rings):
                    radius = (i / num_rings) * max_radius * (1 + audio_level * 0.5)
                    angle = (i * 0.1) + time.time()
                    x = center_x + math.cos(angle) * 50
                    y = center_y + math.sin(angle) * 50

                    color = self.interpolate_color(primary_color, secondary_color, i / num_rings)

                    # Distort radius with a sine wave for a wobbly effect
                    wobble = math.sin(time.time() * 2 + i * 0.5) * 20 * audio_level
                    radius += wobble

                    self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline=color, width=2)

            def draw_mandala(self, audio_level, beat_detected, primary_color, secondary_color):
                center_x = self.screen_width / 2
                center_y = self.screen_height / 2
                num_segments = 12
                rotation_angle = time.time() * 0.5

                for i in range(num_segments):
                    angle = (i / num_segments) * 2 * math.pi + rotation_angle
                    radius = 100 + audio_level * 200

                    x1 = center_x + math.cos(angle) * radius
                    y1 = center_y + math.sin(angle) * radius

                    x2 = center_x + math.cos(angle + 0.1) * (radius + 50)
                    y2 = center_y + math.sin(angle + 0.1) * (radius + 50)

                    color = self.interpolate_color(primary_color, secondary_color, i / num_segments)
                    self.canvas.create_line(center_x, center_y, x1, y1, fill=color, width=2)
                    self.canvas.create_oval(x1 - 10, y1 - 10, x1 + 10, y1 + 10, fill=color, outline="")
                    self.canvas.create_line(x1, y1, x2, y2, fill=secondary_color, width=1)

            def interpolate_color(self, color1, color2, factor):
                r1, g1, b1 = self.root.winfo_rgb(color1)
                r2, g2, b2 = self.root.winfo_rgb(color2)
                r = int(r1 + (r2 - r1) * factor)
                g = int(g1 + (g2 - g1) * factor)
                b = int(b1 + (b2 - b1) * factor)
                return f"#{r:04x}{g:04x}{b:04x}"

            def _get_display_geometry(self, display_number: int):
                """Get geometry string for positioning window on specified display"""
                try:
                    import subprocess

                    # Use system_profiler to get display information
                    result = subprocess.run(['system_profiler', 'SPDisplaysDataType'],
                                            capture_output=True, text=True, timeout=5)

                    if result.returncode != 0:
                        print("Could not get display info, using fallback positioning")
                        return self._get_fallback_geometry(display_number)

                    # Count displays
                    display_count = result.stdout.count('Resolution:')
                    print(f"Detected {display_count} display(s)")

                    if display_number <= 1 or display_count <= 1:
                        # Use primary display
                        return None  # Let system handle primary display

                    # For secondary display, use a more robust positioning strategy
                    main_width = self.root.winfo_screenwidth()
                    main_height = self.root.winfo_screenheight()

                    # Position on secondary display (typically to the right)
                    secondary_x = main_width + 100  # Offset to ensure it's on secondary
                    secondary_y = 0

                    return f"{main_width}x{main_height}+{secondary_x}+{secondary_y}"

                except Exception as e:
                    print(f"Error detecting displays: {e}")
                    return self._get_fallback_geometry(display_number)

            def _get_fallback_geometry(self, display_number: int):
                """Fallback geometry positioning"""
                if display_number <= 1:
                    return None  # Primary display

                # Simple fallback: position to the right of primary display
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                return f"{screen_width}x{screen_height}+{screen_width}+0"


        if __name__ == '__main__':
            import time
            from audio_analyzer import AudioAnalyzer
            from color_engine import ColorEngine

            class MockAudioAnalyzer:
                def get_audio_level(self):
                    return abs(math.sin(time.time()))

                def detect_beat(self):
                    return time.time() % 1 < 0.1

                def get_frequency_spectrum(self):
                    return [random.randint(0, 1000) for _ in range(512)]

            class MockColorEngine:
                def get_current_colors(self):
                    return "red", "blue"

            root = tk.Tk()
            audio_analyzer = MockAudioAnalyzer()
            color_engine = MockColorEngine()
            app = PsychedelicVisualizer(root, audio_analyzer, color_engine)
            app.start()
            root.mainloop()