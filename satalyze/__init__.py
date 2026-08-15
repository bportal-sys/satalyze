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
from .core.Sata_Pipeline import SatelliteTrafficPipeline
from .core.CarDetectionLogging import CarDetectionLogging
from .core.DF_Plotter import CarTrafficPlotter
from .core.MachineLearningInference import MachineInference_YOLO_Provider_Single
from .core.ML_Visualization import MachineLearning_Visualization
from .core.SatelliteDiskCache import SatelliteDiskCache
from .core.SatelliteProvider import GoogleEarthEngineAuthenticator
from .core.SatelliteProvider import GoogleEarthEngineProvider

# shortcut launcher | Streamlit UI
def start():
    """Launches the built-in Streamlit dashboard interface."""
    # Find app.py
    app_path = Path(__file__).parent / "app.py"
    
    print("Launching Satellite Pipeline Dashboard...")
    
    # 'streamlit run Sata_Pipeline/app.py' 
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])
