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
import time 
import json
import requests
import numpy as np
import ee 
from PIL import Image
from abc import ABC, abstractmethod
from typing import Union, List, Dict, Tuple, Any

from .GeospatialValidator import GeospatialValidator
from .MetaDataProcessor import SatelliteMetadataProcessor

import logging

logger = logging.getLogger(__name__)


# ==================================================
# Satellite Provider Base class 
class SatelliteProvider(ABC):
    """Base Class for Satellite Providers"""

    @abstractmethod
    def connect(self) -> None:
        """Placeholder for Authentication ans Initialization"""
        pass

    @abstractmethod
    def get_image_catalog(self, start_date: str, end_date: str, bbox: list = None, center: list = None, threshold: float = 0.001) -> tuple:
        """Fetchs patch for timeframe and location as Numpy Array"""
        pass

    @abstractmethod
    def get_patch(self, img_meta: dict, aoi: Any, pixel_size: int) -> np.ndarray:
        """Fetchs patch for timeframe and location as Numpy Array"""
        pass

# ===============
# Google Earth Engine Authentication Class
# class GoogleEarthEngineAuthenticator:
#     """Manages credentials and authentication for google earth engine"""
#     def __init__(self, project_id: str = None):
#         self.project_id = project_id

#     def authenticate_interactive(self) -> None:
#         """Localhost browser authentication"""
#         try: 
#             ee.Authenticate(auth_mode='localhost')
#         except Exception as err:
#             logger.exception(f"Failied to authenticate GEE: {err}")
#             raise ConnectionError(f"Failied to authenticate GEE: {err}")
        
#     def initialize_session(self) -> bool: 
#         """Attempts silent handshake with active credentials on host OS"""
#         try:
#             ee.Initialize(project=self.project_id)
#             return True
#         except Exception:
#             return False


class GoogleEarthEngineAuthenticator:
    """Manages credentials and authentication for google earth engine"""
    def __init__(self, project_id: str = None):
        self.project_id = project_id

    def is_containerized(self) -> bool:
        return os.path.exists('/.dockerenv')
    
    def authenticate_interactive(self) -> None:
        """Localhost browser authentication"""
        mode = 'notebook' if self.is_containerized() else 'localhost'
        try: 
            ee.Authenticate(auth_mode=mode, force = True)
        except Exception as err:
            logger.exception(f"Failied to authenticate GEE: {err}")
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

    def __init__(self, project_id: str = None, max_daily_calls:int=10): 
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

    def connect(self) -> bool:
        """Connects to Google Earth Engine"""
        if self.auth.initialize_session():
            self._connected = True
            logger.info('Connected to Google Earth Engine successfully. Proceed.')
            return True
        
        logger.warning('No local GEE credentials found. Trying browser authentication.')

        try: 
            self.auth.authenticate_interactive()

            if self.auth.initialize_session():
                if self.verify_project_id():
                    self._connected = True
                    logger.info('Connected to Google Earth Engine successfully. Proceed.')
                    return True
            return False
        except Exception as e:
            self._connected = False
            logger.exception(f"GEE handshake rejected after browser completion {e}")
            if "invalid" in str(e) or "does not exist" in str(e):
                raise ValueError(str(e))
            raise ConnectionError(f"GEE handshake rejected after browser completion {e}")


    def _query_GEE_collection(self, start_date: str, end_date: str, bbox: list[float], limit: int) -> Tuple[List[dict], Any]:
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
            logger.exception(f"Database query failed: Ensure location has NAIP coverage for this timeframe. Details: {GEE_error}")        
            raise LookupError(f"Database query failed: Ensure location has NAIP coverage for this timeframe. Details: {GEE_error}")        


    def _get_thumb_URL(self, target_image: Any, aoi: Any, pixel_size: int = 512) -> str:
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
            logger.exception(f'Unable to fetch ThumbURL: {gee_error}')
            raise RuntimeError(f'Unable to fetch ThumbURL: {gee_error}')


    def _grab_request_numpy_array(self, url: str ) -> np.ndarray:
        """Grabs request URL and returns numpy array"""
        try:
            response = requests.get(url, timeout=45)
            if response.status_code != 200:
                logger.exception(f'Server rejected with status {response.status_code}')
                raise ConnectionError(f'Server rejected with status {response.status_code}')
            img = Image.open(io.BytesIO(response.content))
            return np.array(img)
        except Exception as e:
            logger.exception(f'Unable to grab numpy array {e}')
            raise RuntimeError(f'Unable to grab numpy array {e}')


    def get_image_catalog(self, start_date: str, end_date: str, bbox: list[float] = None, center: list[float] = None, threshold: float = 0.001, ignore_validators: bool = False, limit: int = 1) -> Tuple[List[dict], Any, List[float], dict, int]:
        """
        Fetches metadata using either a hard bounding box OR a center point.
        Parameters:
            bbox (list): [min_lon, min_lat, max_lon, max_lat]
            center (list): [longitude, latitude]
            threshold (float): Degree distance from center to edge (default 0.001 creates a 0.002 span)
        """
        if not self._connected:
            logger.exception("Provider not connected. Connect to active GEE project first")
            raise RuntimeWarning("Provider not connected. Connect to active GEE project first")
        
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
            logger.warning("WARNING Safey validators bypassed via override flag. Monitor EECU usage carefully. Proceeding in 5 seconds.")
            time.sleep(5)
 
        
        #First GEE Call (Metadata)
        batch_metadata_info, aoi = self._query_GEE_collection(start_date, end_date, calculated_bbox, limit)
        available_image_count = len(batch_metadata_info)
        if available_image_count == 0:
            logger.exception("No NAIP imagery found for this timeframe and location")
            raise LookupError("No NAIP imagery found for this timeframe and location")
        else: 
            logger.info(f"Found {available_image_count} image(s). Proceeding.")

        return batch_metadata_info, aoi, calculated_bbox, ground_metrics, pixel_size
    

    def get_patch(self, img_meta: dict, aoi: Any, pixel_size: int = 512) -> np.ndarray:
        """
        Fetches NAIP Imagery using either a hard bounding box OR a center point.
        Parameters:
            bbox (list): [min_lon, min_lat, max_lon, max_lat]
            center (list): [longitude, latitude]
            threshold (float): Degree distance from center to edge (default 0.001 creates a 0.002 span)
        """
        self.validator.check_quota_limit(self._calls_made)
        logger.info(f"Requesting pixel arrays from GEE cloud for {img_meta.get('id')}")
        
        raw_target_image = ee.Image(img_meta['id'])
        target_image = raw_target_image.select(['R','G','B'])
        url = self._get_thumb_URL(target_image, aoi, pixel_size)
        rgb_visual_array = self._grab_request_numpy_array(url)

        self._calls_made += 1
        logger.info(f"API request success({self._calls_made}/{self.validator.max_daily_calls})")

        return rgb_visual_array


    def verify_project_id(self) -> bool:
        """
        Runs a lightweight pre-flight NAIP query to verify if the 
        Google Cloud Project ID exists and is actively authorized.
        """
        import ee
        try:
            # 1. Build a dummy microscopic bounding box to test the channel
            dummy_bbox = [-75.40, 40.08, -75.39, 40.09]
            aoi = ee.Geometry.Rectangle(dummy_bbox)
            
            # 2. Query a single frame from the NAIP catalog
            test_collection = (ee.ImageCollection('USDA/NAIP/DOQQ')
                                .filterBounds(aoi)
                                .limit(1))
            
            # 3. Force a live server handshake using .getInfo()
            # If the project ID is wrong, this line raises an EEException instantly!
            test_collection.toList(1).getInfo()
            return True
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Pre-flight verification query rejected: {error_str}")
            # Explicitly raise a clean ValueError for Shiny to intercept
            if "not found" in error_str.lower() or "denied" in error_str.lower() or "400" in error_str:
                raise ValueError(f"Google Cloud Error: The Project ID '{self.project_id}' does not exist or has been denied permissions.")
            raise ConnectionError(f"Handshake validation failure: {error_str}")
    
