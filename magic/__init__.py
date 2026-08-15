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
import sys
import subprocess
from pathlib import Path

# core subfolder and [pull out] pipeline
from .core import Sata_Pipeline

# shortcut launcher | Streamlit UI
def start():
    """Launches the built-in Streamlit dashboard interface."""
    # Find app.py
    app_path = Path(__file__).parent / "app.py"
    
    print("Launching Satellite Pipeline Dashboard...")
    
    # 'streamlit run Sata_Pipeline/app.py' 
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])
