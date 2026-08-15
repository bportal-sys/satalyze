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
from PIL import Image
from IPython.display import display
import matplotlib.pyplot as plt
from pathlib import Path
from .SatelliteProvider import GoogleEarthEngineProvider
from .MachineLearningInference import MachineInference_YOLO_Provider_Single
from .ML_Visualization import MachineLearning_Visualization
from .CarDetectionLogging import CarDetectionLogging
from .DF_Plotter import CarTrafficPlotter
from .DF_Plotter import CyberpunkFuturisticTheme
from .DF_Plotter import CleanClassicTheme


class SatelliteTrafficPipeline:
    """
    Main Orchestrator Class that stitches together GEE Cloud downloading,
    YOLO Inference, Data Logging, Disk Asset Saving, and Swappable Plotting.
    """
    def __init__(self, project_id: str = "satalyze", output_csv: str = "master_car_detections.csv"):
        self.project_id = project_id
        self.output_csv = output_csv
        
        self.cache_dir = Path("satellite_cache")
        self.labeled_dir = Path("labelled_imgs")
        
        # generate folders if applicable
        self.cache_dir.mkdir(exist_ok=True)
        self.labeled_dir.mkdir(exist_ok=True)
        
        self.provider = GoogleEarthEngineProvider(project_id=self.project_id)
        self.ml_layer = MachineInference_YOLO_Provider_Single(apply_enhancements=False)
        self.visualizer = MachineLearning_Visualization(label_dir="labelled_imgs")
        
        self.data_logger = CarDetectionLogging()
        self.plotter = CarTrafficPlotter(theme=CyberpunkFuturisticTheme())

    def run(self, center_coordinates: list, start_date: str, end_date: str, limit: int = 5, save_to_csv: bool = True):
        """
        Executes the entire end-to-end pipeline run sequence.
        
        Parameters:
        center_coordinates -> List [longitude, latitude]
        start_date         -> String format "YYYY-MM-DD"
        end_date           -> String format "YYYY-MM-DD"
        limit              -> Max number of images to pull and process
        save_to_csv        -> Set True to write updates out to disk storage
        """
        print(f"\nPIPELINE STARTING FOR COORDINATES: {center_coordinates}")
        print(f"TIMEFRAME TARGETS: {start_date} -> {end_date}")
        
        # Connect to GEE
        self.provider.connect()
        
        try:
            # Download image payloads
            payloads = self.provider.download_patch(
                start_date=start_date, 
                end_date=end_date, 
                center=center_coordinates,
                threshold=0.001,
                limit=limit
            )
            
            total_images = len(payloads)
            if total_images == 0:
                print("PIPELINE ALERTER: Zero valid imagery datasets located. Aborting.")
                return None
                
            print(f"INGESTION LOG: Retrieved {total_images} active imagery patch(es).")

            # Analysis single pass
            for idx, patch in enumerate(payloads):
                print(f"\n[Processing Patch {idx + 1}/{total_images}]")
                metadata = patch['metadata']
                image_canvas = patch['image_array']
                
                #ml layer
                ml_report = self.ml_layer.detect_vehicles(image_canvas, confidence=0.01)
                detected_cars = ml_report['primary_count']
                print(f" -> Computer Vision Metric: Found {detected_cars} items.")
                
                #entry into DataFrame buffer
                self.data_logger.log_detection(
                    metadata=metadata, 
                    car_count=detected_cars
                )
               
                # box canvas export
                render_results = self.visualizer.generate_labeled_image(
                    image_source=image_canvas, 
                    ml_output=ml_report, 
                    metadata=metadata,
                    save_image=True,
                )
                
                # Display
                display(Image.fromarray(render_results["image_array"]))
                print("-" * 50)

            # tables and save
            compiled_dataframe = self.data_logger.get_dataframe()
            print("\nPIPELINE RUN COMPLETED. GENERATED TABLE:")
            print(compiled_dataframe)
            
            if save_to_csv:
                self.data_logger.save_to_csv(file_path=self.output_csv, append=False)
            
            #plotting 
            chart_title = f"Telemetry Log // Target: {center_coordinates}"
            self.plotter.plot_timeline_from_dataframe(df=compiled_dataframe, title=chart_title)
            
            return compiled_dataframe

        except Exception as e:
            print(f"\nCRITICAL PIPELINE CRASH FAILURE: {e}")
            return None
        


    def app_run(self, center_coordinates: list, start_date: str, end_date: str, limit: int = 5, save_to_csv: bool = True):
        """
        Executes the entire end-to-end pipeline run sequence.
        
        Parameters:
        center_coordinates -> List [longitude, latitude]
        start_date         -> String format "YYYY-MM-DD"
        end_date           -> String format "YYYY-MM-DD"
        limit              -> Max number of images to pull and process
        save_to_csv        -> Set True to write updates out to disk storage
        """
        print(f"\nPIPELINE STARTING FOR COORDINATES: {center_coordinates}")
        print(f"TIMEFRAME TARGETS: {start_date} -> {end_date}")
        
        # Connect to GEE
        self.provider.connect()
        
        try:
            # Download image payloads
            payloads = self.provider.download_patch(
                start_date=start_date, 
                end_date=end_date, 
                center=center_coordinates,
                threshold=0.001,
                limit=limit
            )
            
            total_images = len(payloads)
            if total_images == 0:
                print("PIPELINE ALERTER: Zero valid imagery datasets located. Aborting.")
                return None
                
            print(f"INGESTION LOG: Retrieved {total_images} active imagery patch(es).")

            raw_images = []
            labeled_images = []

            # Analysis single pass
            for idx, patch in enumerate(payloads):
                print(f"\n[Processing Patch {idx + 1}/{total_images}]")
                metadata = patch['metadata']
                image_canvas = patch['image_array']

                raw_images.append(image_canvas)
                
                #ml_layer
                ml_report = self.ml_layer.detect_vehicles(image_canvas, confidence=0.01)
                detected_cars = ml_report['primary_count']
                print(f" -> Computer Vision Metric: Found {detected_cars} items.")
                
                #parameters into DataFrame buffer
                self.data_logger.log_detection(
                    metadata=metadata, 
                    car_count=detected_cars
                )
               
                #box canvas
                render_results = self.visualizer.generate_labeled_image(
                    image_source=image_canvas, 
                    ml_output=ml_report, 
                    metadata=metadata,
                    save_image=True,
                )
                
                # Display
                labeled_images.append(render_results["image_array"])

            # tables and save
            compiled_dataframe = self.data_logger.get_dataframe()
            print("\nPIPELINE RUN COMPLETED. GENERATED TABLE:")
            print(compiled_dataframe)
            
            if save_to_csv:
                self.data_logger.save_to_csv(file_path=self.output_csv, append=True)
            
            # plotting 
            chart_title = f"Telemetry Log Target: {center_coordinates}"
            self.plotter.plot_timeline_from_dataframe(df=compiled_dataframe, title=chart_title)
            
            fig = plt.gcf()

            return {
                'dataframe': compiled_dataframe,
                'unlabeled': raw_images,
                'labeled': labeled_images,
                'figure': fig
            }

        except Exception as e:
            print(f"\nCRITICAL PIPELINE CRASH FAILURE: {e}")
            return None