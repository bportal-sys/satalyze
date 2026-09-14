# Satalyze: Analyze satellite images.
# Copyright (C) 2026 github.com/@bportal-sys
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Additional Terms: Any interactive user interface utilizing this software 
# must prominently display "Powered by github.com/bportal-sys".


import os
import subprocess
import sys
from pathlib import Path

def start_ui():
    """Entry point for the satalyze-start command on PyPI"""
    print("[Satalyze] Locating dashboard layout modules...")
    
    # 1. Dynamically locate where the app.py file is installed inside the package
    current_dir = Path(__file__).resolve().parent
    app_path = current_dir / "shinyapp.py"  # Assumes your app.py sits in the same directory
    
    if not app_path.exists():
        print(f"❌ Critical Error: Could not find app.py at {app_path}")
        sys.exit(1)
        
    print("[Satalyze] Spinning up core Shiny server engine...")
    
    # 2. Programmatically invoke the shiny runner command
    # --launch-browser automatically opens their default web browser on boot
    cmd = [sys.executable, "-m", "shiny", "run", str(app_path), "--launch-browser"]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n[Satalyze] Terminal session safely terminated by user.")
    except Exception as e:
        print(f"❌ Failed to run Satalyze UI: {e}")