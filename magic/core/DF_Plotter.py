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

class PlotThemeBase:
    """Base class defining what colors and fonts a theme must provide."""
    def __init__(self):
        self.mpl_style = "default"
        self.bg_color = "#ffffff"
        self.line_color = "#1f77b4"
        self.glow_color = None
        self.node_color = "#1f77b4"
        self.grid_color = "#e0e0e0"
        self.spine_color = "#cccccc"
        self.title_color = "#000000"
        self.label_color = "#333333"
        self.font_name = "sans-serif"

class CyberpunkFuturisticTheme(PlotThemeBase):
    """Sleek neon dark-mode style theme."""
    def __init__(self):
        super().__init__()
        self.mpl_style = "dark_background"
        self.bg_color = "#0d0e15"      
        self.line_color = "#00ffcc"   
        self.glow_color = "#00ffcc"   
        self.node_color = "#ff0055"   
        self.grid_color = "#1a1c2e"   
        self.spine_color = "#1a1c2e" 
        self.title_color = "#ff0055"  
        self.label_color = "#8f93b3"   
        self.font_name = "Courier New" 

class CleanClassicTheme(PlotThemeBase):
    """Standard, professional light-mode report style theme."""
    def __init__(self):
        super().__init__()
        self.mpl_style = "seaborn-v0_8-whitegrid"
        self.bg_color = "#ffffff"
        self.line_color = "#0066cc"
        self.glow_color = None
        self.node_color = "#0066cc"
        self.grid_color = "#f0f0f0"
        self.spine_color = "#dddddd"
        self.title_color = "#111111"
        self.label_color = "#555555"
        self.font_name = "Arial"


class CarTrafficPlotter:
    """Core plotting engine that draws charts using a swappable style theme."""
    def __init__(self, theme: PlotThemeBase = None):
        # Default to futuristic theme
        self.theme = theme if theme is not None else CyberpunkFuturisticTheme()

    def set_theme(self, theme: PlotThemeBase):
        """Allows you to switch styles on the fly."""
        self.theme = theme

    def plot_timeline_from_dataframe(self, df: pd.DataFrame, title: str = "SYS_VEHICLE_LOG // DETECTED_UNITS"):
        """Generates a visualization using the active theme parameters."""
        if df.empty:
            print("WARNING: Cannot plot. The provided DataFrame is completely empty.")
            return

        # data format 
        plot_df = df.copy()
        plot_df['date'] = pd.to_datetime(plot_df['date'])
        plot_df = plot_df.sort_values('date')

        # Matplotlib base style
        plt.style.use(self.theme.mpl_style)
        fig, ax = plt.subplots(figsize=(11, 5), facecolor=self.theme.bg_color)
        ax.set_facecolor(self.theme.bg_color)

        # trend line data
        if self.theme.glow_color:
            ax.plot(
                plot_df['date'], plot_df['car_count'],
                color=self.theme.glow_color, alpha=0.3, linewidth=6, zorder=1
            )
            
        # main tracking line
        ax.plot(
            plot_df['date'], plot_df['car_count'],
            marker='o', linestyle='-', 
            color=self.theme.line_color, 
            linewidth=2, 
            markersize=6, 
            markerfacecolor=self.theme.node_color, 
            markeredgecolor=self.theme.line_color, 
            zorder=2
        )

        # Theme
        ax.grid(True, which='both', color=self.theme.grid_color, linestyle='--', linewidth=0.8)
        for spine in ['top', 'bottom', 'left', 'right']:
            ax.spines[spine].set_color(self.theme.spine_color)
            ax.spines[spine].set_linewidth(1.5)

        ax.set_title(title.upper(), fontsize=13, fontweight='bold', color=self.theme.title_color, pad=20, fontname=self.theme.font_name)
        ax.set_xlabel("// SOURCE_TIMELINE_COORDINATES", fontsize=10, color=self.theme.label_color, labelpad=12, fontname=self.theme.font_name)
        ax.set_ylabel("// TOTAL_UNIT_COUNT", fontsize=10, color=self.theme.label_color, labelpad=12, fontname=self.theme.font_name)
        
        ax.tick_params(colors=self.theme.label_color, labelsize=9)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontname(self.theme.font_name)

        fig.autofmt_xdate() 
        plt.tight_layout()
        plt.show()

    def plot_timeline_from_csv(self, file_path: str = "car_detections.csv", title: str = "SYS_VEHICLE_LOG // DETECTED_UNITS"):
        """Loads a stored CSV file and runs it through the themed plotter."""
        if not os.path.exists(file_path):
            print(f"ERROR: Could not find any file located at path: {file_path}")
            return
        df = pd.read_csv(file_path)
        self.plot_timeline_from_dataframe(df, title=title)
