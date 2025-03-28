import subprocess
import os

def update_system():
    """Update system icon cache and desktop database."""
    try:
        # Update icon cache
        subprocess.run(['gtk-update-icon-cache', '--force', '/usr/share/icons/hicolor'], check=False)
        
        # Update desktop database
        subprocess.run(['update-desktop-database', '/usr/share/applications'], check=False)
    except Exception as e:
        print(f"Warning: Could not update system caches: {e}")
