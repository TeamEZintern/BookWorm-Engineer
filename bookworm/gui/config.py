"""
GUI Configuration for BookWorm

This module handles GUI-specific configuration settings.
"""

from dataclasses import dataclass
from typing import Optional
@dataclass
class GUIConfig:
    """Configuration for the BookWorm GUI application."""
    
    # Window settings
    window_width: int = 1200
    window_height: int = 800
    window_title: str = "BookWorm Engineer"
    
    # Side panel settings
    side_panel_width: int = 300
    side_panel_min_width: int = 200
    
    # Main panel settings
    main_panel_min_height: int = 400
    
    # Message display settings
    message_bubble_max_width: int = 600
    show_timestamps: bool = True
    timestamp_format: str = "HH:mm"
    
    # Theme settings
    theme: str = "dark"  # light, dark
    
    # Performance settings
    max_chats: int = 100
    auto_save_interval: int = 30  # seconds
    
    # Search settings
    search_delay: int = 300  # milliseconds
    
    # Tool execution
    tool_execution_timeout: int = 30  # seconds
    
    @classmethod
    def from_config(cls, config=None):
        """Create GUI config from existing config if available."""
        if config is None:
            return cls()
        
        # Extract relevant settings from existing config
        gui_config = cls()
        
        # Override with any existing GUI-specific settings
        if hasattr(config, 'gui_window_width'):
            gui_config.window_width = config.gui_window_width
        if hasattr(config, 'gui_window_height'):
            gui_config.window_height = config.gui_window_height
        if hasattr(config, 'gui_theme'):
            gui_config.theme = config.gui_theme
            
        return gui_config