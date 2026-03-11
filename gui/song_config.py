"""
Song Configuration Widget for DMX Light Show Controller
Handles song creation, editing, and management
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from .base_ui import BaseUIComponent, LoggingMixin, FormHelper, TreeViewHelper, VariableManager
from .video_controls import VideoPathWidget


class SongConfigWidget(BaseUIComponent, LoggingMixin):
    """Widget for song configuration management"""
    
    def __init__(self, parent, controllers=None):
        self.variables = VariableManager()
        self.mic_sensitivity_var = None  # Initialize this first
        # Initialize logging mixin
        self.info_display = None
        self.status_display = None
        # Track original song name for editing detection
        self.original_song_name = None
        # Setup variables before calling super() which calls setup_ui()
        self._setup_variables()
        super().__init__(parent, controllers)
    
    def setup_ui(self):
        """Setup song configuration UI"""
        self.frame = ttk.Frame(self.parent, padding="10")
        
        # Create form and list sections
        self._create_song_form()
        self._create_songs_list()
        
        # Configure grid weights
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)
    
    def _setup_variables(self):
        """Setup tkinter variables for song configuration"""
        self.variables.add_string_var('song_name')
        self.variables.add_int_var('song_intensity', 128)
        self.variables.add_string_var('song_reactivity', 'medium')
        self.variables.add_double_var('song_mic_sensitivity', 0.3)
        self.variables.add_string_var('song_color', 'white')
        self.variables.add_string_var('song_secondary_color', 'none')
        self.variables.add_int_var('song_random_color_percentage', -1)  # -1 means use automatic based on reactivity mode
        self.variables.add_string_var('song_video')
        self.variables.add_string_var('song_visualization', 'none')
        self.variables.add_string_var('song_media_mode', 'video')  # 'video' or 'visualization'
        self.variables.add_string_var('song_notes')
    
    def _create_song_form(self):
        """Create song configuration form"""
        form_frame = ttk.LabelFrame(self.frame, text="Add/Edit Song", padding="10")
        form_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        config_manager = self.get_controller('config_manager')
        reactivity_options = config_manager.get_reactivity_options() if config_manager else ['low', 'medium', 'high']
        color_options = config_manager.get_color_options() if config_manager else ['white', 'red', 'green', 'blue']
        secondary_color_options = ['none'] + color_options  # Include 'none' option for optional secondary color
        
        # Row 0: Song name, reactivity mode, color bias (3 columns)
        ttk.Label(form_frame, text="Song Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        song_entry = ttk.Entry(form_frame, textvariable=self.variables.get_var('song_name'), width=20)
        song_entry.grid(row=0, column=1, padx=(5, 15), sticky=tk.W, pady=2)
        
        reactivity_frame = ttk.Frame(form_frame)
        reactivity_frame.grid(row=0, column=2, columnspan=2, sticky=tk.W, pady=2, padx=(20, 15))
        ttk.Label(reactivity_frame, text="Reactivity:").grid(row=0, column=0, sticky=tk.W)
        self._create_info_button(reactivity_frame, "How aggressively lights respond to music (low=smooth, medium=balanced, high=very reactive)", 0, 1)
        reactivity_combo = ttk.Combobox(reactivity_frame, textvariable=self.variables.get_var('song_reactivity'),
                                       values=reactivity_options, state="readonly", width=12)
        reactivity_combo.grid(row=0, column=2, padx=(5, 0), sticky=tk.W)
        
        color_frame = ttk.Frame(form_frame)
        color_frame.grid(row=0, column=4, columnspan=4, sticky=tk.W, pady=2)
        
        # Primary color
        ttk.Label(color_frame, text="Primary Color:").grid(row=0, column=0, sticky=tk.W)
        self._create_info_button(color_frame, "Primary color theme for this song (white=full spectrum, specific colors=biased toward that color)", 0, 1)
        color_combo = ttk.Combobox(color_frame, textvariable=self.variables.get_var('song_color'),
                                  values=color_options, state="readonly", width=10)
        color_combo.grid(row=0, column=2, padx=(5, 15), sticky=tk.W)
        
        # Secondary color
        ttk.Label(color_frame, text="Secondary:").grid(row=0, column=3, sticky=tk.W)
        self._create_info_button(color_frame, "Optional secondary color that will be randomly mixed in with primary color (none=disabled)", 0, 4)
        secondary_color_combo = ttk.Combobox(color_frame, textvariable=self.variables.get_var('song_secondary_color'),
                                           values=secondary_color_options, state="readonly", width=10)
        secondary_color_combo.grid(row=0, column=5, padx=(5, 15), sticky=tk.W)
        
        
        # Row 1: Intensity and mic sensitivity sliders with bounds and info tooltips
        intensity_frame = ttk.Frame(form_frame)
        intensity_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(intensity_frame, text="Intensity:").grid(row=0, column=0, sticky=tk.W)
        self._create_info_button(intensity_frame, "Overall brightness level for lights (0=off, 255=maximum)", 0, 1)
        ttk.Label(intensity_frame, text="0").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        intensity_scale = ttk.Scale(intensity_frame, from_=0, to=255, variable=self.variables.get_var('song_intensity'),
                                   orient=tk.HORIZONTAL, length=120)
        intensity_scale.grid(row=0, column=3, padx=5, sticky=(tk.W, tk.E))
        ttk.Label(intensity_frame, text="255").grid(row=0, column=4, sticky=tk.W, padx=(5, 10))
        intensity_value = ttk.Label(intensity_frame, textvariable=self.variables.get_var('song_intensity'), width=5, foreground="blue")
        intensity_value.grid(row=0, column=5, sticky=tk.W)
        
        mic_frame = ttk.Frame(form_frame)
        mic_frame.grid(row=1, column=4, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(mic_frame, text="Mic Sensitivity:").grid(row=0, column=0, sticky=tk.W)
        self._create_info_button(mic_frame, "How responsive to microphone input (0.1=very sensitive to quiet sounds, 1.0=only loud sounds)", 0, 1)
        ttk.Label(mic_frame, text="0.1").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        mic_scale = ttk.Scale(mic_frame, from_=0.1, to=1.0, variable=self.variables.get_var('song_mic_sensitivity'),
                             orient=tk.HORIZONTAL, length=80)
        mic_scale.grid(row=0, column=3, padx=5, sticky=(tk.W, tk.E))
        ttk.Label(mic_frame, text="1.0").grid(row=0, column=4, sticky=tk.W, padx=(5, 10))
        # Create formatted mic sensitivity display
        self.mic_sensitivity_var = tk.StringVar()
        self.variables.get_var('song_mic_sensitivity').trace('w', lambda *args: self._update_mic_display())
        self._update_mic_display()  # Call after creating the StringVar
        mic_value = ttk.Label(mic_frame, textvariable=self.mic_sensitivity_var, width=5, foreground="blue")
        mic_value.grid(row=0, column=5, sticky=tk.W)
        
        # Random color percentage next to mic sensitivity
        random_color_frame = ttk.Frame(form_frame)
        random_color_frame.grid(row=1, column=6, sticky=tk.W, pady=2, padx=(20, 0))
        
        ttk.Label(random_color_frame, text="Random %:").grid(row=0, column=0, sticky=tk.W)
        self._create_info_button(random_color_frame, "% random palette colors (0-100%, -1=auto)", 0, 1)
        random_color_spinbox = ttk.Spinbox(random_color_frame, textvariable=self.variables.get_var('song_random_color_percentage'),
                                         from_=-1, to=100, width=6, increment=5)
        random_color_spinbox.grid(row=0, column=2, padx=(5, 0), sticky=tk.W)
        
        # Configure column weights for responsive layout
        intensity_frame.columnconfigure(3, weight=1)
        mic_frame.columnconfigure(3, weight=1)
        
        # Row 2: Media Mode Toggle and Controls
        self._create_media_toggle_section(form_frame)
        
        # Row 4: Notes
        ttk.Label(form_frame, text="Notes:").grid(row=4, column=0, sticky=tk.W, pady=2)
        notes_entry = ttk.Entry(form_frame, textvariable=self.variables.get_var('song_notes'), width=50)
        notes_entry.grid(row=4, column=1, columnspan=5, padx=(5, 0), sticky=(tk.W, tk.E), pady=2)
        
        # Row 5: Action buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=6, pady=(10, 0))
        
        ttk.Button(button_frame, text="New Song", command=self.new_song).grid(
            row=0, column=0, padx=(0, 10)
        )
        ttk.Button(button_frame, text="Save Song", command=self.save_song).grid(
            row=0, column=1
        )
        
        # Configure column weights for responsive layout
        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1) 
        form_frame.columnconfigure(5, weight=1)
    
    def _create_media_toggle_section(self, parent):
        """Create the media mode toggle section with video or visualization controls"""
        # Main media frame
        media_frame = ttk.LabelFrame(parent, text="Media Settings", padding="5")
        media_frame.grid(row=2, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=5)
        
        # Toggle row
        toggle_frame = ttk.Frame(media_frame)
        toggle_frame.grid(row=0, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(toggle_frame, text="Media Type:").grid(row=0, column=0, sticky=tk.W)
        self._create_info_button(toggle_frame, "Choose between video file playback or built-in visualization modes", 0, 1)
        
        # Create toggle using radio buttons for clearer distinction
        video_radio = ttk.Radiobutton(toggle_frame, text="Video", variable=self.variables.get_var('song_media_mode'), 
                                     value="video", command=self._on_media_mode_change)
        video_radio.grid(row=0, column=2, padx=(10, 5), sticky=tk.W)
        
        viz_radio = ttk.Radiobutton(toggle_frame, text="Visualization", variable=self.variables.get_var('song_media_mode'), 
                                   value="visualization", command=self._on_media_mode_change)
        viz_radio.grid(row=0, column=3, padx=(5, 0), sticky=tk.W)
        
        # Video controls frame
        self.video_controls_frame = ttk.Frame(media_frame)
        self.video_controls_frame.grid(row=1, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=2)
        
        # Video path widget
        self.video_widget = VideoPathWidget(
            self.video_controls_frame, 
            self.variables.get_var('song_video'), 
            self.controllers
        )
        ttk.Label(self.video_controls_frame, text="Video Path:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.video_widget.get_frame().grid(row=0, column=1, columnspan=5, padx=(5, 0), sticky=(tk.W, tk.E), pady=2)
        
        # Visualization controls frame
        self.viz_controls_frame = ttk.Frame(media_frame)
        self.viz_controls_frame.grid(row=2, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(self.viz_controls_frame, text="Visualization Mode:").grid(row=0, column=0, sticky=tk.W)
        self._create_info_button(self.viz_controls_frame, "Fullscreen music visualization on extended display", 0, 1)
        
        visualization_options = ['psychedelic', 'hyperspace', 'bubbles', 'waveform', 'particles', 'spiral', 'wild', 'random']
        self.viz_combo = ttk.Combobox(self.viz_controls_frame, textvariable=self.variables.get_var('song_visualization'),
                                     values=visualization_options, state="readonly", width=12)
        self.viz_combo.grid(row=0, column=2, padx=(5, 0), sticky=tk.W)
        
        # Configure column weights
        media_frame.columnconfigure(1, weight=1)
        self.video_controls_frame.columnconfigure(1, weight=1)
        self.viz_controls_frame.columnconfigure(1, weight=1)
        
        # Initial state setup
        self._on_media_mode_change()
    
    def _on_media_mode_change(self):
        """Handle media mode toggle change"""
        mode = self.variables.get_value('song_media_mode')
        
        if mode == 'video':
            # Show video controls, hide visualization controls
            self.video_controls_frame.grid()
            self.viz_controls_frame.grid_remove()
        else:
            # Show visualization controls, hide video controls
            self.video_controls_frame.grid_remove()
            self.viz_controls_frame.grid()
    
    def _create_songs_list(self):
        """Create songs list with management controls"""
        list_frame = ttk.LabelFrame(self.frame, text="Existing Songs", padding="10")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Treeview for songs
        columns = ('Name', 'Intensity', 'Mode', 'Color', 'Secondary', 'Video', 'Visualization')
        self.songs_tree, scrollbar = TreeViewHelper.create_treeview_with_scrollbar(
            list_frame, columns, height=12  # Increased from 8 to 12 lines
        )
        
        self.songs_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Add double-click binding for editing
        self.songs_tree.bind('<Double-1>', self._on_double_click)
        
        # Management buttons
        button_config = [
            ("Edit Selected", self.edit_selected_song),
            ("Delete Selected", self.delete_selected_song)
        ]
        
        FormHelper.create_button_frame(list_frame, 1, button_config)
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Initialize songs list
        self.refresh_songs_list()
    
    def _create_info_button(self, parent, tooltip_text, row, column):
        """Create an info button with tooltip"""
        info_button = ttk.Label(parent, text="ℹ️", font=('Arial', 10), foreground="blue", cursor="hand2")
        info_button.grid(row=row, column=column, sticky=tk.W, padx=(5, 0))
        
        # Create tooltip
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=tooltip_text, background="lightyellow", 
                           relief="solid", borderwidth=1, font=('Arial', 9),
                           wraplength=300, justify=tk.LEFT)
            label.pack()
            
            # Auto-hide after 3 seconds
            tooltip.after(3000, tooltip.destroy)
        
        info_button.bind("<Button-1>", show_tooltip)
    
    def _update_mic_display(self):
        """Update the mic sensitivity display with formatted value"""
        if self.mic_sensitivity_var is not None:
            value = self.variables.get_value('song_mic_sensitivity')
            self.mic_sensitivity_var.set(f"{value:.2f}")
    
    def _on_double_click(self, event):
        """Handle double-click on songs tree for editing"""
        self.edit_selected_song()
    
    def save_song(self):
        """Save song configuration"""
        song_name = self.variables.get_value('song_name').strip()
        if not song_name:
            messagebox.showerror("Error", "Please enter a song name")
            return
        
        # Determine media settings based on toggle
        media_mode = self.variables.get_value('song_media_mode')
        
        config = {
            "intensity": self.variables.get_value('song_intensity'),
            "reactivity_mode": self.variables.get_value('song_reactivity'),
            "mic_sensitivity": self.variables.get_value('song_mic_sensitivity'),
            "color_bias": self.variables.get_value('song_color'),
            "secondary_color_bias": self.variables.get_value('song_secondary_color'),
            "media_mode": media_mode,
            "notes": self.variables.get_value('song_notes')
        }
        
        # Add random color percentage if not -1 (auto)
        random_color_percentage = self.variables.get_value('song_random_color_percentage')
        if random_color_percentage >= 0:
            config["random_color_percentage"] = random_color_percentage
        
        # Add media-specific settings based on mode
        if media_mode == 'video':
            config["video_path"] = self.variables.get_value('song_video')
            config["visualization_mode"] = 'none'  # Clear visualization when using video
        else:
            config["video_path"] = ''  # Clear video when using visualization
            config["visualization_mode"] = self.variables.get_value('song_visualization')
        
        config_manager = self.get_controller('config_manager')
        if not config_manager:
            messagebox.showerror("Error", "Configuration manager not available")
            return
        
        # Check if this is an update by looking at original song name
        existing_songs = config_manager.get_all_songs()
        is_update = self.original_song_name is not None and self.original_song_name in existing_songs
        
        print(f"DEBUG GUI: Saving song '{song_name}', original_name='{self.original_song_name}', is_update={is_update}")
        print(f"DEBUG GUI: Config being saved: {config}")
        
        if is_update:
            # Handle song name changes during updates
            if song_name != self.original_song_name:
                # Song name changed - delete old, add new
                print(f"DEBUG GUI: Song name changed from '{self.original_song_name}' to '{song_name}'")
                if config_manager.delete_song(self.original_song_name) and config_manager.add_song(song_name, config):
                    self.original_song_name = song_name  # Update tracking
                    self.refresh_songs_list()
                    self._notify_other_tabs_refresh()
                    self.log_info(f"Renamed and updated song: {self.original_song_name} -> {song_name}")
                else:
                    messagebox.showerror("Error", "Failed to rename/update song.")
            else:
                # Same name - just update
                if config_manager.update_song(song_name, config):
                    self.refresh_songs_list()
                    self._notify_other_tabs_refresh()
                    self.log_info(f"Updated song: {song_name}")
                else:
                    messagebox.showerror("Error", "Failed to update song. Check configuration.")
        else:
            # Add new song
            if config_manager.add_song(song_name, config):
                self.refresh_songs_list()
                self._notify_other_tabs_refresh()
                self.clear_song_form()
                self.log_info(f"Added new song: {song_name}")
            else:
                messagebox.showerror("Error", "Failed to save song. Check configuration.")
    
    def new_song(self):
        """Start creating a new song by clearing the form"""
        self.clear_song_form()
        self.log_info("Ready to create new song")
    
    def clear_song_form(self):
        """Clear the song form"""
        self.original_song_name = None  # Clear tracking for new songs
        self.variables.set_value('song_name', "")
        self.variables.set_value('song_intensity', 128)
        self.variables.set_value('song_reactivity', "medium")
        self.variables.set_value('song_mic_sensitivity', 0.3)
        self.variables.set_value('song_color', "white")
        self.variables.set_value('song_secondary_color', "none")
        self.variables.set_value('song_random_color_percentage', -1)  # Auto mode
        self.variables.set_value('song_video', "")
        self.variables.set_value('song_visualization', "psychedelic")  # Default to a visualization
        self.variables.set_value('song_media_mode', "video")  # Default to video mode
        self.variables.set_value('song_notes', "")
        
        # Update UI to reflect the default mode
        self._on_media_mode_change()
    
    def refresh_songs_list(self):
        """Refresh the songs list in the treeview"""
        config_manager = self.get_controller('config_manager')
        if not config_manager:
            return
        
        # Clear existing items
        for item in self.songs_tree.get_children():
            self.songs_tree.delete(item)
        
        # Add songs
        songs = config_manager.get_all_songs()
        for song_name, config in songs.items():
            video_path = config.get('video_path', '')
            video_display = os.path.basename(video_path) if video_path else 'None'
            visualization_mode = config.get('visualization_mode', 'none')
            
            self.songs_tree.insert('', 'end', values=(
                song_name,
                config.get('intensity', 0),
                config.get('reactivity_mode', ''),
                config.get('color_bias', ''),
                config.get('secondary_color_bias', 'none'),
                video_display,
                visualization_mode
            ))
    
    def edit_selected_song(self):
        """Edit the selected song"""
        selection = self.songs_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a song to edit")
            return
        
        item = self.songs_tree.item(selection[0])
        song_name = item['values'][0]
        
        print(f"DEBUG EDIT: Selected song name from tree: '{song_name}'")
        
        config_manager = self.get_controller('config_manager')
        if not config_manager:
            return
        
        config = config_manager.get_song_config(song_name)
        if config:
            print(f"DEBUG EDIT: Loading config for '{song_name}': {config}")
            self.original_song_name = song_name  # Track original name for update detection
            self.variables.set_value('song_name', song_name)
            self.variables.set_value('song_intensity', config.get('intensity', 128))
            self.variables.set_value('song_reactivity', config.get('reactivity_mode', 'medium'))
            self.variables.set_value('song_mic_sensitivity', config.get('mic_sensitivity', 0.3))
            self.variables.set_value('song_color', config.get('color_bias', 'white'))
            self.variables.set_value('song_secondary_color', config.get('secondary_color_bias', 'none'))
            self.variables.set_value('song_random_color_percentage', config.get('random_color_percentage', -1))
            self.variables.set_value('song_video', config.get('video_path', ''))
            self.variables.set_value('song_visualization', config.get('visualization_mode', 'none'))
            self.variables.set_value('song_notes', config.get('notes', ''))
            
            # Determine media mode based on existing config
            media_mode = config.get('media_mode')
            if media_mode is None:
                # Legacy support: determine mode from existing video/visualization settings
                if config.get('video_path', '') and config.get('video_path', '') != '':
                    media_mode = 'video'
                elif config.get('visualization_mode', 'none') != 'none':
                    media_mode = 'visualization'
                else:
                    media_mode = 'video'  # Default to video
            
            self.variables.set_value('song_media_mode', media_mode)
            
            # Update UI to reflect the media mode
            self._on_media_mode_change()
            
            # Update the mic display after setting the value
            self._update_mic_display()
            
            self.log_info(f"Loaded song for editing: {song_name}")
        else:
            messagebox.showerror("Error", f"Could not load configuration for song '{song_name}'")
    
    def delete_selected_song(self):
        """Delete the selected song"""
        selection = self.songs_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a song to delete")
            return
        
        item = self.songs_tree.item(selection[0])
        song_name = item['values'][0]
        
        if messagebox.askyesno("Confirm Delete", f"Delete song '{song_name}'?"):
            config_manager = self.get_controller('config_manager')
            if config_manager and config_manager.delete_song(song_name):
                self.refresh_songs_list()
                self._notify_other_tabs_refresh()
                self.log_info(f"Deleted song: {song_name}")
            else:
                messagebox.showerror("Error", "Failed to delete song")
    
    def get_songs_combo_values(self):
        """Get list of song names for combo boxes"""
        config_manager = self.get_controller('config_manager')
        if config_manager:
            songs = config_manager.get_all_songs()
            return list(songs.keys())
        return []
    
    def get_song_config(self, song_name):
        """Get configuration for a specific song"""
        config_manager = self.get_controller('config_manager')
        if config_manager:
            return config_manager.get_song_config(song_name)
        return None
    
    def _notify_other_tabs_refresh(self):
        """Notify other tabs that songs have changed and they should refresh"""
        try:
            # Use direct reference to main app for reliable refresh
            main_app = self.get_controller('main_app')
            if main_app and hasattr(main_app, 'refresh_all_data'):
                # Schedule refresh on next idle cycle for immediate response
                main_app.root.after_idle(main_app.refresh_all_data)
                print("Triggered immediate refresh of all song lists")
            else:
                print("Warning: Could not access main app for refresh")
        except Exception as e:
            print(f"Could not trigger immediate refresh: {e}")


class SongSelectorWidget(BaseUIComponent):
    """Enhanced song selector widget for live performance with sequencing"""
    
    def __init__(self, parent, controllers=None, on_selection_change=None, on_double_click=None):
        self.on_selection_change = on_selection_change
        self.on_double_click_callback = on_double_click
        self.selected_song = None
        super().__init__(parent, controllers)
    
    def setup_ui(self):
        """Setup enhanced song selector UI for live performance"""
        self.frame = ttk.Frame(self.parent)
        
        # Header with sequence controls
        header_frame = ttk.Frame(self.frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(header_frame, text="Song Sequence (Double-click to start):", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W)
        
        # Sequence control buttons
        button_frame = ttk.Frame(header_frame)
        button_frame.grid(row=0, column=1, sticky=tk.E, padx=(10, 0))
        
        ttk.Button(button_frame, text="▲ Move Up", command=self.move_song_up, width=12).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="▼ Move Down", command=self.move_song_down, width=12).grid(row=0, column=1)
        
        header_frame.columnconfigure(0, weight=1)
        
        # Large song list (15 lines) with scrollbar
        list_frame = ttk.Frame(self.frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        
        # Create treeview with columns for better live performance view
        columns = ('Song', 'Mode', 'Color', 'Secondary', 'Video', 'Viz')
        self.song_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Configure column headers and widths
        self.song_tree.heading('Song', text='Song Name')
        self.song_tree.heading('Mode', text='Mode')
        self.song_tree.heading('Color', text='Primary')
        self.song_tree.heading('Secondary', text='Secondary')
        self.song_tree.heading('Video', text='Video')
        self.song_tree.heading('Viz', text='Visualization')
        
        self.song_tree.column('Song', width=250, minwidth=200)
        self.song_tree.column('Mode', width=80, minwidth=60)
        self.song_tree.column('Color', width=70, minwidth=50)
        self.song_tree.column('Secondary', width=70, minwidth=50)
        self.song_tree.column('Video', width=60, minwidth=40)
        self.song_tree.column('Viz', width=100, minwidth=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.song_tree.yview)
        self.song_tree.config(yscrollcommand=scrollbar.set)
        
        self.song_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind events
        self.song_tree.bind('<Double-1>', self._on_double_click)
        self.song_tree.bind('<<TreeviewSelect>>', self._on_selection)
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)
        
        # Initialize songs
        self.refresh_songs()
        # Auto-refresh disabled to prevent unwanted config changes
        # self._start_auto_refresh()
        
    def _on_double_click(self, event):
        """Handle double-click to start song"""
        try:
            print(f"DOUBLECLICK DEBUG: Double-click event triggered")
            
            selection = self.song_tree.selection()
            print(f"DOUBLECLICK DEBUG: Selection: {selection}")
            
            if selection:
                item = self.song_tree.item(selection[0])
                song_name = item['values'][0]
                self.selected_song = song_name
                print(f"DOUBLECLICK DEBUG: Selected song: '{song_name}'")
                
                # If double-click callback is provided, simulate Stop Show + Start Show sequence
                if self.on_double_click_callback:
                    print(f"DOUBLECLICK DEBUG: Starting Stop-then-Start sequence for '{song_name}'")
                    
                    # First check if we need to get the controllers to call stop_show manually
                    # We need to call stop_show on the light show controller, not start_show
                    import time
                    
                    # Get the controllers from the callback (which is start_show method)
                    light_show = self.on_double_click_callback.__self__
                    
                    # Step 1: Stop current show if running (like clicking Stop Show button)
                    if light_show.is_show_running():
                        print(f"DOUBLECLICK DEBUG: Stopping current show first")
                        light_show.stop_show()
                        # Longer delay to let visualization fully stop
                        print(f"DOUBLECLICK DEBUG: Waiting 2 seconds for clean stop...")
                        time.sleep(2.0)
                    
                    # Step 2: Start new show normally
                    print(f"DOUBLECLICK DEBUG: Starting new show for '{song_name}'")
                    self.on_double_click_callback()
                    print(f"DOUBLECLICK DEBUG: Double-click sequence completed successfully")
                # Otherwise fall back to selection change (for backwards compatibility)
                elif self.on_selection_change:
                    print(f"DOUBLECLICK DEBUG: Using selection change callback as fallback")
                    self.on_selection_change()
                else:
                    print(f"DOUBLECLICK DEBUG: No callback available")
            else:
                print(f"DOUBLECLICK DEBUG: No selection found")
                
        except Exception as e:
            print(f"DOUBLECLICK ERROR: Exception in double-click handler: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_selection(self, event):
        """Handle single click selection"""
        selection = self.song_tree.selection()
        if selection:
            item = self.song_tree.item(selection[0])
            self.selected_song = item['values'][0]
    
    def refresh_songs(self):
        """Refresh the song list with sequencing order"""
        config_manager = self.get_controller('config_manager')
        if not config_manager:
            return
        
        # Clear existing items
        for item in self.song_tree.get_children():
            self.song_tree.delete(item)
        
        # Get songs and sequence order
        songs = config_manager.get_all_songs()
        sequence_order = self._get_sequence_order(list(songs.keys()))
        
        # Add songs in sequence order
        for song_name in sequence_order:
            if song_name in songs:
                config = songs[song_name]
                video_path = config.get('video_path', '')
                video_display = '✓' if video_path and os.path.exists(video_path) else ''
                visualization_mode = config.get('visualization_mode', 'none')
                
                self.song_tree.insert('', 'end', values=(
                    song_name,
                    config.get('reactivity_mode', ''),
                    config.get('color_bias', ''),
                    config.get('secondary_color_bias', 'none'),
                    video_display,
                    visualization_mode
                ))
    
    def _get_sequence_order(self, song_names):
        """Get or create sequence order for songs"""
        config_manager = self.get_controller('config_manager')
        if not config_manager:
            return song_names
            
        # Try to get existing sequence from settings
        try:
            settings = config_manager.settings
            if 'song_sequence' in settings:
                sequence = settings['song_sequence'].copy()  # Make a copy to avoid modification issues
                initial_length = len(sequence)
                
                # Add any new songs not in sequence to the end
                for song in song_names:
                    if song not in sequence:
                        sequence.append(song)
                        print(f"Added new song '{song}' to sequence at position {len(sequence)}")
                
                # Remove songs that no longer exist
                sequence = [song for song in sequence if song in song_names]
                
                # If sequence changed, save it immediately
                if len(sequence) != initial_length or len(sequence) != len(settings['song_sequence']):
                    config_manager.settings['song_sequence'] = sequence
                    config_manager.save_settings()
                    print(f"Updated and saved sequence: {sequence}")
                
                return sequence
        except Exception as e:
            print(f"Error getting sequence order: {e}")
        
        # Default alphabetical order if no sequence exists
        sorted_songs = sorted(song_names)
        # Save this as initial sequence
        try:
            config_manager.settings['song_sequence'] = sorted_songs
            config_manager.save_settings()
            print(f"Created initial sequence: {sorted_songs}")
        except Exception as e:
            print(f"Error saving initial sequence: {e}")
        return sorted_songs
    
    def _save_sequence_order(self):
        """Save current sequence order to settings"""
        try:
            config_manager = self.get_controller('config_manager')
            if not config_manager:
                return
                
            # Get current order from treeview
            sequence = []
            for item in self.song_tree.get_children():
                song_name = self.song_tree.item(item)['values'][0]
                sequence.append(song_name)
            
            # Save to settings
            config_manager.settings['song_sequence'] = sequence
            config_manager.save_settings()
            print(f"Saved song sequence: {sequence}")
            
        except Exception as e:
            print(f"Error saving sequence: {e}")
    
    def move_song_up(self):
        """Move selected song up in sequence"""
        selection = self.song_tree.selection()
        if not selection:
            print("No song selected for move up")
            return
            
        item = selection[0]
        index = self.song_tree.index(item)
        song_name = self.song_tree.item(item)['values'][0]
        
        if index > 0:
            print(f"Moving '{song_name}' up from position {index} to {index-1}")
            self.song_tree.move(item, '', index - 1)
            self._save_sequence_order()
            # Keep the song selected after moving (do this after save to avoid refresh clearing it)
            self.song_tree.selection_set(item)
            self.song_tree.focus(item)
            # Skip refresh for now - sequence is already saved and this tab shows the current order
        else:
            print(f"'{song_name}' is already at the top")
    
    def move_song_down(self):
        """Move selected song down in sequence"""
        selection = self.song_tree.selection()
        if not selection:
            print("No song selected for move down")
            return
            
        item = selection[0]
        index = self.song_tree.index(item)
        song_name = self.song_tree.item(item)['values'][0]
        max_index = len(self.song_tree.get_children()) - 1
        
        if index < max_index:
            print(f"Moving '{song_name}' down from position {index} to {index+1}")
            self.song_tree.move(item, '', index + 1)
            self._save_sequence_order()
            # Keep the song selected after moving (do this after save to avoid refresh clearing it)
            self.song_tree.selection_set(item)
            self.song_tree.focus(item)
            # Skip refresh for now - sequence is already saved and this tab shows the current order
        else:
            print(f"'{song_name}' is already at the bottom")
    
    def _notify_refresh_if_possible(self):
        """Notify other tabs to refresh if possible"""
        try:
            # Use direct reference to main app for reliable refresh
            main_app = self.get_controller('main_app')
            if main_app and hasattr(main_app, 'refresh_all_data'):
                # Schedule refresh on next idle cycle for immediate response
                main_app.root.after_idle(main_app.refresh_all_data)
                print("Triggered refresh after sequence change")
            else:
                print("Could not trigger refresh - main app not accessible")
        except Exception as e:
            print(f"Error triggering refresh: {e}")
    
    def _start_auto_refresh(self):
        """Start automatic refresh to detect config changes"""
        def check_for_changes():
            try:
                config_manager = self.get_controller('config_manager')
                if config_manager:
                    # Check if songs.json has been modified
                    import os
                    songs_file = os.path.join('config', 'songs.json')
                    if os.path.exists(songs_file):
                        current_mtime = os.path.getmtime(songs_file)
                        if not hasattr(self, '_last_songs_mtime'):
                            self._last_songs_mtime = current_mtime
                        elif current_mtime > self._last_songs_mtime:
                            self._last_songs_mtime = current_mtime
                            # Add small delay to ensure file write is complete
                            self.frame.after(100, self.refresh_songs)
                            print(f"Auto-refreshed songs due to config change (Light Show tab)")
            except Exception as e:
                print(f"Auto-refresh error: {e}")  # Debug errors instead of silent ignore
            
            # Schedule next check
            if hasattr(self, 'frame') and self.frame.winfo_exists():
                self.frame.after(1000, check_for_changes)  # Check every 1 second for faster response
        
        # Start the auto-refresh cycle
        self.frame.after(500, check_for_changes)  # Initial delay of 0.5 seconds
    
    def get_selected_song(self):
        """Get the currently selected song name"""
        return self.selected_song
    
    def get_combo_widget(self):
        """For compatibility - return the treeview instead of combobox"""
        return self.song_tree
    
    def set_selected_song(self, song_name):
        """Set the selected song"""
        self.selected_song = song_name
        # Find and select the song in the treeview
        for item in self.song_tree.get_children():
            if self.song_tree.item(item)['values'][0] == song_name:
                self.song_tree.selection_set(item)
                self.song_tree.see(item)
                break