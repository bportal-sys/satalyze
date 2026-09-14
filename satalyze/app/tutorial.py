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



from shiny import ui, reactive

# src/satalyze/app/tutorial.py

def hl(text: str, color_type: str = "blue") -> str:
    """Reusable element that wraps text in a bold, high-visibility colored tag.
    Options: 'blue', 'pink', 'green'"""
    colors = {
        "blue": "#60a5fa",    # High-tech light blue
        "pink": "#ff007f",    # Fleet average pink/magenta
        "green": "#4ade80"    # Success green
    }
    hex_color = colors.get(color_type, "#60a5fa")
    
    # Returns raw HTML that markdown parses flawlessly
    return f'<b style="color: {hex_color}; font-weight: 700;">{text}</b>'



TUTORIAL_STEPS = {
    1: {
        "title": "🎯 Step 1: Timeframe Controller",
        "content": f"Set your query timeline bounds here. \n\n\n Choose the {hl('Start & End Date')} sequence to filter satellite data history metrics.",
        "target_id": "date_field",
        "nav_target": "main_dashboard"
    },
    2: {
        "title": "🏢 Step 2: Asset Categories",
        "content": f"{hl('Private mode')} tracks vehicle counts only. \n\n\n Switch to {hl('Public mode')} and enter a corporate ticker to cross-reference traffic with revenue data.",
        "target_id": "asset_type_toggle",
        "nav_target": "main_dashboard"
    },
    3: {
        "title": "🔄 Step 3: Execution Scope",
        "content": f"Choose {hl('Single Store')} to log a solitary location, \n\n\n or switch to {hl('Batch Fleet')} to track multiple properties across a whole region simultaneously.",
        "target_id": "execution_mode",
        "nav_target": "main_dashboard"
    },
    4: {
        "title": "📍 Step 4: Map & Queue Pins",
        "content": f"Your location hub. For {hl('Single Store, just click the map grid')}.\n\n\n For {hl('Batch Fleet')}, click a spot {hl("and select 'Add Pinpoint'")} to append it to your active queue.",
        "target_id": "map",
        "nav_target": "main_dashboard"
    },
    5: {
        "title": "⚙️ Step 5: GEE Cloud Integration",
        "content": f"Welcome to Advanced Settings. \n\n\nYou {hl('must enter your unique Google Earth Engine Project ID')} here to authenticate imagery API queries.",
        "target_id": "project_id",
        "nav_target": "settings_panel"
    },
    6: {
        "title": "📸 Step 6: Recency Cap",
        "content": f"Control snapshot limits. \n\n\nSetting this threshold parameter to {hl('3')} instructs the pipeline to pull down only the {hl('3 most recent cloud observations')}.",
        "target_id": "limit",
        "nav_target": "settings_panel"
    },
    7: {
        "title": "⚡ Step 7: Clear Cache Blocks",
        "content": f"If data feels frozen, toggle {hl('Force Cache Overwrite')}. \n\n\nThis ignores saved SQLite table rows and forces a fresh GEE download and ML model call.",
        "target_id": "force_refresh",
        "nav_target": "settings_panel"
    },
    8: {
        "title": "🔍 Step 8: Gallery Zoom",
        "content": f"Use this slider to resize your outputs. \n\n\nScale images {hl('up or down')} smoothly to track specific target details.",
        "target_id": "zoomything",
        "nav_target": "settings_panel"
    },
    9: {
        "title": "📊 Step 9: Analytical Ledger",
        "content": f"Back on the dashboard! \n\n\nThis ledger panel prints your structured Pandas dataframes, showing raw coordinates, counts, and financial values.",
        "target_id": "ledger_card",  # ✨ Maps to updated layout card ID
        "nav_target": "main_dashboard"
    },
    10: {
        "title": "📈 Step 10: Trend Curves",
        "content": f"Your telemetry charts print here. \n\n\n In {hl('Single Mode')} you will see the site counts with optional financial metrics. \n\n\nIn {hl('Batch Mode')}, you will see individual store lines fading cleanly behind a bold fleet average line.",
        "target_id": "plot_card",    # ✨ Maps to updated layout card ID
        "nav_target": "main_dashboard"
    },
    11: {
        "title": "🖼️ Step 11: Image Vault",
        "content": f"The visual engine panel. Displays your Raw Context imagery side-by-side with YOLO computer vision object tracking bounding box overlays.",
        "target_id": "imagery_card", # ✨ Maps to updated layout card ID
        "nav_target": "main_dashboard"
    },
    12: {
        "title": "Step 12: See the world",
        "content": f"{hl("You're now ready to use satalyze")}, if you need try clicking through the tutorial again while clicking the elements!",
        "target_id": "start_tutorial", # ✨ Maps to updated layout card ID
        "nav_target": "main_dashboard"
    }
}

class GuidedTourManager:
    def __init__(self):
        self.current_step = reactive.Value(0)

    def get_current_nav_target(self):
        step_data = TUTORIAL_STEPS.get(self.current_step())
        return step_data["nav_target"] if step_data else None

    def get_ui_and_css(self):
        step_idx = self.current_step()
        step_data = TUTORIAL_STEPS.get(step_idx)
        if not step_data:
            return None, ""
            
        target = step_data["target_id"]
        total_steps = len(TUTORIAL_STEPS)
        
        footer_buttons = []
        if step_idx > 1:
            footer_buttons.append(ui.input_action_button("tut_prev", "◀", class_="btn-secondary btn-sm"))
        if step_idx < total_steps:
            footer_buttons.append(ui.input_action_button("tut_next", "Next ▶", class_="btn-primary btn-sm"))
        else:
            footer_buttons.append(ui.input_action_button("tut_close", "Finish ✓", class_="btn-success btn-sm"))

       # src/satalyze/app/tutorial.py

        panel_ui = ui.div(
            ui.div(
                ui.h5(step_data["title"], style="color: #60a5fa; margin-top: 0; font-weight: 600; font-size: 14px;"),
                ui.hr(style="border-color: #2d3139; margin: 8px 0;"),
                
                # ✨ FIX: Wrap the content in ui.div(ui.markdown(...)) instead of ui.p()!
                ui.div(
                    ui.markdown(step_data["content"]),
                    style="margin: 12px 0; line-height: 1.5; font-size: 13px; color: #e5e7eb;"
                ),
                
                ui.div(*footer_buttons, style="display: flex; gap: 6px; justify-content: flex-end; margin-top: 16px;"),
                style="padding: 14px; background: #111318; border: 1px solid #2d3139; border-radius: 6px;"
            ),
            style="position: fixed; right: 24px; top: 100px; width: 300px; z-index: 10003; pointer-events: auto !important;"
        )


        css_rules = f"""
        body::before {{
            content: "" !important;
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            background: rgba(9, 13, 22, 0.75) !important;
            z-index: 10000 !important;
            pointer-events: auto !important;
        }}
        #{target} {{
            position: relative !important;
            z-index: 10001 !important;
            border: 2px solid #60a5fa !important;
            pointer-events: auto !important;
            box-shadow: 0 0 25px rgba(96, 165, 250, 0.4) !important;
        }}
        .navbar {{ position: relative !important; z-index: 10002 !important; pointer-events: auto !important; }}
        body {{ pointer-events: none !important; }}
        [id^="tut_"], .btn-sm {{ pointer-events: auto !important; }}
        """
        return panel_ui, css_rules

    def start(self): self.current_step.set(1)
    def next(self): self.current_step.set(self.current_step() + 1)
    def prev(self): self.current_step.set(self.current_step() - 1)
    def stop(self): self.current_step.set(0)
