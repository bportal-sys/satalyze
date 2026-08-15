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

# ===============================
# Ml enhancement (preprocessing)
class ML_Enhancements():
    """Class for Machine Learning preprocessing"""
    def __init__(self, clipLimit: float = 3.0, tileGridSize: tuple = (4, 4)):
        self.clipLimit = clipLimit
        self.tileGridSize = tileGridSize
        self.clahe = cv2.createCLAHE(clipLimit=self.clipLimit, tileGridSize=self.tileGridSize)

    def enhance_micro_contrast(self, bgr_array: np.ndarray) -> np.ndarray:
        """Isolates Luminance (Y) channel stopping color bleeding"""
        ycrcb = cv2.cvtColor(bgr_array, cv2.COLOR_BGR2YCrCb)
        channels = list(cv2.split(ycrcb))
        channels[0] = self.clahe.apply(channels[0])
        enhanced_bgr = cv2.merge(channels)
        return cv2.cvtColor(enhanced_bgr, cv2.COLOR_YCrCb2BGR)
    
    def micro_sharpen(self, bgr_array: np.ndarray) -> np.ndarray:
        """Sharpen edges of cars"""
        kernel = np.array([[0, -1, 0],
                           [-1, 5, -1],
                           [0, -1, 0]])
        return cv2.filter2D(bgr_array, -1, kernel)

    def enhance_pipeline(self, image: np.ndarray) -> np.ndarray:
        """Runs pipeline for enhancement features"""
        processing_image = self.enhance_micro_contrast(image)
        processed_image = self.micro_sharpen(processing_image)
        return processed_image