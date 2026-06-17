#!/usr/bin/env python3
"""
Test script for Bookworm GUI

This script tests if the Bookworm GUI can be imported and instantiated
without errors.
"""

import sys
from PySide6.QtWidgets import QApplication

# Add the project root to the Python path
sys.path.insert(0, '/workspace/BookWorm-Engineer')

from bookworm.config import load_config
from bookworm.gui import BookwormGUI, GUIConfig
def main():
    """Main function to test the GUI."""
    # Load configuration
    config = load_config()
    
    # Create GUI config
    gui_config = GUIConfig()
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = BookwormGUI(config, gui_config)
    window.show()
    
    # Run the application
    sys.exit(app.exec())
if __name__ == "__main__":
    main()