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

# ================================
# Validation Class
class GeospatialValidator:
    """Handles all safety thresholds, quotas and strucutural input verification"""
    def __init__(self, max_daily_calls: int = 5, max_degree_span: float = 0.05, max_days_range: int = 2400):
        self.max_daily_calls = max_daily_calls
        self.max_degree_span = max_degree_span
        self.max_days_range = max_days_range
        self.max_allowable_meters = 1000.0 
        self.max_multi_limit = 10
        
    def validate_switch_mode(self, bbox: list, center: list, threshold: float) -> list:
        """Determines the active input and outputs final bounding box geometry"""
        if center is not None:
            lon, lat = center
            #Prevents cos(90) (div by 0)
            if abs(lat) >= 89.9:
                lon_threshold = threshold
                lat_threshold = threshold
            else: 
                lon_threshold = threshold / math.cos(math.radians(lat))
                lat_threshold = threshold
            
            return [lon - lon_threshold, lat - lat_threshold, lon + lon_threshold, lat + lat_threshold]
        
        elif bbox is not None:
            return bbox
        else: 
            raise ValueError("No bounding box provided")

    def check_spatial_bounds(self, calculated_bbox: list) -> None:
        """Limits bounding box footprint to conserve EECU-seconds"""
        min_lon, min_lat, max_lon, max_lat = calculated_bbox
        lon_width = abs(max_lon - min_lon)
        lat_height = abs(max_lat - min_lat)

        if lon_width > self.max_degree_span or lat_height > self.max_degree_span:
            raise ValueError(f"Bounding Box too big. Current span ({round(lon_width, 4)}) | Allowable span ({self.max_degree_span})")

    def check_time_bounds(self, start_date: str, end_date: str) -> None:
        """Limits horizon footprint to conserve EECU-seconds"""
        d1 = datetime.strptime(start_date, "%Y-%m-%d")
        d2 = datetime.strptime(end_date, "%Y-%m-%d")
        days_requested = (d2 - d1).days

        if days_requested > self.max_days_range:
            raise ValueError(f"Time Horizon too big. Current span ({days_requested}) | Allowable span ({self.max_days_range})")

    def check_quota_limit(self, current_calls: int) -> None:
        """Self-imposed API execution limits to prevent runaway code eating EECU-seconds"""
        if current_calls >= self.max_daily_calls: 
            raise PermissionError(f"Personal Quota Reached: Local limit of {self.max_daily_calls}")
        
    def check_ground_scale_safety(self, dimensions_dict: dict) -> None:
        """Checks if approximate ground distance is viable for ML"""
        w = dimensions_dict['width_meters']
        h = dimensions_dict['height_meters']
        if w > self.max_allowable_meters or h > self.max_allowable_meters:
            raise ValueError(
                f"Requested area too large for ML ({round(w)})m x ({round(h)})m | Allowable ground distance ({self.max_allowable_meters})m x ({self.max_allowable_meters})m"
            )
        
    def get_target_pixels(self, dimensions_dict: dict, res: float = 0.6) -> int:
        """
        Creates optimial dimension for request based on ground distance
        res: 0.6 for NAIP 0.6 sub meter resolution change if upgrade
        """
        w = dimensions_dict['width_meters']
        h = dimensions_dict['height_meters']

        max_ground_span = max(w, h)
        
        calculate_pixels = int(math.ceil(max_ground_span / res))
        target_pixel_size = max(min(calculate_pixels, 1111), 512)
        return target_pixel_size
    
    def check_multi_limit(self, limit: int) -> None:
        """Checks limit number for multi image API call"""
        if limit > self.max_multi_limit:
            raise ValueError(f'Multi Limit exceeded: {limit} | Allowed {self.max_multi_limit}. Enable bypass flag or lower limit')