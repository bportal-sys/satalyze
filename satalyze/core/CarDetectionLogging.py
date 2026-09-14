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
import pandas as pd
from typing import Union, List, Dict
import logging

logger = logging.getLogger(__name__)

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

    def _generate_site_id(self, lat: float, lon: float) -> str:
        """Generates site_id for db insertion | Placed to 3 decimal places to try to bring together images if image in wrong spot force_erewrite"""
        lat_str = f"{float(lat):.3f}".replace('.', 'o')
        lon_str = f"{float(lon):.3f}".replace('.', 'o')
        return f"SITE_{lat_str}_{lon_str}"

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
            "car_count": int(car_count),
            "year": int(capture_date.split("-")[0])
        }
        self._buffer.append(record)
        self.df = pd.DataFrame(self._buffer)

    def get_dataframe(self) -> pd.DataFrame:
        """Returns the full gathered dataset."""
        return self.df
    
    def clear_buffer(self) -> None:
        """purges active memory"""
        self._buffer = []
        self.df = pd.DataFrame()

    def save_to_csv(self, file_path: str = "car_detections.csv", append: bool = True):
        """
        Saves data to a CSV file.
        
        Parameters:
        append=True  -> Adds data to the bottom of the existing file.
        append=False -> Overwrites the file or creates a brand-new one.
        """
        if self.df.empty:
            logger.warning("No data to save.")
            return

        # Check if file exists and we want to append
        if append and os.path.exists(file_path):
            # Append mode ('a'). Do not write the header
            self.df.to_csv(file_path, mode='a', header=False, index=False)
            logger.info(f"Successfully ADDED records to existing file: {file_path}")
        else:
            # Write mode ('w'). Create a new file or overwrite
            self.df.to_csv(file_path, mode = 'w', header = True, index = False)
            logger.info(f"Successfully CREATED/OVERWRITTEN file: {file_path}")
            
        self.clear_buffer()