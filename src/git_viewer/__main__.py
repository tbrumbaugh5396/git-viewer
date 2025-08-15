#!/usr/bin/env python3
"""
Main entry point for the Git Repository Viewer package.

This allows the package to be run as:
    python -m git_viewer
    python -m src.git_viewer
"""

import sys
import os

# Add the current directory to the path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """Main entry point for the application"""
    try:
        # Try relative import first (for package execution)
        try:
            from .git_viewer import GitViewerApp
        except ImportError:
            # Fall back to absolute import (for script execution)
            from git_viewer import GitViewerApp
        
        # Create and run the application
        app = GitViewerApp()
        app.MainLoop()
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error launching application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
