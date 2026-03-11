"""
Video Controls Widget for DMX Light Show Controller
Handles all video playback UI and functionality
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from .base_ui import BaseUIComponent, LoggingMixin, FormHelper


class VideoControlsWidget(BaseUIComponent, LoggingMixin):
    """Widget for video playback controls"""
    
    def __init__(self, parent, controllers=None, song_combo=None):
        self.song_combo = song_combo  # Reference to song selection combo
        # Initialize logging mixin
        self.info_display = None
        self.status_display = None
        super().__init__(parent, controllers)
    
    def setup_ui(self):
        """Setup video controls UI"""
        self.frame = ttk.Frame(self.parent)
        
        # Video control buttons frame
        control_frame = ttk.Frame(self.frame)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(control_frame, text="Video Control:").grid(row=0, column=0, sticky=tk.W)
        
        # Button frame
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E))
        
        # Video control buttons
        self.play_btn = ttk.Button(button_frame, text="Play Video", command=self.play_video)
        self.play_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop Video", command=self.stop_video)
        self.stop_btn.grid(row=0, column=1, padx=(0, 5))
        
        self.pause_btn = ttk.Button(button_frame, text="Pause Video", command=self.pause_video)
        self.pause_btn.grid(row=0, column=2, padx=(0, 5))
        
        self.resume_btn = ttk.Button(button_frame, text="Resume Video", command=self.resume_video)
        self.resume_btn.grid(row=0, column=3)
        
        control_frame.columnconfigure(1, weight=1)
    
    def play_video(self):
        """Play video for selected song"""
        if not self.song_combo:
            messagebox.showerror("Error", "No song selection available")
            return
            
        selected_song = self.song_combo.get()
        if not selected_song:
            messagebox.showwarning("Warning", "Please select a song first")
            return
        
        config_manager = self.get_controller('config_manager')
        video_controller = self.get_controller('video_controller')
        
        if not config_manager or not video_controller:
            messagebox.showerror("Error", "Controllers not available")
            return
            
        song_config = config_manager.get_song_config(selected_song)
        if not song_config:
            messagebox.showerror("Error", f"Song '{selected_song}' not found")
            return
            
        video_path = song_config.get('video_path', '')
        if not video_path:
            messagebox.showinfo("Info", f"No video configured for '{selected_song}'")
            return
            
        if not os.path.exists(video_path):
            messagebox.showerror("Error", f"Video file not found: {video_path}")
            return
            
        # Play video with the ffplay-backed video controller.
        if video_controller.play_video(video_path):
            self.log_info(f"Started video: {os.path.basename(video_path)}")
        else:
            self.log_error(f"Failed to start video: {os.path.basename(video_path)}")
    
    def stop_video(self):
        """Stop video playback"""
        video_controller = self.get_controller('video_controller')
        if video_controller:
            video_controller.stop()
            self.log_info("Video stopped")
    
    def pause_video(self):
        """Pause video playback"""
        video_controller = self.get_controller('video_controller')
        if video_controller:
            video_controller.pause()
            self.log_info("Video paused")
    
    def resume_video(self):
        """Resume video playback"""
        video_controller = self.get_controller('video_controller')
        if video_controller:
            video_controller.resume()
            self.log_info("Video resumed")


class VideoPathWidget(BaseUIComponent):
    """Widget for video path selection in song configuration"""
    
    def __init__(self, parent, video_var, controllers=None):
        self.video_var = video_var
        super().__init__(parent, controllers)
    
    def setup_ui(self):
        """Setup video path selection UI"""
        self.frame = ttk.Frame(self.parent)
        
        ttk.Label(self.frame, text="Video Path:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        video_frame = ttk.Frame(self.frame)
        video_frame.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E), pady=2)
        
        # Entry for video path
        self.path_entry = ttk.Entry(video_frame, textvariable=self.video_var, width=25)
        self.path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Browse button
        self.browse_btn = ttk.Button(video_frame, text="Browse", command=self.browse_video_file)
        self.browse_btn.grid(row=0, column=1, padx=(5, 0))
        
        video_frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
    
    def browse_video_file(self):
        """Browse for video file"""
        filetypes = [
            ('Video files', '*.mp4 *.mov *.avi *.mkv *.wmv *.flv *.webm *.m4v'),
            ('All files', '*.*')
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=filetypes
        )
        
        if filename:
            self.video_var.set(filename)
    
    def get_path(self):
        """Get the current video path"""
        return self.video_var.get()
    
    def set_path(self, path):
        """Set the video path"""
        self.video_var.set(path)
    
    def clear_path(self):
        """Clear the video path"""
        self.video_var.set("")


class VideoManagerWidget(BaseUIComponent, LoggingMixin):
    """Combined widget for video management in different contexts"""
    
    def __init__(self, parent, controllers=None, mode="playback"):
        self.mode = mode  # "playback" or "configuration"
        super().__init__(parent, controllers)
    
    def setup_ui(self):
        """Setup UI based on mode"""
        self.frame = ttk.LabelFrame(self.parent, text="Video Controls", padding="10")
        
        if self.mode == "playback":
            self._setup_playback_ui()
        elif self.mode == "configuration":
            self._setup_configuration_ui()
    
    def _setup_playback_ui(self):
        """Setup playback controls"""
        # Current video display
        self.current_video_var = tk.StringVar(value="No video loaded")
        ttk.Label(self.frame, text="Current Video:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(self.frame, textvariable=self.current_video_var, 
                 font=('SF Mono', 10)).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Control buttons
        button_config = [
            ("Play", self.play_video),
            ("Stop", self.stop_video),
            ("Pause", self.pause_video),
            ("Resume", self.resume_video)
        ]
        
        FormHelper.create_button_frame(self.frame, 1, button_config)
        
        # Volume control
        self.volume_var = tk.IntVar(value=50)
        ttk.Label(self.frame, text="Volume:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        
        volume_frame = ttk.Frame(self.frame)
        volume_frame.grid(row=2, column=1, padx=(10, 0), sticky=(tk.W, tk.E), pady=(10, 0))
        
        volume_scale = ttk.Scale(volume_frame, from_=0, to=100, variable=self.volume_var,
                               orient=tk.HORIZONTAL, command=self.on_volume_change)
        volume_scale.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.volume_label = ttk.Label(volume_frame, text="50")
        self.volume_label.grid(row=0, column=1, padx=(10, 0))
        
        volume_frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
    
    def _setup_configuration_ui(self):
        """Setup configuration controls"""
        # Video path selection
        self.video_var = tk.StringVar()
        self.video_path_widget = VideoPathWidget(self.frame, self.video_var, self.controllers)
        self.video_path_widget.get_frame().grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Preview controls
        button_config = [
            ("Preview Video", self.preview_video),
            ("Clear Path", self.clear_video_path)
        ]
        
        FormHelper.create_button_frame(self.frame, 1, button_config)
        
        self.frame.columnconfigure(0, weight=1)
    
    def play_video(self):
        """Play current video"""
        video_controller = self.get_controller('video_controller')
        if video_controller and hasattr(self, 'current_video_path'):
            if video_controller.play_video(self.current_video_path):
                self.log_info(f"Started video: {os.path.basename(self.current_video_path)}")
            else:
                self.log_error("Failed to start video")
    
    def stop_video(self):
        """Stop video playback"""
        video_controller = self.get_controller('video_controller')
        if video_controller:
            video_controller.stop()
            self.log_info("Video stopped")
    
    def pause_video(self):
        """Pause video playback"""
        video_controller = self.get_controller('video_controller')
        if video_controller:
            video_controller.pause()
            self.log_info("Video paused")
    
    def resume_video(self):
        """Resume video playback"""
        video_controller = self.get_controller('video_controller')
        if video_controller:
            video_controller.resume()
            self.log_info("Video resumed")
    
    def preview_video(self):
        """Preview selected video"""
        if hasattr(self, 'video_var'):
            video_path = self.video_var.get()
            if video_path and os.path.exists(video_path):
                video_controller = self.get_controller('video_controller')
                if video_controller:
                    video_controller.play_video(video_path)
                    self.log_info(f"Previewing: {os.path.basename(video_path)}")
            else:
                messagebox.showwarning("Warning", "Please select a valid video file first")
    
    def clear_video_path(self):
        """Clear video path"""
        if hasattr(self, 'video_var'):
            self.video_var.set("")
    
    def on_volume_change(self, value):
        """Handle volume change"""
        volume = int(float(value))
        self.volume_label.config(text=str(volume))
        
        video_controller = self.get_controller('video_controller')
        if video_controller:
            video_controller.set_volume(volume)
    
    def set_current_video(self, video_path):
        """Set the current video path"""
        self.current_video_path = video_path
        if hasattr(self, 'current_video_var'):
            display_name = os.path.basename(video_path) if video_path else "No video loaded"
            self.current_video_var.set(display_name)
