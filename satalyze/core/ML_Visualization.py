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

#===========================================================
# Visualization engine
class MachineLearning_Visualization:
    """Draws geometric masks/text on pixel canvases"""
    def __init__(self):
        pass
        

    def _normalize_image(self, image_source: np.ndarray):
        if isinstance(image_source, str):
            canvas = cv2.imread(image_source)
        elif isinstance(image_source, np.ndarray):
            if image_source.shape[-1] == 4:
                image_source = image_source[:, :, :3]
            bgr_img = cv2.cvtColor(image_source, cv2.COLOR_RGB2BGR)
            canvas = bgr_img.copy()
            
        return canvas

    def _draw_bounding_boxes(self, canvas: np.ndarray, predictions: list) -> None:
        for pred in predictions:
            points = None
            
            # explicit polygon
            if hasattr(pred, 'polygon') and pred.polygon is not None:
                points = np.array(pred.polygon.points, dtype=np.int32)
                
            # points from sahi mask object
            elif hasattr(pred, 'mask') and pred.mask is not None:
                mask_obj = pred.mask
                
                # sahi boolean mask
                if hasattr(mask_obj, 'bool_mask') and mask_obj.bool_mask is not None:
                    # mask to 8-bit image 
                    mask_img = (mask_obj.bool_mask * 255).astype(np.uint8)
                    
                    # contour paths around the mask shape
                    contours, _ = cv2.findContours(mask_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    if contours:
                        # largest contour 
                        largest_contour = max(contours, key=cv2.contourArea)
                        
                        # tight obb
                        rect = cv2.minAreaRect(largest_contour)
                        points = np.int32(cv2.boxPoints(rect))
                        

            # draw points
            if points is not None and len(points) > 0:
                points = points.reshape((-1, 1, 2))
                cv2.polylines(canvas, [points], isClosed=True, color=(0, 255, 0), thickness=1)
                continue  
                

            if hasattr(pred, 'bbox') and pred.bbox is not None:
                bbox = pred.bbox #Object (each car, not long and lat)
                if hasattr(bbox, 'xmin'):
                    x1, y1, x2, y2 = int(bbox.xmin), int(bbox.ymin), int(bbox.xmax), int(bbox.ymax)
                elif hasattr(bbox, 'minx'):
                    x1, y1, x2, y2 = int(bbox.minx), int(bbox.miny), int(bbox.maxx), int(bbox.maxy)
                else:    
                    x1, y1, x2, y2 = int(bbox.val[0]), int(bbox.val[1]), int(bbox.val[2]), int(bbox.val[3])
                cv2.rectangle(canvas, (x1,y1), (x2,y2), (0, 255, 0), 1)


    def _draw_metadata_banner(self, canvas: np.ndarray, text_overlay: str) -> None:
        cv2.rectangle(canvas, (10, 5), (250, 40), (0, 0, 0), -1)
        cv2.putText(canvas, text_overlay, (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


    def generate_labeled_image(self, image_source: np.ndarray, ml_output: Dict, metadata: dict, stamp_meta: bool = False) -> dict:
        canvas = self._normalize_image(image_source=image_source)    
        
        predictions = ml_output['predictions_to_draw']
        text_overlay = ml_output["display_string"]

        # Loop over prediction list
        self._draw_bounding_boxes(canvas, predictions)
        
        if stamp_meta:
            self._draw_metadata_banner(canvas, text_overlay)

        final_disk_path = None

        rgb_canvas=cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        
        return {
            "image_array": rgb_canvas,
        }
