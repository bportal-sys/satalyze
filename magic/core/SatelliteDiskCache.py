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

# ==================================================
# Cache Class
class SatelliteDiskCache:
    """Manages all local disk read/write for caching raw arrays and text metrics """ 
    def __init__(self, cache_dir: str = "satellite_cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.manifest_path = os.path.join(self.cache_dir, "cache_manifest.json")
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> dict:
        """Loads the registry mapping file from disk or builds fresh one"""
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, 'r') as f:
                return json.load(f)
        return {}

    def _save_manifest(self) -> None:
        """Persists master registry to local storage"""
        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest, f, indent = 4)
        
    def _create_search_key(self, capture_date: str, bbox: list, pixel_size) -> str:
        """Generates standardized string key representing user's raw query"""
        clean_timestamp = capture_date.replace(" ", "_").replace(":", "+")
        coords_str = "_".join([f"{coord:.4f}" for coord in bbox])
        return f"asset_{clean_timestamp}_{coords_str}_{pixel_size}"
    
    def check(self, capture_date: str, bbox: list, pixel_size) -> dict:
        """Scans master registry for existing file (after getting metadata / capture date)"""
        search_key = self._create_search_key(capture_date, bbox, pixel_size)
        if search_key in self.manifest:
            file_identifier = self.manifest[search_key]
            img_path = os.path.join(self.cache_dir, f"{file_identifier}.png")
            meta_path = os.path.join(self.cache_dir, f"{file_identifier}.json")

            if os.path.exists(img_path) and os.path.exists(meta_path):
                print(f"CACHE file found for {capture_date}, using historical asset.")
                with open(meta_path, 'r') as f:
                    loaded_metadata = json.load(f)
                return {
                    'image_array': np.array(Image.open(img_path)),
                    "metadata": loaded_metadata
                }
        return None
    
    def _generate_asset_identifier(self, metadata: dict, bbox: list, pixel_size) -> str:
        """File naming calculations in RAM"""
        clean_date = metadata['capture_date'].split(" ")[0]
        min_lon, min_lat, max_lon, max_lat = bbox 
        center_lat = (min_lat + max_lat) / 2.0
        center_lon = (min_lon + max_lon) / 2.0 
        return f"asset_{clean_date}_{center_lat:.4f}_{center_lon:.4f}_{pixel_size}"
    
    def _write_assets_to_disk(self, asset_id: str, rgb_array: np.ndarray, metadata: dict) -> tuple:
        """Local Storage file streams"""
        img_path = os.path.join(self.cache_dir, f"{asset_id}.png")
        meta_path = os.path.join(self.cache_dir, f"{asset_id}.json")
        if not os.path.exists(img_path):
            Image.fromarray(rgb_array).save(img_path)
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=4)

        return img_path, meta_path

    def save(self, capture_date: str, bbox: list, rgb_array: np.ndarray, metadata: dict, pixel_size: int = 512) -> None:
        """Saves rgb and metadata assets by capture date and updates registry"""
        search_key = self._create_search_key(capture_date, bbox, pixel_size)
        asset_identifier = self._generate_asset_identifier(metadata, bbox, pixel_size)
        self._write_assets_to_disk(asset_identifier, rgb_array, metadata)
        #Updates master registry
        self.manifest[search_key] = asset_identifier
        self._save_manifest()
