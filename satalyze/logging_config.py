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


import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logger():
    # 1. Get the 'root' logger that controls everything
    root_logger = logging.getLogger()
    
    # If the logger is already set up, don't do it again
    if root_logger.hasHandlers():
        return root_logger

    root_logger.setLevel(logging.INFO)

    # 2. Define exactly what information shows up in your errors
    log_format = logging.Formatter(
        fmt="%(asctime)s | [%(levelname)s] | %(name)s | Line %(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 3. Output to the Terminal/Console (Crucial for Shiny logs)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)

    # 4. 🗄️ SAFE EXTENSION: Storage-Controlled Rotating File Logging
    # Automatically creates a "logs/" directory at the package root level
    package_root = Path(__file__).resolve().parent
    log_dir = package_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file_path = log_dir / "app_errors.log"

    # Rotating Handler Settings: 
    # maxBytes=5*1024*1024 locks the file size to a 5 Megabyte maximum ceiling.
    # backupCount=3 ensures it keeps a maximum of 3 historical rotated archive logs.
    # Total combined disk space for logs can NEVER exceed 20MB!
    file_handler = RotatingFileHandler(
        filename=str(log_file_path),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO) # Only log Errors or Critical bugs here
    file_handler.setFormatter(log_format)
    root_logger.addHandler(file_handler)

    return root_logger
