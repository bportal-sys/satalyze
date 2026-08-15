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
from .GeospatialValidator import GeospatialValidator
from .MetaDataProcessor import SatelliteMetadataProcessor
from .SatelliteDiskCache import SatelliteDiskCache

# ==================================================
# Satellite Provider Base class 
class SatelliteProvider(ABC):
    """Base Class for Satellite Providers"""

    @abstractmethod
    def connect(self) -> None:
        """Placeholder for Authentication ans Initialization"""
        pass

    @abstractmethod
    def download_patch(self, start_date: str, end_date:str, bbox: list = None, center: list = None, threshold: float = 0.001, save_images: bool = True) -> dict:
        """Fetchs patch for timeframe and location as Numpy Array"""
        pass

# ===============
# Google Earth Engine Authentication Class
class GoogleEarthEngineAuthenticator:
    """Manages credentials and authentication for google earth engine"""
    def __init__(self, project_id: str = None):
        self.project_id = project_id

    def authenticate_interactive(self) -> None:
        """Localhost browser authentication"""
        try: 
            ee.Authenticate(auth_mode='localhost')
        except Exception as err:
            raise ConnectionError(f"Failied to authenticate GEE: {err}")
        
    def initialize_session(self) -> bool: 
        """Attempts silent handshake with active credentials on host OS"""
        try:
            ee.Initialize(project=self.project_id)
            return True
        except Exception:
            return False

# Google Earth Engine Provider Class
class GoogleEarthEngineProvider(SatelliteProvider):
    """Google Earth Engine Satellite Provider"""

    def __init__(self, project_id: str = None, max_daily_calls:int=5): 
        #Connection
        self.project_id = project_id
        self.auth = GoogleEarthEngineAuthenticator(project_id = project_id)
        self._connected = False
        #Quota Tracking
        self._calls_made = 0
        #Validator
        self.validator = GeospatialValidator(max_daily_calls=max_daily_calls)
        #Processor
        self.metadata_processor = SatelliteMetadataProcessor()
        #Cache
        self.cache = SatelliteDiskCache()

    def connect(self) -> None:
        """Connects to Google Earth Engine"""
        if self.auth.initialize_session():
            self._connected = True
            print('Connected to Google Earth Engine successfully. Proceed.')
            return 
        
        print('No local GEE credentials found. Trying browser authentication.')
        time.sleep(1)

        self.auth.authenticate_interactive()
        if self.auth.initialize_session():
            self._connected = True
            print('Connected to Google Earth Engine successfully. Proceed.')
        else:
            raise ConnectionError("GEE handshake rejected after browser completion")
           
    def _query_GEE_collection(self, start_date: str, end_date: str, bbox: list[float], limit: int):
        """Handles communication between GEE servers for image requested"""
        try: 
            aoi = ee.Geometry.Rectangle(bbox) 
            base_collection = (ee.ImageCollection('USDA/NAIP/DOQQ')
                                .filterBounds(aoi)
                                .filterDate(start_date, end_date)
                                .select(['R','G','B']))
            
            sorted_collection = base_collection.sort('system:time_start', False)
            limited_collection = sorted_collection.limit(limit)

            batch_metadata = limited_collection.toList(limit).getInfo()
            
            return batch_metadata, aoi

        except Exception as GEE_error:
            raise LookupError(f"Database query failed: Ensure location has NAIP coverage for this timeframe. Details: {GEE_error}")
        
    def _get_thumb_URL(self, target_image, aoi, pixel_size: int = 512) -> str:
        """Grabs ThumbURL for AOI from GEE"""
        try:
            pixel_request = {
                    'image': target_image,
                    'region': json.loads(aoi.toGeoJSONString()),
                    'dimensions': f"{pixel_size}x{pixel_size}",
                    'format': 'PNG',    
                }

            return target_image.getThumbURL(pixel_request)    
        except Exception as gee_error:
            raise RuntimeError(f'Unable to fetch ThumbURL: {gee_error}')

    def _grab_request_numpy_array(self, url, ) -> str:
        """Grabs request URL and returns numpy array"""
        try:
            response = requests.get(url)
            img = Image.open(io.BytesIO(response.content))
            return np.array(img)
        except:
            raise RuntimeError('Unable to grab numpy array')
        
    def download_patch(self, start_date: str, end_date: str, bbox: list[float] = None, center: list[float] = None, threshold: float = 0.001, ignore_validators: bool = False, limit: int = 1, save_images: bool = True) -> list:
        """
        Fetches NAIP imagery and metadata using either a hard bounding box OR a center point.
        Parameters:
            bbox (list): [min_lon, min_lat, max_lon, max_lat]
            center (list): [longitude, latitude]
            threshold (float): Degree distance from center to edge (default 0.001 creates a 0.002 span)
        """
        if not self._connected:
            raise RuntimeWarning("Provider not connected.")
        
        #Necessary calculations
        calculated_bbox = self.validator.validate_switch_mode(bbox, center, threshold)
        ground_metrics = self.metadata_processor.calculate_ground_dimensions(calculated_bbox)
        pixel_size = self.validator.get_target_pixels(ground_metrics)

        #DONT IGNORE but if chosen to heres the condition
        if not ignore_validators:
            self.validator.check_time_bounds(start_date, end_date)
            self.validator.check_spatial_bounds(calculated_bbox)
            self.validator.check_ground_scale_safety(ground_metrics)
            self.validator.check_multi_limit(limit)
        else:
            print("WARNING Safey validators bypassed via override flag. Monitor EECU usage carefully. Proceeding in 5 seconds.")
            time.sleep(5)
 
        
        #First GEE Call (Metadata)
        batch_metadata_info, aoi = self._query_GEE_collection(start_date, end_date, calculated_bbox, limit)
        available_image_count = len(batch_metadata_info)
        if available_image_count == 0:
            raise LookupError("No NAIP imagery found for this timeframe and location")
        else: 
            print(f"Found {available_image_count} image(s). Proceeding.")

        #Start of loop 
        output_payloads = []    
        for idx, img_meta in enumerate(batch_metadata_info):
            self.validator.check_quota_limit(self._calls_made)    
            
            exact_capture_date = self.metadata_processor.extract_capture_date(img_meta)
            #Check cache
            cached_payload = self.cache.check(exact_capture_date, calculated_bbox, pixel_size)
            if cached_payload is not None:
                output_payloads.append(cached_payload)
                continue
            
            print(f'Attempting API request: {self._calls_made + 1}...')

            #Second GEE call
            raw_target_image = ee.Image(img_meta['id'])
            target_image = raw_target_image.select(['R','G','B'])
            url = self._get_thumb_URL(target_image, aoi, pixel_size)
            rgb_visual_array = self._grab_request_numpy_array(url)

            self._calls_made += 1
            print(f'API request {self._calls_made}/{self.validator.max_daily_calls}')

            item_payload = {
                "image_array": rgb_visual_array,
                "metadata": {
                    "capture_date": exact_capture_date,
                    "ground_dimensions": ground_metrics,
                    "bounding_box": calculated_bbox,
                    'bullshit': 'helly my friend',
                    "pixel_size": pixel_size,
                    "array_shape": list(rgb_visual_array.shape)
                }
            }

            if save_images:
                self.cache.save(exact_capture_date, calculated_bbox, rgb_visual_array, item_payload['metadata'], pixel_size)

            output_payloads.append(item_payload)

        return output_payloads
    
