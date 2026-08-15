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

class CarDetectionLogging:
    """store Dataframe information"""
    def __init__(self):
        self._buffer = []
        self.df = pd.DataFrame()

    def _read_metadata(self, metadata: dict):
        """Helper function to read and process meta data ( again)"""
        #Fix time stamp if needed
        raw_capture_date = metadata['capture_date']
        #capture_date = raw_capture_date[:10].strip()
        capture_date = raw_capture_date.split(" ")[0]
        pixel_size = metadata['pixel_size']
        min_lon, min_lat, max_lon, max_lat = metadata['bounding_box']
        center_lat = (min_lat + max_lat) / 2.0
        center_lon = (min_lon + max_lon) / 2.0 
        return {'capture_date': capture_date,
                'center_lat': center_lat,
                'center_lon': center_lon,
                'pixel_size': pixel_size
                }

    def log_detection(self, metadata: Dict, car_count: int):
        """Plugs directly into the pipeline loop to save a single image record."""
        metadata_processed = self._read_metadata(metadata=metadata)
        capture_date = metadata_processed['capture_date']
        lon = metadata_processed['center_lon']
        lat = metadata_processed['center_lat']

        record = {
            "date": pd.to_datetime(capture_date),
            "longitude": lon,
            "latitude": lat,
            "car_count": int(car_count)
        }
        self._buffer.append(record)
        self.df = pd.DataFrame(self._buffer)

    def get_dataframe(self) -> pd.DataFrame:
        """Returns the full gathered dataset."""
        return self.df

    def save_to_csv(self, file_path: str = "car_detections.csv", append: bool = True):
        """
        Saves data to a CSV file.
        
        Parameters:
        append=True  -> Adds data to the bottom of the existing file.
        append=False -> Overwrites the file or creates a brand-new one.
        """
        if self.df.empty:
            print("No data to save.")
            return

        # Check if file exists and we want to append
        if append and os.path.exists(file_path):
            # Append mode ('a'). Do not write the header
            self.df.to_csv(file_path, mode='a', header=False, index=False)
            print(f"Successfully ADDED records to existing file: {file_path}")
        else:
            # Write mode ('w'). Create a new file or overwrite
            print(f"Successfully CREATED/OVERWRITTEN file: {file_path}")
            
        # Clear memory buffer
        self._buffer = []
        self.df = pd.DataFrame()