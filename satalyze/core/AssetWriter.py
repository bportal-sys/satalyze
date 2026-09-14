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
import numpy as np
from PIL import Image
from .SatalyzeDatabase import SatalyzeDatabaseManager
import logging

logger = logging.getLogger(__name__)

class SatalyzeAssetWriter:
    """Image(s) to disk and metadata to db"""
    def __init__(self, db: SatalyzeDatabaseManager):
        self.db = db

    async def save_pipeline_observation(self, raw_canvas: np.ndarray, label_canvas: np.ndarray, raw_path: str, label_path: str,
                                        site_id: str, year: int, car_count: int, lat: float, lon: float, date) -> bool:
        """Writes Images to disk and metadata to db using text paths fo images"""
        try: 
            os.makedirs(os.path.dirname(raw_path), exist_ok = True)
            os.makedirs(os.path.dirname(label_path), exist_ok = True)


            Image.fromarray(raw_canvas).save(raw_path)
            Image.fromarray(label_canvas).save(label_path)


            db_success = await self.db.insert_streaming_observation(
                site_id = site_id, 
                year = int(year),
                car_count = float(car_count),
                total_capacity = 100,
                lat = float(lat),
                lon = float(lon),
                raw_image_save_path=raw_path,
                label_image_save_path=label_path,
                date = date
            )

            if db_success:
                logger.info(f'Successful written to database')
            else: 
                logger.warning(f'Disk save succeeded but save to database failed')
            return db_success
        
        except Exception as e:
            logger.exception(f"Failed to save assets and to database | {e}")
            return False