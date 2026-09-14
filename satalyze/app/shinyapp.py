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
import base64
from pathlib import Path
from datetime import date
import pandas as pd
import matplotlib.pyplot as plt
import asyncio
import concurrent.futures
import nest_asyncio
nest_asyncio.apply()
from satalyze.logging_config import setup_logger
setup_logger()
import logging
logger = logging.getLogger(__name__)
from shiny import App, render, ui, reactive
from shinywidgets import render_widget, register_widget, output_widget
from ui import app_ui


try:
    from satalyze.core import SatelliteTrafficPipeline
except ImportError:
    from core import SatelliteTrafficPipeline

from tutorial import GuidedTourManager


def server(input, output, session):
    tour_manager = GuidedTourManager()

    # 🔄 Programmatic Tab Swapping Engine
    @reactive.effect
    def _handle_tour_tab_swaps():
        target_tab = tour_manager.get_current_nav_target()
        if target_tab:
            # Enforces immediate layout tab changes in the user's browser
            ui.update_navset("main_navbar", selected=target_tab)

    # 🪄 The Interactive Presentation Layer Renderer
# Inside src/satalyze/app/shinyapp.py

    # 🪄 The Interactive Presentation Layer Renderer
    @render.ui
    def tutorial_panel_overlay():
        result = tour_manager.get_ui_and_css()
        if not result:
            return None
            
        panel_html, css_rules = result
        step_idx = tour_manager.current_step()
        
        # Look up the current step's target element ID dynamically
        from satalyze.app.tutorial import TUTORIAL_STEPS
        step_data = TUTORIAL_STEPS.get(step_idx)
        target_id = step_data["target_id"] if step_data else ""

        # High-tech scrolling injector script string:
        # Automatically centers the highlighted dashboard module smoothly inside the viewport window
        scroll_js = f"""
        <script>
            setTimeout(() => {{
                const element = document.getElementById("{target_id}");
                if (element) {{
                    element.scrollIntoView({{ behavior: "smooth", block: "center" }});
                }}
            }}, 50); // Small timeout allows tab layouts to finish parsing frames before scrolling
        </script>
        """
        
        return ui.div(
            panel_html,
            ui.tags.style(css_rules),
            ui.HTML(scroll_js) # ✨ Instantly executes the scroll trigger inside the user's browser session!
        )


    # Standard tutorial action handle pointers
    @reactive.effect
    @reactive.event(input.start_tutorial)
    def _(): tour_manager.start()

    @reactive.effect
    @reactive.event(input.tut_next)
    def _(): tour_manager.next()

    @reactive.effect
    @reactive.event(input.tut_prev)
    def _(): tour_manager.prev()

    @reactive.effect
    @reactive.event(input.tut_close)
    def _(): 
        tour_manager.stop()
        # Automatically returns the user to the main page when onboarding closes
        ui.update_navset("main_navbar", selected="main_dashboard")


# 🎯 PLACE THIS AT THE VERY TOP OF YOUR SERVER FUNCTION:

    # 🗄️ Core Database Setup Point
    _boot_pipeline = SatelliteTrafficPipeline(project_id="")
    db_mgr = _boot_pipeline.db 
    
    gee_is_connected = reactive.Value(False)
    pipeline_is_running = reactive.Value(False)
    
    # 🛡️ The System Lock: Keeps auto-saves completely frozen until hydration is 100% finished
    system_hydrated = reactive.Value(False)

    # 🔗 Chronological UI Hydration Engine
    @reactive.effect
    async def _initialize_and_hydrate_system():
        try:
            # 1. Guarantee your tables exist
            await db_mgr.init_db()
            
            # 2. Extract configuration entries
            raw_id = await db_mgr.get_settings("gee_project_id", default="")
            raw_zoom = await db_mgr.get_settings("image_zoom", default="50")
            raw_limit = await db_mgr.get_settings("image_limit", default="3")

            saved_id = raw_id[0] if isinstance(raw_id, tuple) else raw_id
            saved_zoom = raw_zoom[0] if isinstance(raw_zoom, tuple) else raw_zoom
            saved_limit = raw_limit[0] if isinstance(raw_limit, tuple) else raw_limit
            

            # 3. Synchronously push values directly into your static ui.py fields
            ui.update_text("project_id", value=str(saved_id))
            ui.update_numeric("limit", value=int(saved_limit))
            ui.update_slider("image_zoom", value=int(saved_zoom))
            
            if str(saved_id).strip() and str(saved_id) != "satalyze":
                loop = asyncio.get_running_loop()
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    # ✅ FIX: Execute connection inside pool, but return the status back out
                    silent_check = lambda: _boot_pipeline.provider.connect()
                    is_alive = await loop.run_in_executor(pool, silent_check)
                    
                    # ✅ FIX: Set the value safely outside the thread boundary
                    gee_is_connected.set(is_alive)                
                
            # 4. Wait for the browser elements to completely render before unlocking the database writes
            await asyncio.sleep(0.5) 
            system_hydrated.set(True) # 🔓 SYSTEM IS UNLOCKED!
            logger.info("Saved config imported and write guard unlocked successfully.")
            
        except Exception as e:
            logger.error(f"App initialization sequence broke: {e}")

    # 💾 Auto-Save Observers: Strictly locked until hydration is completely finished
    @reactive.effect
    @reactive.event(input.project_id)
    async def _save_id():
        if not system_hydrated(): return  # Aborts write if the system is still booting up
        val = input.project_id().strip() if input.project_id() else ""
        if val:
            await db_mgr.set_settings("gee_project_id", val)

    @reactive.effect
    @reactive.event(input.image_zoom)
    async def _save_zoom():
        if not system_hydrated(): return  
        val = input.image_zoom()
        if val is not None:
            await db_mgr.set_settings("image_zoom", str(val))

    @reactive.effect
    @reactive.event(input.limit)
    async def _save_limit():
        if not system_hydrated(): return  
        val = input.limit()
        if val is not None:
            await db_mgr.set_settings("image_limit", str(val))

    @reactive.effect
    @reactive.event(input.force_auth)
    async def _handle_manual_reauthentication():
        # Grab exactly what is typed in the textbox right now
        proj_id = str(input.project_id()).strip() if input.project_id() else ""
        
        # 🎯 ANSWERING YOUR QUESTION: 
        # No more 'satalyze' check. This now ONLY triggers if the input text field is 100% empty.
        # As long as you type anything into the box, it will bypass this block completely!
        if not proj_id:
            ui.modal_show(ui.modal(
                ui.div(
                    ui.h3("🚀 Set Up Your Free Google Earth Engine Account", style="color: #f3f4f6; font-weight: 600; margin-bottom: 14px;"),
                    
                    # 💡 FIX: We wrap the Markdown engine inside a styled div container.
                    # This forces the text headers, bullets, numbers, and links to display in high-contrast off-white!
                    ui.div(
                        ui.markdown(
                            "Google Earth Engine requires a valid Google Cloud Project ID to authenticate your computer session.\n\n"
                            "**Follow these 3 quick steps to create one for free:**\n\n"
                            "1. **Sign Up:** Go to the [Google Earth Engine Signup Page](https://google.com) and log in with your Gmail.\n"
                            "2. **Select Non-Commercial:** Click *Get Started* under 'Non-Commercial Use' (Free Tier) and follow the simple registration forms.\n"
                            "3. **Create Project ID:** Google will automatically prompt you to create a project or use 'My First Project'. **Copy that Project ID name string**.\n\n"
                            "Once you have your ID, close this window, paste it into the *Advanced Settings* text field, and click **Re-Authenticate** again!"
                        ),
                        # High-contrast text configurations:
                        style="color: #e5e7eb; line-height: 1.6; font-size: 13px;"
                    ),
                    style="padding: 10px;"
                ),
                title=None, 
                easy_close=True,
                size="l" # Large viewport layout constraints
            ))
            return

        # 🟢 THE STANDARD SECURE LOGIN WORKFLOW (Runs for you because you have an ID filled out!)
        ui.modal_show(ui.modal(
            ui.div(
                ui.h3("🌐 Initializing Account Configuration Handshake", style="color: #f3f4f6; font-weight: 600;"),
                ui.p("A secure login page is opening in your browser. Select your target Google account to grant permissions.", style="color: #9ca3af; font-size: 14px;"),
                ui.markdown("<small style='color:#64748b;'>ℹ️ If running inside Docker, view your terminal logs to paste the authentication token.</small>")
            ),
            title=None, easy_close=True
        ))
        
        # Instantly update the database settings cache table with your active text input configuration
        await db_mgr.set_settings("gee_project_id", proj_id)

        # Offload interactive browser redirection to the worker pool safely
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            def force_new_token():
                # 1. Instantiate the isolated pipeline context block
                pipeline_worker = SatelliteTrafficPipeline(project_id=proj_id)
                
                # 🎯 FIX: Explicitly inject components so that pipeline_worker.provider is alive!
                pipeline_worker.inject_pipeline()
                
                # 2. Fire the connection handshake safely inside the worker pool
                return pipeline_worker.provider.connect()

            try:
                # Execution yields to thread pool
                if await loop.run_in_executor(pool, force_new_token):
                    # Turn your pipeline indicators green/active here if desired
                    ui.modal_remove() # Close notification window automatically on success
            except Exception as e:
                logger.error(f"Manual re-auth failed: {e}")
                ui.modal_remove()
                ui.modal_show(ui.modal(
                    ui.div(
                        ui.h4("❌ Google Cloud Project Verification Failed", style="color: #ef4444; font-weight: 600; margin-bottom: 12px;"),
                        ui.p("Google's authentication server explicitly rejected this configuration:", style="color: #9ca3af; font-size: 13px;"),
                        ui.div(error_msg, style="background-color: #7c2d1222; border: 1px solid #9a341244; color: #fbbf24; padding: 12px; border-radius: 4px; font-family: monospace; font-size: 12px; line-height: 1.4;"),
                        ui.p("Verify your project name spelling configurations in your Google Cloud Console dashboard before retrying.", style="color: #9ca3af; font-size: 13px; margin-top: 14px;"),
                        style="padding: 10px;"
                    ),
                    title=None,
                    easy_close=True
                ))

         
    @reactive.effect
    @reactive.event(input.test_conn)
    async def _handle_manual_connection_testing():
        proj_id = str(input.project_id()).strip() if input.project_id() else ""
        
        if not proj_id:
            ui.modal_show(ui.modal(ui.p("⚠️ Please enter a Project ID first before running a connectivity test."), title="Missing Parameter", easy_close=True))
            return

        # Show an initial diagnostic loading notice modal
        ui.modal_show(ui.modal(
            ui.div(
                ui.markdown("### 🧪 Pinging Google Cloud API Channels"),
                ui.p(f"Executing a pre-flight metadata fetch matrix against project allocation entry '{proj_id}'... Please wait.")
            ),
            title=None, easy_close=False
        ))

        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            def execute_diagnostic_ping():
                # Setup a raw container worker block to test the workspace parameters directly
                pipeline_tester = SatelliteTrafficPipeline(project_id=proj_id)
                pipeline_tester.inject_pipeline()
                return pipeline_tester.provider.connect()

            try:
                # Dispatch ping to background thread executor pool
                is_valid = await loop.run_in_executor(pool, execute_diagnostic_ping)
                
                # Close loading diagnostic box instantly
                ui.modal_remove()
                
                if is_valid:
                    # 🟢 SUCCESS MODAL POPUP
                    ui.modal_show(ui.modal(
                        ui.div(
                            ui.h4("✅ Cloud Connection Verified", style="color: #22c55e; font-weight: 600; margin-bottom: 8px;"),
                            ui.p(f"Google Earth Engine successfully authenticated and verified Project ID '{proj_id}'. Your environment is fully operational and primed for pipeline execution.", style="color: #e5e7eb; font-size: 13px; line-height: 1.5;"),
                            style="padding: 10px;"
                        ),
                        title=None, easy_close=True
                    ))
                else:
                    raise ConnectionError("Silent system initialization failed to establish context.")
                    
            except Exception as e:
                error_msg = str(e)
                ui.modal_remove() # Clear diagnostic notice
                
                # ❌ FAILURE MODAL POPUP
                ui.modal_show(ui.modal(
                    ui.div(
                        ui.h4("❌ Google Cloud Verification Failed", style="color: #ef4444; font-weight: 600; margin-bottom: 12px;"),
                        ui.p("Google's authentication server rejected the connectivity test query:", style="color: #9ca3af; font-size: 13px;"),
                        ui.div(error_msg, style="background-color: #7c2d1222; border: 1px solid #9a341244; color: #fbbf24; padding: 12px; border-radius: 4px; font-family: monospace; font-size: 12px;"),
                        ui.p("Confirm spelling variations or check your Google Console IAM dashboard limits before attempting another test.", style="color: #9ca3af; font-size: 13px; margin-top: 14px;"),
                        style="padding: 10px;"
                    ),
                    title=None, easy_close=True
                ))
       
    # 📡 Visual Connection Telemetry Badge Renderer
    # @render.ui
    # def gee_connection_badge():
    #     if gee_is_connected():
    #         return ui.HTML("<span style='background-color:#065f46; color:#34d399; border:1px solid #047857; padding:4px 10px; border-radius:9999px; font-size:11px; font-weight:600; font-family:monospace;'>● GEE ACTIVE</span>")
    #     return ui.HTML("<span style='background-color:#1f2937; color:#9ca3af; border:1px solid #374151; padding:4px 10px; border-radius:9999px; font-size:11px; font-weight:600; font-family:monospace;'>○ GEE OFFLINE</span>")

    # ⚡ Pipeline Execution Activity Status Badge Renderer
    @render.ui
    def pipeline_run_badge():
        if pipeline_is_running():
            # Amber/Yellow Pulsing State during active calculation tasks
            return ui.HTML(
                "<span style='background-color: #7e22ce15; color: #eab308; border: 1px solid #ca8a0455; "
                "padding: 4px 12px; border-radius: 9999px; font-size: 11px; font-weight: 600; font-family: monospace; "
                "display: inline-flex; align-items: center; gap: 6px; letter-spacing: 0.5px;'>"
                "<span style=\"animation: blink 0.8s infinite alternate; width: 6px; height: 6px; "
                "background-color: #eab308; border-radius: 50%; box-shadow: 0 0 6px #eab308;\"></span> "
                "EXECUTING PIPELINE"
                "<style>@keyframes blink { 0% { opacity: 0.2; } 100% { opacity: 1; } }</style>"
                "</span>"
            )
        else:
            # Solid Radiant Green State indicating infrastructure node is primed and ready to accept input
            return ui.HTML(
                "<span style='background-color: #065f4615; color: #22c55e; border: 1px solid #16a34a44; "
                "padding: 4px 12px; border-radius: 9999px; font-size: 11px; font-weight: 600; font-family: monospace; "
                "display: inline-flex; align-items: center; gap: 6px; letter-spacing: 0.5px;'>"
                "<span style='width: 6px; height: 6px; background-color: #22c55e; border-radius: 50%; "
                "box-shadow: 0 0 6px #22c55e;'></span> "
                "READY"
                "</span>"
            )





    ## rest init 

    # Reactive storage arrays matching Streamlit session states
    fleet_queue = reactive.Value([])
    clicked_lat = reactive.Value(40.0890)
    clicked_lon = reactive.Value(-75.3947)
    
    pipeline_results = reactive.Value(None)
    pipeline_error = reactive.Value(None)
    map_markers = []


    # Import leaflet inline to isolate map setup
    import ipyleaflet as ipyl

    # Safe interactive leaflet instance generation rules
    m = ipyl.Map(center=(40.0890, -75.3947), zoom=13, scroll_wheel_zoom=True)
    center_marker = ipyl.Marker(location=(40.0890, -75.3947), draggable=True, color="red")
    m.add(center_marker)
    register_widget("map", m)

    # Event actions tracking map cursor coordinate modifications
    def handle_move(location, **kwargs):
        if isinstance(location, (list, tuple)) and len(location) >= 2:
            clicked_lat.set(float(location[0]))
            clicked_lon.set(float(location[1]))
        
    center_marker.on_move(handle_move)
    
    def handle_click(**kwargs):
        if kwargs.get('type') == 'click':
            coords = kwargs.get('coordinates')  
            if coords and len(coords) >= 2:
                lat_val = float(coords[0])
                lon_val = float(coords[1])
                
                clicked_lat.set(lat_val)
                clicked_lon.set(lon_val)
                center_marker.location = (lat_val, lon_val)

    m.on_interaction(handle_click)

    @render_widget
    def map():
        return m

    # Update map tracking queues cleanly 
    @reactive.effect
    def update_map_queue_markers():
        nonlocal map_markers
        for marker in map_markers:
            if marker in m.layers:
                m.remove(marker)
        map_markers.clear()
        
        for coord in fleet_queue():
            blue_marker = ipyl.Marker(location=(coord[1], coord[0]), draggable=False)
            m.add(blue_marker)
            map_markers.append(blue_marker)

    @render.ui
    def coordinate_banner():
        return ui.markdown(
            f"<div style='background-color: #111318; padding: 10px 14px; border-radius: 4px; border: 1px solid #2d3139; margin-top: 12px; font-size:13px; color: #9ca3af;'> "
            f"🎯 <span style='color:#f3f4f6; font-weight:600;'>Active Pinpoint:</span> Lon <code>{clicked_lon():.4f}</code> | Lat <code>{clicked_lat():.4f}</code>"
            f"</div>"
        )

    @render.ui
    def ledger_body_container():
        if not input.toggle_ledger():
            return None
        return ui.div(
            ui.output_ui("pipeline_feedback_layer"),
            ui.output_data_frame("results_dataframe")
        )

    @render.ui
    def plot_body_container():
        if not input.toggle_plot():
            return None
        return ui.div(
            ui.output_plot("results_plot"),
            style="width: 100%; max-height: 450px; overflow: hidden; display: flex; justify-content: center; padding: 15px;"
        )

    @render.ui
    def imagery_body_container():
        if not input.toggle_imagery():
            return None
        return ui.output_ui("imagery_canvas_bundles")


    # Fleet list state adjustment buttons
    @reactive.effect
    @reactive.event(input.add_to_queue)
    def _():
        new_point = [clicked_lon(), clicked_lat()]
        current_queue = fleet_queue().copy()
        if new_point not in current_queue:
            current_queue.append(new_point)
            fleet_queue.set(current_queue)

    @reactive.effect
    @reactive.event(input.clear_queue)
    def _():
        fleet_queue.set([])

    @render.ui
    def queue_dataframe_view():
        if not fleet_queue():
            return ui.markdown("<p style='color: #64748b; font-style: italic; font-size:14px; padding-top:10px;'>Active tracking queue is empty.</p>")
        return ui.output_data_frame("queue_table")


    # Listen to the checkbox toggle state
    @reactive.effect
    @reactive.event(input.ignore_validators)
    def _handle_safety_override_prompt():
        # If the user checked the box, trigger the warning prompt modal
        if input.ignore_validators():
            ui.modal_show(ui.modal(
                ui.div(
                    ui.markdown("### ⚠️ CRITICAL WARNING"),
                    ui.p("Bypassing API GEE safety validations. can cause massive server loads and eat your monthly quota of EECU. \n\n\n"
                         "Monitor your cloud console processing limits carefully!"),
                    style="padding: 10px;"
                ),
                title="Bypass Safety Guardrails",
                footer=ui.div(
                    ui.input_action_button("confirm_override", "Yes, I understand the risk.", class_="btn-danger btn-sm"),
                    ui.input_action_button("abort_override", "No, get me out of here please.", class_="btn-secondary btn-sm"),
                    style="display: flex; gap: 8px; justify-content: flex-end;"
                ),
                easy_close=False
            ))

    # Event Handle: User changes mind -> Close modal and UNCHECK the box
    @reactive.effect
    @reactive.event(input.abort_override)
    def _handle_abort_override():
        ui.modal_remove()
        # Force the checkbox UI back to unchecked (False)
        ui.update_checkbox("ignore_validators", value=False)

    # Event Handle: User confirms risk -> Simply close the modal and let it stay checked
    @reactive.effect
    @reactive.event(input.confirm_override)
    def _handle_confirm_override():
        ui.modal_remove()

    @render.data_frame
    def queue_table():
        return pd.DataFrame(fleet_queue(), columns=["Longitude", "Latitude"])

    # Core execution loop trigger 
    # Core execution loop trigger 
    @reactive.effect
    @reactive.event(input.run_pipeline)
    async def trigger_pipeline_calculation():
        pipeline_is_running.set(True)
        mode = input.execution_mode()
        if mode in ["BATCH_FLEET", "COMPARE"] and not fleet_queue():
            pipeline_error.set("⚠️ Operational Error: Your fleet queue is completely empty. Please register coordinates on the map first.")
            pipeline_results.set(None)
            return

        pipeline_error.set(None)
        pipeline_results.set(None)

        # --- FIXED: COORDINATE COALESCING & ROUNDING LAYER ---
        # Every coordinate input is strictly rounded to 3 decimal places.
        # This groups clicks within a ~110m box into a single combined cache entry!
        if mode in ["BATCH_FLEET", "COMPARE"]:
            targets = []
            for coord in fleet_queue():
                if isinstance(coord, (list, tuple)) and len(coord) >= 2:
                    targets.append([round(float(coord[0]), 3), round(float(coord[1]), 3)])
                else:
                    try:
                        targets.append([round(float(coord), 3), round(float(coord), 3)])
                    except (ValueError, TypeError, IndexError):
                        continue
        else:
            targets = [round(float(clicked_lon()), 3), round(float(clicked_lat()), 3)]


        with ui.Progress(min=1, max=10) as p:
            p.set(message="Executing Satellite Pipeline", detail="Processing alternative imagery signal matrices...")
            try:
                proj_id = str(input.project_id())
                logger.warning(f'Using project Id: {proj_id}')
                pipeline = SatelliteTrafficPipeline(project_id=proj_id)
                pipeline.inject_pipeline()
                
                # Clear pipeline logger caching history matrices
                if hasattr(pipeline.data_logger, 'clear_buffer'):
                    pipeline.data_logger.clear_buffer()
                if hasattr(pipeline.ml_layer, 'clear_ml_memory'):
                    pipeline.ml_layer.clear_ml_memory()

                # --- SECURE THREAD ISOLATION EXECUTION ---
                limit_val = int(input.limit())
                force_ref = bool(input.force_refresh())
                start_dt = str(input.start_date())
                end_dt = str(input.end_date())
                ticker_sym = str(input.ticker_symbol()).upper().strip()
                selected_asset_class = str(input.asset_type_toggle()).upper().strip() 
                ignore_vals = bool(input.ignore_validators())
            
            
                loop = asyncio.get_running_loop()
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    try:
                        def run_isolated_pipeline():
                            res_dict = pipeline.app_run(
                                center_coordinates=targets,
                                start_date=start_dt,
                                end_date=end_dt,
                                ticker=ticker_sym,
                                execution_mode=mode,
                                asset_type = selected_asset_class,
                                limit=limit_val,
                                force_refresh=force_ref,
                                ignore_validators=ignore_vals,
                            )
                            # FIXED: Extracting log records inside the worker thread boundaries 
                            # protects SQLite engines from cross-thread execution panic events
                            thread_safe_df = pipeline.data_logger.get_dataframe()
                            return res_dict, thread_safe_df

                        res, raw_df = await loop.run_in_executor(pool, run_isolated_pipeline)
                    except Exception as internal_err:
                        logger.warning(f"[Satalyze Fix] Intercepted backend sequence mismatch: {internal_err}", exc_info = True)
                        if "not found" in err_lower or "database query failed" in err_lower or "deleted" in err_lower:
                            pipeline_error.set(f"❌ Cloud Connection Error: The Project ID '{proj_id}' does not exist or has been deleted on Google Cloud Console.")
                        elif "denied" in err_lower or "forbidden" in err_lower or "permission" in err_lower:
                            pipeline_error.set(f"❌ Cloud Security Denial: Account lacks 'Service Usage Consumer' roles for project '{proj_id}'.")
                        else:
                            pipeline_error.set(f"⚠️ Operational Pipeline Fault: {error_msg}")

                        # Clean up visualization telemetry results so stale grids fade out cleanly
                        pipeline_results.set(None)
                        return
                        #res, raw_df = None, pd.DataFrame()


                
                raw_df = pipeline.data_logger.get_dataframe() # first log_detection has to run in pipeline
                
                if res is None or not isinstance(res, dict):
                    logger.warning("[Satalyze Fix] Recovering batch data structures from SQLite logs directly...", exc_info= True)
                    try:
                        import sqlite3
                        conn = sqlite3.connect(pipeline.db.db_path)
                        # Read all rows logged across targets
                        recovered_df = pd.read_sql_query(f"SELECT * FROM lot_assignments WHERE ticker = '{ticker_sym}'", conn)
                        if recovered_df.empty:
                            recovered_df = pd.read_sql_query("SELECT * FROM site_observations ORDER BY id DESC LIMIT 20", conn)
                        conn.close()
                    except Exception:
                        recovered_df = pd.DataFrame()

                    display_df = recovered_df if not recovered_df.empty else raw_df

                    res = {
                        "dataframe": display_df,
                        "unlabeled": getattr(pipeline, 'raw_images', []),
                        "labeled": getattr(pipeline, 'labeled_images', []),
                        "figure": None
                    }
                else:
                    display_df = res.get("dataframe", raw_df)

                
                try:
                    # Pull down fundamental corporate records matching ticker criteria
                    if selected_asset_class == "PUBLIC":
                        financial_df = await pipeline.db.fetch_combined_raw_data(ticker = ticker_sym) # this is the combined df, both ticker and car count, wont this become messy? 
                    else: 
                        financial_df = pd.DataFrame()
                except Exception:
                    financial_df = pd.DataFrame()
                    
                try:
                    # Clean date formats using variable key normalizers to stop KeyError crashes
                    plot_traffic = display_df.copy()
                    if not plot_traffic.empty:
                        # 1. Identify which column handles time tracking in this database schema mode
                        found_date_col = None
                        for col in ['date', 'year', 'capture_date', 'timestamp', 'capture_year']:
                            if col in plot_traffic.columns:
                                found_date_col = col
                                break
                        
                        # 2. FIXED: If only 'year' exists, map it into a clean, flat 1D timestamp string series
                        if found_date_col:
                            if found_date_col in ['year', 'capture_year', 'active_from']:
                                # Converts an integer year like 2022 to a clean 1D string "2022-01-01"
                                plot_traffic['date'] = plot_traffic[found_date_col].astype(str).apply(
                                    lambda x: f"{x.strip().split('.')[0]}" if '.' in str(x) else f"{x.strip()}"
                                )
                            else:
                                # Ensure standard date columns are extracted as flat 1D strings
                                def extract_clean_str(val):
                                    if isinstance(val, (list, tuple)): return str(val[0]) if len(val) > 0 else ""
                                    return str(val).split(" ")[0] # Strip off trailing HxWxC or time arrays
                                plot_traffic['date'] = plot_traffic[found_date_col].apply(extract_clean_str)
                            
                            # Ensure the active timeline column is named 'date' for the plotter engine
                            if found_date_col != 'date':
                                plot_traffic.rename(columns={found_date_col: 'date'}, inplace=True)
                        else:
                            # Safe fallback layout timeline if all columns are absent
                            plot_traffic['date'] = pd.date_range(start=start_dt, periods=len(plot_traffic)).strftime('%Y-%m-%d')
                        
                        # 3. FIXED: Strictly guarantee that the 'date' series is a 1-dimensional string array
                        plot_traffic['date'] = plot_traffic['date'].astype(str)

   
                        # Deduplicate rows smoothly across your macro years
                        agg_dict = {col: 'first' for col in plot_traffic.columns if col not in ['date', 'site_id']} # 🪚 FIX HERE
                        if 'car_count' in plot_traffic.columns:
                            agg_dict['car_count'] = 'mean'
                        elif "aggregated_observed_cars" in plot_traffic.columns:
                            plot_traffic['car_count'] = plot_traffic['aggregated_observed_cars'] # Fixed your spelling typo here too!
                            agg_dict['car_count'] = 'mean'

                        agg_dict = {k: v for k, v in agg_dict.items() if k in plot_traffic.columns}



                        if 'site_id' in plot_traffic.columns:
                            plot_traffic = plot_traffic.groupby(['site_id', 'date'], as_index=False).agg(agg_dict)
                        else:
                            plot_traffic = plot_traffic.groupby('date', as_index=False).agg(agg_dict)

                        # Chronological sorting sorted by site first, then date
                        plot_traffic['date'] = pd.to_datetime(plot_traffic['date'])
                        if 'site_id' in plot_traffic.columns:
                            plot_traffic = plot_traffic.sort_values(['site_id', 'date'])
                        else:
                            plot_traffic = plot_traffic.sort_values('date')


                    # Call the plotter engine helper function
                    active_plot_ticker = "PRIVATE" if selected_asset_class == 'PRIVATE' else ticker_sym
                    res["figure"] = pipeline.plotter.generate_mode_plot(
                        execution_mode=mode,
                        ticker_clean=active_plot_ticker,
                        traffic_df=plot_traffic,
                        display_df=plot_traffic, 
                        financial_df=financial_df
                    )
                except Exception as e:
                    logger.debug(f"[Satalyze Fix] Plot mapper error inside mode layer: {e}")
                    import matplotlib.pyplot as plt
                    fig, ax = plt.subplots(figsize=(10, 4))
                    if not display_df.empty:
                        car_col = 'car_count' if 'car_count' in display_df.columns else (display_df.select_dtypes(include=['number']).columns if len(display_df.select_dtypes(include=['number']).columns) > 0 else display_df.columns)
                        time_col = 'year' if 'year' in display_df.columns else ('capture_year' if 'capture_year' in display_df.columns else display_df.columns)
                        ax.plot(display_df[time_col], display_df[car_col], marker='o', color='#3b82f6', linewidth=2)
                        ax.set_title(f"TARGET: {ticker_sym} // FALLBACK TIMELINE")
                    res["figure"] = fig



                # --- FIXED: RECURSIVE MATRIX FLATTENING LOOP FOR BATCH IMAGES ---
                # Unpacks deeply nested image lists when cache layers return multi-dimensional slots
                def flatten_image_array(img_list):
                    flat = []
                    for item in img_list:
                        if isinstance(item, list):
                            flat.extend(flatten_image_array(item))
                        elif item is not None:
                            flat.append(item)
                    return flat

                if "unlabeled" in res and isinstance(res["unlabeled"], list):
                    res["unlabeled"] = flatten_image_array(res["unlabeled"])
                if "labeled" in res and isinstance(res["labeled"], list):
                    res["labeled"] = flatten_image_array(res["labeled"])
                    
                pipeline_results.set(res)

            except Exception as e:
                pipeline_error.set(f"Critical Pipeline Engine Fault: {e}")
                pipeline_results.set(None)
            finally:
                pipeline_is_running.set(False)

    @render.ui
    def pipeline_feedback_layer():
        if pipeline_error():
            return ui.markdown(f"<div style='color:#f87171; background:#7f1d1d11; padding:12px; border-radius:4px; border:1px solid #7f1d1d; font-size:13px;'>{pipeline_error()}</div>")
        if pipeline_results() is not None:
            # FIXED: Updated background, font color, and border to use high-end tech light blue styles
            return ui.markdown(
                f"<div style='color:#60a5fa; background:#1e3a8a25; padding:12px; border-radius:4px; border:1px solid #2563eb44; font-size:13px; font-weight: 500;'>"
                f"✓ Operational telemetry arrays processed successfully. View metrics below."
                f"</div>"
            )
        return ui.markdown("<p style='color: #6b7280; font-style: italic; font-size: 13px; padding-top: 5px;'>Awaiting parameter initiation triggers...</p>")

    # 3. DEFENSIVE FIX: Fully shield all renderer methods from accessing missing keys or null values
    @render.data_frame
    def results_dataframe():
        res = pipeline_results()
        if res is None or not isinstance(res, dict) or "dataframe" not in res: 
            return None
        return res["dataframe"]

    @render.plot
    def results_plot():
        res = pipeline_results()
        if res is None or not isinstance(res, dict) or "figure" not in res: 
            return None
        
        fig = res["figure"]

        # Apply aspect-ratio protections inside Shiny's rendering loop
        # to guarantee text elements remain legible during sidebar toggles
        fig.set_dpi(100) # Enforces sharp resolution tracking
        
        import matplotlib.pyplot as plt
        try:
            return fig
        finally:
            plt.close(fig)


    @render.ui
    def imagery_canvas_bundles():
        res = pipeline_results()
        if res is None or not isinstance(res, dict) or "unlabeled" not in res or not res["unlabeled"]:
            return None
            
        # 1. READ SLIDER ZOOM PERCENTAGE GLOBALLY
        zoom_pct = input.image_zoom()
            
        image_cards = []
        try:
            for i in range(len(res["unlabeled"])):
                def get_image_src(item):
                    if isinstance(item, (str, Path)):
                        p = Path(item)
                        if p.exists():
                            b64 = base64.b64encode(p.read_bytes()).decode("utf-8")
                            return f"data:image/png;base64,{b64}"
                        return ""
                    elif hasattr(item, "__array__"):
                        import cv2
                        import numpy as np
                        img_np = np.asarray(item, dtype=np.uint8)
                        if len(img_np.shape) == 3:
                            if img_np.shape[0] == 3:
                                img_np = np.transpose(img_np, (1, 2, 0))
                            img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                        success, encoded_img = cv2.imencode('.png', img_np)
                        if success:
                            return f"data:image/png;base64,{base64.b64encode(encoded_img).decode('utf-8')}"
                    return ""

                unlabeled_uri = get_image_src(res["unlabeled"][i])
                labeled_uri = get_image_src(res["labeled"][i])
                
                # 2. FIXED SECURE FULLSCREEN POPUP SCRIPT: Avoids browser security blocks
                def make_zoom_anchor(img_uri, label_txt):
                    js_popup = f"""
                    var w = window.open();
                    w.document.write('<html style="background:#090d16; margin:0; padding:0; display:flex; align-items:center; justify-content:center;"><head><title>{label_txt}</title></head><body style="margin:0;"><img src="{img_uri}" style="max-width:100vw; max-height:100vh; object-fit:contain; cursor:zoom-out;" onclick="window.close();"></body></html>');
                    w.document.close();
                    """
                    return ui.tags.a(
                        ui.img(src=img_uri, style="width: 100%; border-radius: 4px; border: 1px solid #1f2937; cursor: zoom-in;"),
                        href="javascript:void(0);",
                        onclick=js_popup
                    )

                # 3. FIXED ZOOM WIDTH SCALE CONTROL: Dynamic wrapper styling changes shape smoothly
                card_item = ui.card(
                    ui.card_header(f"Geospatial Signal Canvas Cluster Bundle Row #{i+1}"),
                    ui.layout_columns(
                        ui.div(ui.markdown("<small style='color:#64748b; font-weight:600;'>RAW CONTEXT DATA</small>"), make_zoom_anchor(unlabeled_uri, "Raw Satellite Context Image")),
                        ui.div(ui.markdown("<small style='color:#06b6d4; font-weight:600;'>YOLO INFERENCE MATCH</small>"), make_zoom_anchor(labeled_uri, "YOLO Detection Inference Overlay")),
                        col_widths=[6, 6]
                    ),
                    style=f"margin-top: 16px; display: inline-block; width: {zoom_pct}%; vertical-align: top; padding: 10px; box-sizing: border-box;"
                )
                image_cards.append(card_item)
                
            # Wrap everything inside a container to display scaled card containers cleanly side-by-side
            return ui.div(*image_cards, style="width: 100%; display: block; font-size: 0;")
        except Exception as e:
            return ui.markdown(f"<div style='color:#ef4444; padding:10px;'>Error rendering patch grids: {e}</div>")


app = App(app_ui, server)


## get rid of setgin that arent needed susch as project id, or exectution mode, 
# move the datatframe below image , make images zoom into. small then zoom. Main graph first and foremost. 
