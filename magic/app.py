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


import sys
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

import streamlit as st
import pandas as pd
from PIL import Image
import folium
from streamlit_folium import st_folium
from folium.plugins import Geocoder  
import matplotlib.pyplot as plt
from magic.core import SatelliteTrafficPipeline


def run_app():
    st.set_page_config(page_title="Satellite Analysis Dashboard", layout="wide", page_icon="🛰️")
    st.title("Satellite Image Analysis Dashboard")
    st.write("Powered by github.com/bportal-sys")
    st.write("Click on the map to automatically capture coordinates, set your parameters, and run the pipeline.")

# Default to King of Prussia Mall
    if "clicked_lon" not in st.session_state:
        st.session_state.clicked_lon = -75.3947  
    if "clicked_lat" not in st.session_state:
        st.session_state.clicked_lat = 40.0890

    # CREATE TWO COLUMNS FOR INTERFACE
    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.subheader("1. Select Location")
        
        # interactive Map
        m = folium.Map(location=[st.session_state.clicked_lat, st.session_state.clicked_lon], zoom_start=14)
        folium.Marker(
            [st.session_state.clicked_lat, st.session_state.clicked_lon], 
            tooltip="Target Area"
        ).add_to(m)
        
        Geocoder(collapsed=False, position='topleft', placeholder="Search an address or landmark...").add_to(m)
        

        # Display map
        map_data = st_folium(m, width="100%", height=400)
        
        if map_data and map_data.get("last_clicked"):
            st.session_state.clicked_lat = map_data["last_clicked"]["lat"]
            st.session_state.clicked_lon = map_data["last_clicked"]["lng"]

        # Displayselected coordinates
        st.info(f"Selected Coordinates: **Longitude:** {st.session_state.clicked_lon:.4f}, **Latitude:** {st.session_state.clicked_lat:.4f}")

    with right_col:
        st.subheader("2. Pipeline Parameters")
        
        project_id = st.text_input("Project ID", value="satalyze")
        
        # Date Pickers
        col_start, col_end = st.columns(2)
        with col_start:
            start_date = st.date_input("Start Date", value=pd.to_datetime("2017-01-01"))
        with col_end:
            end_date = st.date_input("End Date", value=pd.to_datetime("2022-12-31"))
            
        # Plus/Minus Image Limit
        limit = st.number_input("Image Limit", min_value=1, max_value=50, value=2, step=1)
        
        st.write("---")
        # RUN BUTTON
        run_pipeline = st.button("🚀 Run Full Pipeline", use_container_width=True)

    # --- PIPELINE EXECUTION AND OUTPUTS ---
    if run_pipeline:
        with st.spinner("Executing pipeline layers... processing satellite images, running YOLO, and slicing tracking grids..."):
            try:
                # 1. Initialize pipeline class
                pipeline = SatelliteTrafficPipeline(project_id=project_id)
                
                # 2. Run the pipeline with the selected map coordinates and parameters
                results = pipeline.app_run(
                    center_coordinates=[st.session_state.clicked_lon, st.session_state.clicked_lat], # [lon, lat] order
                    start_date=str(start_date),
                    end_date=str(end_date),
                    limit=limit,
                    save_to_csv = False
                )
                

                if results is None:
                    st.error("No imagery found or the pipeline aborted.")
                else:
                    st.success("Pipeline Completed Successfully!")
                    st.write("---")

                    st.subheader("📈 Traffic Trends Over Time")
                    if isinstance(results, dict) and "figure" in results:
                        st.pyplot(results["figure"])
                    else:
                        st.pyplot(plt.gcf()) # Grabs whatever active open matplotlib graph figure exists
                    
                    
                    # DATAFRAME
                    st.subheader("📊 Analyzed Traffic Dataframe")
                    if isinstance(results, dict) and "dataframe" in results:
                        st.dataframe(results["dataframe"], use_container_width=True)
                    else:
                        st.dataframe(results, use_container_width=True) # Fallback if it returned just the dataframe
                    
                    # DISPLAY IMAGES
                    st.subheader("🖼️ Processed Satellite Imagery Patches")
                    
                    # If pipeline returned a dictionary with lists of images
                    if isinstance(results, dict) and "unlabeled" in results and "labeled" in results:
                        for i in range(len(results["unlabeled"])):
                            st.write(f"### Patch Image Bundle #{i+1}")
                            img_col1, img_col2 = st.columns(2)
                            
                            with img_col1:
                                st.image(results["unlabeled"][i], caption="Original Unlabeled Sat Patch", use_container_width=True)
                                        
                            with img_col2:
                                st.image(results["labeled"][i], caption="YOLO + SAHI Detections", use_container_width=True)
                            st.write("---")
                    else:
                        st.info("Images are being saved to your local disk folders. Move them to the results packet if you want them inside the UI!")


            except Exception as e:
                st.error(f"An error occurred while executing the core library pipeline: {e}")



if __name__ == "__main__":
    run_app()
