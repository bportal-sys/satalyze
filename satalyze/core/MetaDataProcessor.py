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


import io
import os
import json
import numpy as np
import pandas as pd
from PIL import Image
import time
from datetime import datetime
import ee 
from abc import ABC, abstractmethod
import requests
import math 
import cv2
from typing import Union, List, Dict
from ultralytics import YOLO
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction
import pandas as pd
import matplotlib.pyplot as plt
import os
import logging

logger = logging.getLogger(__name__)

# ==================================
# Metadata Processor 
class SatelliteMetadataProcessor:
    """Processor for timestamp extraction, and geometric tracking"""

    def extract_capture_date(self, metadata_info: dict) -> str:
        """Gets timestamp of capture time from metadata"""
        timestamp_ms = metadata_info['properties'].get('system:time_start')
        if not timestamp_ms:
            logger.warning('Warning, unknown flight date')
            return "Unknown Flight Date"
        
        return datetime.fromtimestamp(timestamp_ms / 1000.0).strftime('%Y-%m-%d')
        

    @staticmethod
    def calculate_ground_dimensions(bbox: list) -> dict:
        """Computes approximate physical width and height spans of the bounding box (meters)"""
        min_lon, min_lat, max_lon, max_lat = bbox
        lon_width = abs(max_lon - min_lon)
        lat_height = abs(max_lat - min_lat)

        #Some math that calculates ground distance
        avg_lat = (min_lat + max_lat) / 2.0
        width_meters = lon_width * 111000 * math.cos(math.radians(avg_lat))
        height_meters = lat_height * 111000
        
        return {
            'width_meters': float(width_meters),
            'height_meters': float(height_meters)
        }