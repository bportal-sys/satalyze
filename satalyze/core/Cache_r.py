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
from typing import Dict, Optional, Tuple
import pandas as pd
from .SatalyzeDatabase import SatalyzeDatabaseManager
import logging

logger = logging.getLogger(__name__)

class SatalyzeCache_r:
    def __init__(self, db: SatalyzeDatabaseManager, cache_dir: str = 'raw_image_cache', label_dir: str = 'label_image_cache'):
        self.db = db
        self.cache_dir = cache_dir
        self.label_dir = label_dir

        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.label_dir, exist_ok=True)

    def generate_paths(self, exact_capture_date: str, lat: float, lon: float, pixel_size: int) -> Tuple[str, str]:
        """Both raw and label image paths"""
        clean_date = exact_capture_date.split(" ")[0]
        asset_base = f"asset_{clean_date}_{lat:.4f}_{lon:.4f}_{pixel_size}"
        return (
            os.path.join(self.cache_dir, f"{asset_base}.png"),
            os.path.join(self.label_dir, f"{asset_base}.png")
        )

    async def resolve_condition(self, raw_path: str, label_path: str, force_refresh: bool) -> Tuple[int, Optional[dict]]:
        """
        Cache availability and condition evaluation

        Condition 1: Full hit(both raw and labeld images found)
        Condition 2: Partial hit (found api hit but missing labeled image, call YOLO model)
        Condition 3: Miss (found nothing, run full pipeline API and YOLO)
        Condition 4: Force overwrite (ignore cache and write new info to db)
        """
        if force_refresh:
            return 4, None
        
        combined_db = await self.db.fetch_combined_raw_data()
        if combined_db.empty:
            return (2 if os.path.exists(raw_path) else 3), None
        
        matches = combined_db[
            (combined_db['raw_image_save_path'] == raw_path) & 
            (combined_db['label_image_save_path'] == label_path)
        ]

        if not matches.empty and os.path.exists(raw_path) and os.path.exists(label_path):
            return 1, matches.iloc[0].to_dict()
            
        elif os.path.exists(raw_path):
            return 2, None

        return 3, None
        