#!/usr/bin/env python3
"""
Launcher script for Git Repository Viewer
This script can be used to run the application directly
"""

import sys
import os

# Add the package directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """Main entry point"""
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