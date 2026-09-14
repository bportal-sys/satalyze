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
from pathlib import Path

def launch_dashboard():
    """Programmatic entry point to run the embedded dashboard dashboard interface."""
    from shiny import run_app
    
    # Calculate exactly where the shinyapp.py is installed inside site-packages
    app_path = Path(__file__).resolve().parent / "app" / "shinyapp.py"
    
    if not app_path.exists():
        raise FileNotFoundError(f"Critical Package Error: Dashboard script missing at {app_path}")
        
    run_app(str(app_path), launch_browser=True)
