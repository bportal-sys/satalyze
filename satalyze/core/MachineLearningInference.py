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
from .MLEnhancements import ML_Enhancements
from pathlib import Path

# ===============================================
# Abstract class for Machine learning Interface layers

class MachineLearningInference(ABC):
    """Base Class for Machine Inference Layer"""

    def _normalize_input_format(self, source_input: Union[str, np.ndarray]) -> np.ndarray:
        """Mormalized input to allow both saved images and numpy arrays"""
        if isinstance(source_input, str):
            if not os.path.exists(source_input):
                raise FileNotFoundError(f'No local file found under {source_input}')
            img = cv2.imread(source_input)
            if img is None:
                raise ValueError(f'Failed to decode image at path {source_input}')
            return img
        elif isinstance(source_input, np.ndarray):
            if source_input.shape[-1] == 4:
                source_input = source_input[:, :, :3]
            bgr_img = cv2.cvtColor(source_input, cv2.COLOR_RGB2BGR)
            return bgr_img.copy()
        else: 
            raise TypeError("Source must be string path or valid numpy array")

    @abstractmethod
    def detect_vehicles(self, image_souce: Union[str, np.ndarray], confidence:float) -> Dict:
        """Placeholder for detecting vehicles | main ML inference layer"""
        pass


#============================================
# Machine Learning dectection providers with SAHI
#==========
# Single
class MachineInference_YOLO_Provider_Single(MachineLearningInference):
    """Machine Learning inference layer via YOLO model | Hard count"""
    def __init__(self, model_weights: str = 'franken_yolo11n_obb.pt', slice_size: int=512, confidence: float = 0.20, apply_enhancements: bool = False, device: str = 'cpu'):
        self.slice_size = slice_size
        self._history_buffer = []
        self.apply_enhancements = apply_enhancements
        self.enhancer = ML_Enhancements()

        current_file = Path(__file__).resolve()
        package_root = current_file.parent.parent
        self.model_dir = package_root / 'models'
        model_path_str = os.path.join(self.model_dir, f"{model_weights}")
        self.model = AutoDetectionModel.from_pretrained(
            model_type='ultralytics',
            model_path = model_path_str,
            confidence_threshold=confidence, # edit SAHI confidence instead
            device = device
        )

    def clear_ml_memory(self):
        self._history_buffer = []

    def detect_vehicles(self, image_source: Union[str, np.ndarray], confidence: float = 0.25, overlap_ratio: float = 0.2) -> Dict:
        raw_bgr = self._normalize_input_format(image_source)
        # Enhancements | bool flag 
        inference_image = self.enhancer.enhance_pipeline(raw_bgr) if self.apply_enhancements else raw_bgr

        sahi_results = get_sliced_prediction(
            inference_image, self.model, 
            slice_height=self.slice_size, slice_width=self.slice_size, 
            overlap_height_ratio=overlap_ratio, overlap_width_ratio=overlap_ratio, 
            perform_standard_pred=False, verbose=0
        )

        filtered_predictions = [p for p in sahi_results.object_prediction_list if p.score.value >= confidence]
        car_count = len(filtered_predictions)

        self._history_buffer.append(car_count)

        return {
            "display_string": f"Detected Cars: {car_count}",
            "primary_count": car_count,
            "predictions_to_draw": filtered_predictions,
            "metadata_payload": {
                "strict_count": car_count,
                "lenient_count": len(filtered_predictions)
            },
            "database_payload": {
                "timestamp": datetime.now(),
                'count_mean': None,
                'count_st_dev': None,
                'hard_count': car_count,
            }
        }

# ==============================================
# Probability class
class MachineInference_YOLO_Provider_Probability(MachineLearningInference):
    """Machine Learning inference layer via YOLO model | Hard count"""
    def __init__(self, model_weights: str = 'franken_yolo11n_obb.pt', slice_size: int=512, apply_enhancements: bool = False, device: str = 'cpu'):
        self.slice_size = slice_size
        self.apply_enhancements = apply_enhancements
        self.enhancer = ML_Enhancements()
        self.model_dir = "./models"
        model_path_str = os.path.join(self.model_dir, f"{model_weights}")
        self.model = AutoDetectionModel.from_pretrained(
            model_type='ultralytics',
            model_path = model_path_str,
            confidence_threshold=0.1,
            device = device
        )

        
    def _extract_statistics(self, predictions):
        probabilities = np.array([p.score.value for p in predictions])

        if len(probabilities) == 0:
            return {
                    "mean_count": 0.0,
                    "std": 0.0,
                    "min_likely_cars": 0.0,
                    "max_likely_cars": 0.0,
                    'variance': 0.0
                }
    
        mean_count = float(np.sum(probabilities))
        variance = float(np.sum(probabilities * (1.0 - probabilities)))
        std = float(np.sqrt(variance))
        min_likely_cars = int(max(0, round(mean_count - (2 * std))))
        max_likely_cars = int(round(mean_count + (2 * std)))
        return {
            'mean_count': mean_count,
            'std': std,
            'min_likely_cars': min_likely_cars,
            'max_likely_cars': max_likely_cars,
            'variance': variance,
        }

    def detect_vehicles(self, image_source: Union[str, np.ndarray], confidence: float = 0.25, overlap_ratio: float = 0.2) -> Dict:
        raw_bgr = self._normalize_input_format(image_source)
        # Enhancements | bool flag 
        inference_image = self.enhancer.enhance_pipeline(raw_bgr) if self.apply_enhancements else raw_bgr

        sahi_results = get_sliced_prediction(
            inference_image, self.model, 
            slice_height=self.slice_size, slice_width=self.slice_size, 
            overlap_height_ratio=overlap_ratio, overlap_width_ratio=overlap_ratio, 
            perform_standard_pred=False, verbose=0
        )


        predictions = sahi_results.object_prediction_list
        
        stats = self._extract_statistics(predictions)
        
        mean_count = stats['mean_count']
        std = stats['std']
        min_likely_cars = stats['min_likely_cars']
        max_likely_cars = stats['max_likely_cars']
        variance = stats['variance']

        boxes_to_draw = [p for p in predictions if p.score.value >= confidence]

        return {
            'display_string': f"Estimated Cars: {min_likely_cars} - {max_likely_cars} cars | Mean ± standard deviation: {mean_count} ± {std}",
            'primary_count': int(round(mean_count)),
            'predictions_to_draw': boxes_to_draw,
            "metadata_payload": {
                "mean": mean_count,
                "std": std,
                "min_likely": min_likely_cars,
                "max_likely": max_likely_cars
                },
            "database_payload": {
                "timestamp": datetime.now(),
                'count_mean': mean_count,
                'count_st_dev': std,
                'hard_count': None,
            }
            }
