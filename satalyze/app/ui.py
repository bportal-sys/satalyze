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


from datetime import date
from shiny import ui
from shinywidgets import output_widget
from styles import CARBON_SLATE_THEME_CSS


# 1. Clean separation: Link natively to your separate CSS asset file
# This loads custom.css from your package's www/ folder at boot time
app_ui = ui.page_navbar(

    # ================= TAB 1: OPERATIONAL TERMINAL =================
    ui.nav_panel(
        "🛰️ Terminal Workspace",
        # Instructs the browser to load your external stylesheet text file
        ui.head_content(ui.tags.style(CARBON_SLATE_THEME_CSS)),
        ui.layout_sidebar(
            # CLEANED SIDEBAR: Only Day-to-Day inputs
            ui.sidebar(
                ui.markdown("### **Platform Controller**"),
                ui.layout_columns(
                    ui.input_date("start_date", "Start Date", value=date(2019, 1, 1)),
                    ui.input_date("end_date", "End Date", value=date(2022, 12, 31)),
                    id = 'date_field',
                ),

                ui.input_radio_buttons(
                    id="asset_type_toggle",
                    label="Asset Class Selection",
                    choices=["PRIVATE", "PUBLIC"],
                    selected="PRIVATE",
                    inline=True
                ),
                

                # 💡 Only shows up if "Public" is selected above
                ui.panel_conditional(
                    "input.asset_type_toggle == 'PUBLIC'",
                    ui.input_text("ticker_symbol", "Corporate Ticker", value="AMZN")
                ),
                
                

                ui.input_select(
                    "execution_mode", 
                    "Execution Mode",
                    {
                        "SINGLE_STORE": "SINGLE_STORE",
                        "BATCH_FLEET": "BATCH_FLEET", 
                        # "NATIONWIDE": "NATIONWIDE", 
                        # "COMPARE": "COMPARE"
                    },
                    selected="SINGLE_STORE"
                ),
                
                ui.hr(),
                
                ui.input_action_button(
                    "run_pipeline", 
                    "🚀 Run Execution Engine", 
                    class_="btn-primary w-100",
                    style="font-weight: bold; background-color: #2563eb; color: white; padding: 10px;"
                ),
                width=340
            ),
            
            # MAIN WORKSPACE AREA: Grid Layout
            ui.layout_columns(
                # Panel 1: Interactive Spatial Map Canvas (Static & Isolated for Complete Stability)
                ui.card(
                    ui.card_header("📍 Spatial Map Pinpoint Tracker"),
                    output_widget("map", height="400px"),
                    ui.output_ui("coordinate_banner"),

                    ui.panel_conditional("input.execution_mode == 'BATCH_FLEET'",
                        
                        ui.layout_columns(
                            ui.input_action_button("add_to_queue", "📍 Add Pinpoint", class_="btn-secondary btn-sm"),
                            ui.input_action_button("clear_queue", "🗑️ Clear Queue", class_="btn-outline-danger btn-sm"),
                                            ),
                        ui.output_ui("queue_dataframe_view"),
                        )
                ),
                
                # Panel 2: Output Analytical Ledger (Collapsible Header Toggle)
                ui.card(
                    ui.card_header(
                        ui.div(
                            ui.span("📊 Output Data Ledger"),
                            ui.input_switch("toggle_ledger", "", value=True),
                            style="display: flex; justify-content: space-between; align-items: center; width: 100%;"
                        )
                    ),
                    ui.output_ui("ledger_body_container")
                ),
                col_widths=[6, 6], id = 'ledger_card'
            ),
            
            # Panel 3: Timeline Chart Visualizations (Collapsible Header Toggle)
            ui.card(
                ui.card_header(
                    ui.div(
                        ui.span("📈 Aggregated Trend Visualizations"),
                        ui.input_switch("toggle_plot", "", value=True),
                        style="display: flex; justify-content: space-between; align-items: center; width: 100%;"
                    )
                ),
                ui.output_ui("plot_body_container"), 
                id = 'plot_card',
            ),
            
            # Panel 4: Satellite Patch Canvas Gallery (Collapsible Header Toggle)
            ui.card(
                ui.card_header(
                    ui.div(
                        ui.span("🖼️ Satellite Imagery Canvas Gallery"),
                        ui.input_switch("toggle_imagery", "", value=True),
                        style="display: flex; justify-content: space-between; align-items: center; width: 100%;"
                    )
                ),
                ui.output_ui("imagery_body_container"), id = 'imagery_card'
            )
        ) , value='main_dashboard'
    ),

    # ================= TAB 2: GLOBAL SETTINGS PANEL =================
    ui.nav_panel(
        "⚙️ Advanced Settings",
        ui.div(
            ui.layout_columns(
                ui.card(
                    ui.card_header("GEE Authentication"),
                    ui.div(
                        # 🔗 Clean, inline horizontal block spacing layout configuration
                        ui.div(
                            ui.input_action_button(
                                "force_auth", 
                                "🔑 (Re)Authenticate Account Profile", 
                                class_="btn-outline-primary btn-sm",
                                style="flex: 2;" # Takes up more proportional space dynamically
                            ),
                            ui.input_action_button(
                                "test_conn", 
                                "Test Connection", 
                                class_="btn-outline-primary btn-sm", # Switched to green for clear identity
                                style="flex: 1;"
                            ),
                            style="display: flex; gap: 12px; margin-top: 8px; margin-bottom: 8px; width: 100%;"
                        ),
                        ui.markdown("<small style='color:#64748b;'>This maps package authentication hooks back to your cloud console credentials framework natively.</small>")
                    )
                ),
                ui.card(
                    ui.card_header("Cloud Infrastructure Integration"),
                    ui.input_text("project_id", "Google Earth Engine Project ID", placeholder="satalyze (e.g. my-gcp-project-1234)"),
                    ui.markdown("<small style='color:#64748b;'>This maps package authentication hooks back to your cloud console credentials framework natively.</small>")
                ),
                ui.card(
                    ui.card_header("Multiple Caching API & Machine Learning Calls"),
                    ui.input_numeric("limit", "Snapshots Pipeline Download Limit", value=3, min=1, max=20),
                    ui.markdown("<small style='color:#64748b;'>This increases or decreases the amount of images you get back from your satellite API ( NAIP data occurs 2 - 3 years expect sparse data).</small>")
                ),
                ui.card(
                    ui.card_header("Force Refresh"),
                    ui.input_checkbox("force_refresh", "Force Local Cache Overwrite (Bypass Databases)", value=False),
                    ui.markdown("<small style='color:#64748b;'>This forces the database to ignore the cached data in your local database and forces a fresh API and ML call.</small>")
                ),
                ui.card(
                    ui.card_header("Image Grid size"),
                    ui.input_slider(
                        "image_zoom", 
                        "Satellite Patch Gallery Zoom", 
                        min=30, 
                        max=100, 
                        value=50, 
                        step=5, 
                        post="%",
                    ),
                    ui.markdown("<small style='color:#64748b;'>This changes the size of your image in your image gallery.</small>"), id = 'zoomything'
                ),
                ui.card(
                    ui.card_header("Developer Mode / API Access Controls"),
                    ui.input_checkbox("ignore_validators", "Bypass API GEE Safety Validators", value=False),
                    ui.markdown("<small style='color:#ef4444;'>⚠️ Warning: Overriding scale limits could spike cloud usage processing metrics unexpectedly.</small>")
                ),
                col_widths=[6, 6]
            ),
            style="margin-top: 25px;"
        ), value = 'settings_panel'
    ),

    ui.nav_spacer(),
    
    # 🎯 FIXED NAVBAR CONTROL LAYER: Removed class_ argument to prevent structural compilation crashes
    ui.nav_control(
        ui.div(
            # 1. Real-time dynamic processing status badge indicator wrapper
            ui.div(
                ui.output_ui("pipeline_run_badge"),
                style="margin-right: 16px;" # Spacing gap separating badge from button
            ),
            # 2. Interactive help documentation onboarding button widget
            ui.div(
                ui.input_action_button("start_tutorial", "Help / Onboarding 📖", class_="btn-outline-primary btn-sm")
            ),
            # ✅ THE FIX: The Bootstrap layout wrapper properties 'ms-auto' and 'd-flex' are placed here!
            class_="ms-auto d-flex align-items-center",
            style="height: 100%;"
        )
    ),
    
    id="main_navbar", 
    footer=ui.output_ui("tutorial_panel_overlay"),
    title="Satalyze | Powered by github.com/bportal-sys",
    bg="#0f172a",  
    inverse=True
)
