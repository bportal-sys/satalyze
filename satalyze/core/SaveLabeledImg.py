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

#=======================================================
# save util
class LabelImage_Save():
    """Manages local disk read/write for saving labelled images """ 
    def __init__(self, label_dir: str = "labelled_imgs"):
        self.label_dir = label_dir
        os.makedirs(self.label_dir, exist_ok=True)
    
    def check_file_exists(self, img_path_str: str) -> bool:
        """Scans label folder for existing file (after getting metadata / capture date)"""
        image_path = os.path.join(self.label_dir, f"{img_path_str}.png")
        return os.path.exists(image_path)

    def _generate_asset_identifier(self, metadata: dict) -> str:
        """File naming calculations in RAM"""
        #Fix time stamp if needed
        raw_capture_date = metadata['capture_date']
        #capture_date = raw_capture_date[:10].strip()
        capture_date = raw_capture_date.split(" ")[0]
        pixel_size = metadata['pixel_size']
        min_lon, min_lat, max_lon, max_lat = metadata['bounding_box']
        center_lat = (min_lat + max_lat) / 2.0
        center_lon = (min_lon + max_lon) / 2.0 
        return f"asset_{capture_date}_{center_lat:.4f}_{center_lon:.4f}_{pixel_size}"

    def _write_assets_to_disk(self, image_path: str, canvas: np.ndarray, format_type: str = 'png'):
        """Local Storage file save"""
        # file type.png or .jpg
        ext = format_type.lower().replace(".", "")
        save_path = os.path.join(self.label_dir, f"{image_path}.{ext}")
        
        # array format
        if not isinstance(canvas, np.ndarray):
            canvas = np.array(canvas)

        if canvas.dtype != np.uint8:
            canvas = canvas.astype(np.uint8)

        # where file is actually saved
        success = cv2.imwrite(save_path, canvas)
        print('success saving Image')
        save_path = os.path.join(self.label_dir, f"{image_path}.png")
        cv2.imwrite(save_path, canvas)
        return save_path