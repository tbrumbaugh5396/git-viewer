#!/usr/bin/env python3
"""
Git Repository Viewer Package

A comprehensive Git and Meta repository management tool built with wxPython.
This package provides a graphical interface for all Git operations plus support 
for meta repositories.
"""

__version__ = "1.0.0"
__author__ = "Git Viewer Team"
__description__ = "A comprehensive Git and Meta repository management tool"

# Import main classes for easy access
from .git_viewer import GitViewerApp, MainFrame

__all__ = [
    'GitViewerApp',
    'MainFrame',
    '__version__',
    '__author__',
    '__description__'
]
