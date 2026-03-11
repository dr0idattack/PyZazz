"""
GUI package for DMX Light Show Controller
Contains modular UI components for better maintainability
"""

from .base_ui import BaseUIComponent
from .video_controls import VideoControlsWidget
from .song_config import SongConfigWidget
from .light_config import LightConfigWidget
from .manual_controls import ManualControlsWidget
from .light_show import LightShowWidget
from .status_bar import StatusBarWidget

__all__ = [
    'BaseUIComponent',
    'VideoControlsWidget',
    'SongConfigWidget', 
    'LightConfigWidget',
    'ManualControlsWidget',
    'LightShowWidget',
    'StatusBarWidget'
]