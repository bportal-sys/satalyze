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
import asyncio
import numpy as np
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

from .SatelliteProvider import GoogleEarthEngineProvider
from .MachineLearningInference import MachineInference_YOLO_Provider_Single
from .ML_Visualization import MachineLearning_Visualization
from .CarDetectionLogging import CarDetectionLogging
from .SatalyzeDatabase import SatalyzeDatabaseManager
from .Cache_r import SatalyzeCache_r
from .AssetWriter import SatalyzeAssetWriter
from .FinancialMetricsSata import FinancialDataManager
from .StrategyViews import SatalyzeStrategyResolver

from .DF_Plotter import CarTrafficPlotter
from .DF_Plotter import CyberpunkFuturisticTheme
from .DF_Plotter import CleanClassicTheme
import logging

logger = logging.getLogger(__name__)



class SatelliteTrafficPipeline:
    """
    Main class that combines together GEE Cloud downloading,
    YOLO Inference, Data Logging, Disk Asset Saving, and Plotting.
    """


    def __init__(self, project_id: str = "satalyze", db_path: str = "satalyze.db"):
        self.project_id = project_id
        
        self.db = SatalyzeDatabaseManager(db_path = db_path)
        self.data_logger = CarDetectionLogging()
        self.cache = SatalyzeCache_r(self.db, cache_dir='raw_image_cache', label_dir= 'label_image_cache')
        self.writer = SatalyzeAssetWriter(self.db)
        self.fin_manager = FinancialDataManager()
        self.strategy_resolver = SatalyzeStrategyResolver(self.db)

        self.provider = None
        self.ml_layer = None
        self.visualizer = None
        self.plotter = None

    def inject_pipeline(self, provider = None, ml_layer = None, visualizer = None, plotter = None):    
        # Allow passing components or gracefully drop down to standard initialized library anchors standardly
        self.provider = provider if provider is not None else GoogleEarthEngineProvider(project_id=self.project_id)
        self.ml_layer = ml_layer if ml_layer is not None else MachineInference_YOLO_Provider_Single(apply_enhancements=False)
        self.visualizer = visualizer if visualizer is not None else MachineLearning_Visualization()
        self.plotter = plotter if plotter is not None else CarTrafficPlotter(theme=CyberpunkFuturisticTheme())



    async def app_run_async(self, center_coordinates: list, start_date: str, end_date: str, ticker: str, execution_mode: str = "SINGLE_STORE", asset_type: str='PUBLIC', limit: int = 5, force_refresh: bool = True, ignore_validators=False):
        """
        Executes the entire end-to-end pipeline run sequence.
        
        Parameters:
        center_coordinates -> List [longitude, latitude]
        start_date         -> String format "YYYY-MM-DD"
        end_date           -> String format "YYYY-MM-DD"
        execution_mode     -> String: 'NATIONWIDE', "SINGLE_STORE', 'BATCH', 'COMPARISON'
        limit              -> Max number of images to pull and process
        force_refresh      -> Set True to force write updates
        ignore_validators  -> dont touch unless you dare :)
        """

        logger.info(f"\nPIPELINE STARTING FOR COORDINATES: {center_coordinates}")
        await self.db.init_db()
        logger.info(f"TIMEFRAME TARGETS: {start_date} -> {end_date}")


        if asset_type == "PRIVATE":
            ticker_clean = "PRIVATE"
            is_public_entity = False
        else: 
            ticker_clean = str(ticker).upper().strip()
            is_public_entity = True

        logger.info(f"Entity Classification -> is_public_entity: {is_public_entity} | Active Name: {ticker_clean}")

        if isinstance(center_coordinates[0], list):
            # If batch array containing an inner list context arrives
            coord_target = center_coordinates[0]
        else:
            # If a single flat [lon, lat] array arrives
            coord_target = center_coordinates

        lon, lat = coord_target[0], coord_target[1]

        self.ml_layer.clear_ml_memory()
        self.data_logger.clear_buffer()
#        site_id = self.data_logger._generate_site_id(lat=lat, lon=lon)

        work_list = center_coordinates if execution_mode in ["BATCH_FLEET", "COMPARE"] else [center_coordinates]


        financial_exists = False

        if is_public_entity:
            combined_db = await self.db.fetch_combined_raw_data()

            if not combined_db.empty and 'ticker' in combined_db.columns:
                has_ticker = ticker_clean in combined_db['ticker'].values
                has_real_financial_data = combined_db['total_revenue'].notna().any() if 'total_revenue' in combined_db.columns else False
                financial_exists = has_ticker and has_real_financial_data
            else:
                financial_exists = False

            logger.info(f'Status for {ticker_clean}: {financial_exists}')

            if not financial_exists or force_refresh:
                logger.info(f"Scraping {ticker_clean}")
                try:
                    fin_df = await self.fin_manager.get_annual_metrics_async(ticker_str = ticker_clean, start_date=start_date, end_date=end_date)
                    if fin_df is None:
                        logger.warning(f"None for {ticker_clean}")
                    elif fin_df.empty:
                        logger.warning(f'Empty df for {ticker_clean}')
                    else:
                        fin_df.columns = fin_df.columns.str.replace('"', "").str.replace("'", "").str.strip()
                        await self.db.save_financial_dataframe(fin_df)
                        logger.info(f"Financial metric saved to sqlite")
                except: 
                    logger.exception(f"Failed while scraping {ticker_clean}")
                    fin_df = pd.DataFrame()
        else: 
            logger.info(f"Private asset detected skipping financials")

        fleet_site_ids = []
        raw_images, labeled_images = [], []

        for current_coord in work_list:
            lat, lon = current_coord[0], current_coord[1]
            site_id = self.data_logger._generate_site_id(lat = lat, lon = lon)
            fleet_site_ids.append(site_id)
            
            start_year = int(start_date.split("-")[0])
            await self.db.assign_site_to_lot(ticker = ticker_clean, year = start_year, site_id = site_id, lat = lat, lon = lon)

            try:
                # Connect to GEE
                self.provider.connect()
                batch_meta, aoi, calculated_bbox, ground_metrics, pixel_size = self.provider.get_image_catalog(
                    start_date=start_date, end_date=end_date, center=current_coord, limit=limit, ignore_validators = ignore_validators
                )
            except Exception:
                logger.exception(f"Failed to fetch catalog image for {current_coord}")
                continue
            

            total_images = len(batch_meta)
            if total_images == 0:
                logger.warning(f"! Zero images found")
                continue


            for img_meta in batch_meta:
                exact_capture_date = self.provider.metadata_processor.extract_capture_date(img_meta)
                capture_year = int(exact_capture_date.split("-")[0])

                raw_path, label_path = self.cache.generate_paths(exact_capture_date, lat, lon, pixel_size)

                condition, db_record = await self.cache.resolve_condition(raw_path, label_path, force_refresh)

                if condition == 1: 
                    logger.info(f"Condition 1 skipping GEE and YOLO call for {exact_capture_date}")
                    raw_canvas = np.array(Image.open(raw_path))
                    label_canvas = np.array(Image.open(label_path))
                    cars = int(db_record['car_count'])

                else:
                    if condition == 2:
                        logger.info(f"Condition 2 Raw image found skipping GEE call for {exact_capture_date}")
                        raw_canvas = np.array(Image.open(raw_path))

                    else:
                        logger.info(f"Condition {condition} | Sending out API call(s)")
                        raw_canvas = self.provider.get_patch(img_meta, aoi, pixel_size)

                    ml_report = self.ml_layer.detect_vehicles(raw_canvas, confidence=0.01)
                    cars = ml_report['primary_count']
                    
                    metadata_package = {"capture_date": exact_capture_date, "pixel_size": pixel_size, "bounding_box": calculated_bbox}
                    render_results = self.visualizer.generate_labeled_image(
                        image_source= raw_canvas, ml_output=ml_report, metadata=metadata_package,
                    )
                    label_canvas = render_results["image_array"]

                    await self.writer.save_pipeline_observation(
                        raw_canvas = raw_canvas, label_canvas = label_canvas, raw_path = raw_path, label_path = label_path,
                        site_id = site_id, year = capture_year, car_count = cars, lat = lat, lon = lon, date = exact_capture_date
                    )

                    await self.db.assign_site_to_lot(
                        ticker = ticker_clean, year = capture_year, site_id=site_id, lat = lat, lon = lon 
                    )

                self.data_logger.log_detection({"capture_date": exact_capture_date, "pixel_size":pixel_size, "bounding_box":calculated_bbox}, cars)
                raw_images.append(raw_canvas)
                labeled_images.append(label_canvas)


        # Strategy resolution routing
        if execution_mode == "NATIONWIDE" and is_public_entity:
            display_df = await self.strategy_resolver.execute_nationwide(ticker_clean)
        elif execution_mode == "SINGLE_STORE":
            display_df = await self.strategy_resolver.execute_single_store(fleet_site_ids, ticker_clean)
        elif execution_mode == "COMPARE":
            display_df = await self.strategy_resolver.execute_comparison(list(set(fleet_site_ids)))
        else:
            display_df = await self.strategy_resolver.execute_batch_fleet(fleet_site_ids, ticker_clean)

        if display_df is not None and not display_df.empty:
            display_df.columns = display_df.columns.str.replace('"','').str.replace("'","").str.strip()

            if 'ticker' in display_df.columns:
                if is_public_entity:
                    display_df['ticker'] = display_df['ticker'].astype(str).str.upper().str.strip()
                    display_df = display_df[display_df['ticker'] == ticker_clean]
                else: 
                    display_df['ticker'] = "PRIVATE"
                    for fin_col in ['total_revenue', 'capex','gross_ppe']:
                        if fin_col in display_df.columns:
                            display_df[fin_col] = 'N/A'

            display_df = display_df.reset_index(drop=True)

            if 'year' in display_df.columns:
                display_df['year'] = pd.to_numeric(display_df['year'],errors='coerce')
                start_yr = int(start_date.split("-")[0])
                end_yr = int(end_date.split("-")[0])
                display_df = display_df[(display_df['year']>= start_yr) & (display_df['year']<=end_yr)]

                display_df = display_df.drop_duplicates()
    
        # --- CLEAN ABSTRACTED PLOTTER CALL ---
        try:
            financial_df = await self.db.fetch_combined_raw_data()
            logger.info(f"Combined raw db empty status: {financial_df.empty}")
            if financial_df is not None and not financial_df.empty:
                financial_df.columns = financial_df.columns.str.replace("'","").str.replace('"',"").str.strip()
                if 'year' in financial_df.columns:
                    financial_df['year'] = pd.to_numeric(financial_df['year'],errors='coerce')
                    start_yr = int(start_date.split("-")[0])
                    end_yr = int(end_date.split("-")[0])
                    financial_df = financial_df[(financial_df['year']>= start_yr) & (financial_df['year']<=end_yr)]
        except Exception:
            logger.exception(f"Failed to read combined df")
            financial_df = pd.DataFrame()


        # ==========================================================
        # 🪵 DIAGNOSTIC LOG: See exactly what is getting passed to the plotter
        # ==========================================================
        logger.info("==================================================")
        logger.info("  FINAL PLOTTER INGESTION PROFILER (Sata_Pipeline) ")
        logger.info("==================================================")
        logger.info(f" -> Active UI Target Ticker: '{ticker_clean}'")
        logger.info(f" -> Asset Classification Type: is_public_entity={is_public_entity}")
        
        if display_df is not None and not display_df.empty:
            logger.info(f" -> Total Rows passing to chart engine: {len(display_df)}")
            logger.info(f" -> Columns visible to plotter: {list(display_df.columns)}")
            
            # Print unique values in indexing columns to trap cross-contamination bugs
            if 'ticker' in display_df.columns:
                logger.info(f" -> Unique tickers inside DataFrame: {display_df['ticker'].unique()}")
            if 'date' in display_df.columns:
                logger.info(f" -> Unique dates inside DataFrame: {display_df['date'].unique()}")
                
            logger.info("\n Raw DataFrame Payload Matrix Snapshot:")
            # Capture up to 20 rows of the payload to track the exact data structure
            for idx, row in display_df.head(20).iterrows():
                logger.info(
                    f"    [{idx}] Date: {row.get('date')} | Year: {row.get('year')} | "
                    f"Ticker: {row.get('ticker')} | Site: {row.get('site_id')} | "
                    f"Cars: {row.get('car_count')} | Rev: {row.get('total_revenue')}"
                )
        else:
            logger.warning(" -> ⚠️ CRITICAL WARNING: The DataFrame passing to the plotter is completely EMPTY!")
        logger.info("==================================================")

        # Just pass everything to the helper function!
        fig = self.plotter.generate_mode_plot(
            execution_mode=execution_mode,
            ticker_clean=ticker_clean,
            traffic_df=self.data_logger.get_dataframe(),
            display_df=display_df,
            financial_df=display_df
        )

        return {
            'dataframe': display_df,
            'unlabeled': raw_images,
            'labeled': labeled_images,
            'figure': fig
        }

############    
        # compiled_dataframe = self.data_logger.get_dataframe()
        # if not compiled_dataframe.empty:
        #     self.plotter.plot_timeline_from_dataframe(df=compiled_dataframe, title = f"Target: {ticker_clean} Timeline Log")
        # fig = plt.gcf()
        

        # return {
        #     'dataframe': display_df,
        #     'unlabeled': raw_images,
        #     'labeled': labeled_images,
        #     'figure': fig
        # }

    def app_run(self, *args, **kwargs) -> Optional[Dict]:
        """For thing like streamlit"""
        try: 
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(self.app_run_async(*args, **kwargs))
        return loop.run_until_complete(self.app_run_async(*args, **kwargs))