"""
BookWorm GUI Controllers

Controllers own their generated views, wire signals via ``findChild()``, and
hold the GUI behaviour previously embedded in the monolithic panel classes.
"""

from .app_controller import AppController
from .main_panel_controller import MainPanelController
from .side_panel_controller import SidePanelController

__all__ = [
    "AppController",
    "MainPanelController",
    "SidePanelController",
]
