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
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import logging

logger = logging.getLogger(__name__)

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

class CarbonSlateTheme(PlotThemeBase):
    """Refined enterprise dark slate-and-iron style layout theme."""
    def __init__(self):
        super().__init__()
        self.mpl_style = "dark_background"
        self.bg_color = "#1a1d24"       
        self.line_color = "#3b82f6"     
        self.glow_color = None
        self.node_color = "#3b82f6"     
        self.grid_color = "#2d3139"     
        self.spine_color = "#2d3139"    
        self.title_color = "#ffffff"    
        self.label_color = "#9ca3af"    
        self.font_name = "sans-serif"

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


class CarTrafficPlotterOG:
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
            logger.warning("Cannot plot. The provided DataFrame is completely empty.")
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
            logger.exception(f"Could not find any file located at path: {file_path}")
            return
        df = pd.read_csv(file_path)
        self.plot_timeline_from_dataframe(df, title=title)

  


class CarTrafficPlotter:
    """Core plotting engine that draws analytics charts using a swappable style theme."""
    def __init__(self, theme: PlotThemeBase = None):
        self.theme = theme if theme is not None else CarbonSlateTheme()

    def set_theme(self, theme: PlotThemeBase):
        self.theme = theme

    def _apply_base_styling(self, ax, title: str, xlabel: str, ylabel: str):
        """Internal helper to apply premium, unified style choices across all subplots."""
        ax.set_facecolor(self.theme.bg_color)
        ax.grid(True, which='both', color=self.theme.grid_color, linestyle='--', linewidth=0.8)
        
        for spine in ['top', 'bottom', 'left', 'right']:
            ax.spines[spine].set_color(self.theme.spine_color)
            ax.spines[spine].set_linewidth(1.2)

        ax.set_title(title.upper(), fontsize=11, fontweight='bold', color=self.theme.title_color, pad=12, fontname=self.theme.font_name)
        ax.set_xlabel(xlabel.upper(), fontsize=9, color=self.theme.label_color, labelpad=8, fontname=self.theme.font_name)
        ax.set_ylabel(ylabel.upper(), fontsize=9, color=self.theme.label_color, labelpad=8, fontname=self.theme.font_name)
        
        ax.tick_params(colors=self.theme.label_color, labelsize=8)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontname(self.theme.font_name)


    def plot_timeline_from_dataframe(self, df: pd.DataFrame, title: str = "SYS_VEHICLE_LOG // METRIC_CORRELATION"):
        """Generates a dual-axis visualization correlating car counts with financial metrics."""
        if df.empty:
            logger.warning("Cannot plot. The provided DataFrame is completely empty.")
            return

        # Data formatting
        plot_df = df.copy()
        plot_df['date'] = pd.to_datetime(plot_df['date'])
        plot_df = plot_df.sort_values('date')

        # Identify available financial columns (ignoring structural columns)
        exclude_cols = {'date', 'car_count'}
        financial_metrics = [col for col in plot_df.columns if col not in exclude_cols]

        # Matplotlib base style
        plt.style.use(self.theme.mpl_style)
        fig, ax1 = plt.subplots(figsize=(12, 6), facecolor=self.theme.bg_color)
        ax1.set_facecolor(self.theme.bg_color)

        # --- AXIS 1: CAR COUNT (Primary Y-Axis) ---
        if self.theme.glow_color:
            ax1.plot(
                plot_df['date'], plot_df['car_count'],
                color=self.theme.glow_color, alpha=0.3, linewidth=6, zorder=1
            )
            
        ax1.plot(
            plot_df['date'], plot_df['car_count'],
            marker='o', linestyle='-', 
            color=self.theme.line_color, 
            linewidth=2.5, 
            markersize=6, 
            markerfacecolor=self.theme.node_color, 
            markeredgecolor=self.theme.line_color, 
            zorder=3,
            label="Car Count"
        )

        ax1.set_ylabel("// TOTAL_UNIT_COUNT", fontsize=10, color=self.theme.label_color, labelpad=12, fontname=self.theme.font_name)
        ax1.tick_params(axis='y', colors=self.theme.label_color, labelsize=9)

        # --- AXIS 2: FINANCIAL METRICS (Secondary Y-Axis) ---
        ax2 = ax1.twinx()  # Shared X-axis, independent Y-axis
        
        # Color palette for financial metrics to distinguish them from the main car count
        # You can replace this with properties from self.theme if available
        fin_colors = ['#00ffcc', '#ff00ff', '#ffff00'] 
        
        for i, metric in enumerate(financial_metrics):
            color = fin_colors[i % len(fin_colors)]
            ax2.plot(
                plot_df['date'], plot_df['financial_metrics'],
                linestyle='--', 
                linewidth=1.8,
                color=color,
                zorder=2,
                label=metric.replace('_', ' ').upper()
            )

        ax2.set_ylabel("// FINANCIAL_METRICS_USD", fontsize=10, color=self.theme.label_color, labelpad=12, fontname=self.theme.font_name)
        ax2.tick_params(axis='y', colors=self.theme.label_color, labelsize=9)

        # --- GLOBAL THEME & STYLING ---
        ax1.grid(True, which='both', color=self.theme.grid_color, linestyle='--', linewidth=0.8)
        
        # Style spines for both axes
        for ax in [ax1, ax2]:
            for spine in ['top', 'bottom', 'left', 'right']:
                ax.spines[spine].set_color(self.theme.spine_color)
                ax.spines[spine].set_linewidth(1.5)
            for label in ax.get_yticklabels():
                label.set_fontname(self.theme.font_name)
                
        for label in ax1.get_xticklabels():
            label.set_fontname(self.theme.font_name)

        ax1.set_title(title.upper(), fontsize=13, fontweight='bold', color=self.theme.title_color, pad=25, fontname=self.theme.font_name)
        ax1.set_xlabel("// SOURCE_TIMELINE_COORDINATES", fontsize=10, color=self.theme.label_color, labelpad=12, fontname=self.theme.font_name)
        ax1.tick_params(axis='x', colors=self.theme.label_color, labelsize=9)

        # Unified Legend for both axes
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        leg = ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True, facecolor=self.theme.bg_color, edgecolor=self.theme.spine_color)
        for text in leg.get_texts():
            text.set_color(self.theme.label_color)
            text.set_fontname(self.theme.font_name)

        fig.autofmt_xdate() 
        plt.tight_layout()
        plt.show()


    # def plot_mega_density(self, batch_df: pd.DataFrame, title: str = "COMPREHENSIVE FLEET DENSITY ANALYTICS") -> plt.Figure:
    #     """Generates true independent location tracks grouped explicitly by physical site coordinates."""
    #     plt.style.use(self.theme.mpl_style)
    #     fig, ax = plt.subplots(figsize=(11, 5), facecolor=self.theme.bg_color)
        
    #     self._apply_base_styling(ax, title, "// OBSERVATION_DATE_SERIES", "// VEHICLE_TRAFFIC_COUNT")
        
    #     if batch_df is None or batch_df.empty:
    #         ax.text(0.5, 0.5, "FLEET_MATRIX_EMPTY / NO DATA AVAILABLE FOR THIS SELECTION", color="red", ha="center")
    #         return fig

    #     # 🧼 Force clean local copy and map headers to uniform lowercase
    #     df = batch_df.copy()
    #     df.columns = df.columns.str.replace("'", "").str.replace('"', "").str.strip().str.lower()
        
    #     # 🧼 THE CORE FIX: Find or construct a true physical site locator key
    #     # We search aggressively for explicit location markers first
    #     actual_id_col = None
    #     for candidate in ['site_id', 'site', 'location', 'ticker']:
    #         if candidate in df.columns:
    #             actual_id_col = candidate
    #             break
                
    #     # 🧠 THE DEFENSIVE BACKUP: If no text key exists, anchor directly to your coordinates!
    #     # This combines Lat + Lon into an un-fakeable location identifier string (e.g. "LOC_40.089_-75.395")
    #     if actual_id_col is None and 'latitude' in df.columns and 'longitude' in df.columns:
    #         df['constructed_site_id'] = "LOC_" + df['latitude'].astype(str) + "_" + df['longitude'].astype(str)
    #         actual_id_col = 'constructed_site_id'
    #         logger.info("Plotter: Constructed dynamic location mapping handles from coordinate floats.")
            
    #     # Absolute structural fallback rule to prevent runtime index failures
    #     if actual_id_col is None:
    #         df['constructed_site_id'] = "NODE_SITE_01"
    #         actual_id_col = 'constructed_site_id'

    #     # Safely identify your vehicle tracker numbers column vector
    #     val_col = 'car_count' if 'car_count' in df.columns else ('aggregated_observed_cars' if 'aggregated_observed_cars' in df.columns else df.columns[0])
        
    #     # Enforce chronological sorting and clear null cells
    #     df['date'] = pd.to_datetime(df['date'], errors='coerce')
    #     df = df.dropna(subset=['date', val_col])
    #     df = df.sort_values('date')

    #     unique_nodes = df[actual_id_col].unique()
    #     is_single_node = len(unique_nodes) == 1
    #     logger.info(f"Plotter: Separating chart canvas into {len(unique_nodes)} unique physical store lines.")

    #     # 1. 📈 PLOT PURE INDEPENDENT PLOTS GROUPED BY ACTUAL STORE LOCATIONS
    #     colors = ['#00ffcc', '#ffff00', '#00bfff', '#ff9900', '#9932cc', '#66c2a5']
    #     for idx, node in enumerate(unique_nodes):
    #         node_df = df[df[actual_id_col] == node]
    #         color = colors[idx % len(colors)]
            
    #         ax.plot(
    #             node_df['date'], 
    #             node_df[val_col], 
    #             linestyle='-',
    #             linewidth=2.5 if is_single_node else 1.2,
    #             alpha=1.0 if is_single_node else 0.5,
    #             marker='o',
    #             markersize=5,
    #             color=color,
    #             zorder=3,
    #             label=f"Store: {str(node).replace('SITE_', '').replace('LOC_', '')[:12]}"
    #         )

    #     # 2. ⚡ CALCULATE AND OVERLAY THE MACRO FLEET AVERAGE 
    #     fleet_average = df.groupby('date')[val_col].mean().reset_index().sort_values('date')
        
    #     if not fleet_average.empty:
    #         avg_color = '#ff007f' 
            
    #         # Only draw the ambient halo under-glow if there are genuinely multiple stores to average
    #         if not is_single_node:
    #             ax.plot(fleet_average['date'], fleet_average[val_col], color=avg_color, alpha=0.2, linewidth=7, zorder=4)
            
    #         ax.plot(
    #             fleet_average['date'], 
    #             fleet_average[val_col], 
    #             color=avg_color, 
    #             linestyle='--' if is_single_node else '-',
    #             linewidth=1.8 if is_single_node else 3.5,
    #             marker='D',          
    #             markersize=6,
    #             zorder=5,            
    #             label="FLEET AVERAGE (MEAN)"
    #         )

    #     # Apply design configurations and style frames
    #     ax.legend(loc='upper left', fontsize=7, frameon=True, facecolor=self.theme.bg_color, edgecolor=self.theme.spine_color)
    #     ax.grid(True, which='both', color=self.theme.grid_color, linestyle='--', linewidth=0.5)
        
    #     fig.autofmt_xdate()
    #     plt.tight_layout()
    #     return fig


    def plot_store_with_financials(self, traffic_df: pd.DataFrame, financial_df: pd.DataFrame, title: str = "STORE // TRAFFIC_VS_FINANCIAL_METRICS") -> plt.Figure:
        """Layout 1: Shared timeline dual-axis visualization mapping traffic markers and multiple corporate ledger assets."""
        plt.style.use(self.theme.mpl_style)
        fig, ax1 = plt.subplots(figsize=(11, 5), facecolor=self.theme.bg_color)
        
        # Axis 1: Satellite Vehicle Tracking
        self._apply_base_styling(ax1, title, "// METRICS_TIMELINE", "// CAR_COUNT_SIGNAL")
        
        lines = []
        labels = []

        # 🧼 FIX: Force use ONLY the clean data passed by the pipeline
        if traffic_df is not None and not traffic_df.empty:
            t_df = traffic_df.copy()
            t_df.columns = t_df.columns.str.lower() # Normalize case mapping
            
            time_col = 'date' if 'date' in t_df.columns else ('year' if 'year' in t_df.columns else t_df.columns[0])
            
            if pd.api.types.is_numeric_dtype(t_df[time_col]):
                t_df['plot_date'] = pd.to_datetime(t_df[time_col].astype(int).astype(str) + "-01-01")
            else:
                t_df['plot_date'] = pd.to_datetime(t_df[time_col])
                
            t_df = t_df.sort_values('plot_date')
            
            if self.theme.glow_color:
                ax1.plot(t_df['plot_date'], t_df['car_count'], color=self.theme.glow_color, alpha=0.2, linewidth=5)
            
            line1 = ax1.plot(t_df['plot_date'], t_df['car_count'], color=self.theme.line_color, marker='o', linewidth=2, label="Car Count")
            lines.extend(line1)
            labels.append("Car Count")
        
        # Axis 2: Corporate Business Metrics Overlay
        ax2 = ax1.twinx()
        ax2.spines['right'].set_color(self.theme.node_color)
        ax2.tick_params(colors=self.theme.node_color, labelsize=8)
        
        target_metrics = ['total_revenue', 'capex', 'gross_ppe']
        
        # 🧼 CRITICAL FIX: Evaluate using the clean financial dataframe passed from pipeline
        has_real_financials = False
        if financial_df is not None and not financial_df.empty:
            f_df = financial_df.copy()
            f_df.columns = f_df.columns.str.lower()
            
            # Check if columns exist and contain valid numeric numbers (greater than 0)
            valid_cols = [c for c in target_metrics if c in f_df.columns]
            if valid_cols:
                # Force conversion to numeric floats to drop text anomalies
                for col in valid_cols:
                    f_df[col] = pd.to_numeric(f_df[col], errors='coerce')
                # If it's a private asset run or holds only NaN/None cells, this evaluates to False
                has_real_financials = f_df[valid_cols].dropna(how='all').gt(0).any().any()

        if has_real_financials:
            date_col = 'year' if 'year' in f_df.columns else ('date' if 'date' in f_df.columns else f_df.columns[0])
            
            if pd.api.types.is_numeric_dtype(f_df[date_col]):
                f_df['plot_date'] = pd.to_datetime(f_df[date_col].astype(int).astype(str) + "-01-01")
            else:
                f_df['plot_date'] = pd.to_datetime(f_df[date_col])
                
            f_df = f_df.sort_values('plot_date')
            
            fin_colors = [self.theme.node_color, '#00ffcc', '#ffff00']
            styles = ['--', ':', '-.']
            
            color_idx = 0
            for metric in target_metrics:
                if metric in f_df.columns and f_df[metric].notna().any():
                    color = fin_colors[color_idx % len(fin_colors)]
                    style = styles[color_idx % len(styles)]
                    label_text = metric.replace('_', ' ').upper()
                    
                    line_f = ax2.plot(
                        f_df['plot_date'], f_df[metric], 
                        color=color, linestyle=style, marker='s', linewidth=1.8, label=label_text
                    )
                    lines.extend(line_f)
                    labels.append(label_text)
                    color_idx += 1
            
            ax2.set_ylabel("// CORPORATE_LEDGER_VALUES (USD $)", color=self.theme.node_color, fontsize=9, fontname=self.theme.font_name, labelpad=8)
        else:
            # Cleanly collapse right-side axis boundaries for Private Assets
            ax2.set_ylabel("// CORPORATE_LEDGER_VALUE (NO FINANCIAL DATA AVAILABLE)", color=self.theme.node_color, fontsize=8, fontname=self.theme.font_name, alpha=0.5)
            ax2.get_yaxis().set_visible(False)

        if lines:
            ax1.legend(lines, labels, loc='upper left')

        fig.autofmt_xdate()
        plt.tight_layout()
        return fig


    def generate_mode_plot(self, execution_mode: str, ticker_clean: str, traffic_df: pd.DataFrame, display_df: pd.DataFrame, financial_df: pd.DataFrame = None) -> plt.Figure:
        """Smart routing function enforcing strict execution matching to permanently defuse Z-patterns."""
        import matplotlib.pyplot as plt
        
        # 1. Clean and normalize column text layouts defensively across all inputs
        for df_obj in [traffic_df, display_df, financial_df]:
            if df_obj is not None and not df_obj.empty:
                df_obj.columns = df_obj.columns.str.replace("'","").str.replace('"',"").str.strip()

        # 🧼 STEP A: FORCE CASING COMPATIBILITY
        active_ticker = str(ticker_clean).upper().strip()
        mode_str = str(execution_mode).strip()

        # 🧼 STEP B: THE SHINY INTERCEPTOR FIREWALL
        # Extract what ticker is ACTUALLY inside the incoming dataframe matrix
        incoming_ticker = None
        test_df = display_df if display_df is not None else traffic_df
        if test_df is not None and not test_df.empty and 'ticker' in test_df.columns:
            incoming_ticker = str(test_df['ticker'].iloc[0]).upper().strip()

        # 🔒 THE TRAP BLOCK: If Shiny triggers a stale run pass where the requested ticker 
        # doesn't match the actual incoming dataset records, abort drawing instantly to stop the Z-pattern!
        if incoming_ticker and active_ticker != incoming_ticker:
            logger.warning(f"Plotter Interceptor: Stale pass block avoided! UI wanted '{active_ticker}', but Data holds '{incoming_ticker}'.")
            # Return an empty, clean visual placeholder canvas to clear the screen area
            fig, ax = plt.subplots(figsize=(11, 5), facecolor=self.theme.bg_color)
            ax.text(0.5, 0.5, f"// SYNCHRONIZING_CANVAS_GRID ({active_ticker})", color=self.theme.label_color, ha="center", va="center", fontname=self.theme.font_name, alpha=0.5)
            ax.axis('off')
            return fig

        # 2. PROCEED TO YOUR SECURE STABLE VISUALIZATION PATHS
        f_df = financial_df if financial_df is not None else pd.DataFrame()
        
        if mode_str == "SINGLE_STORE":
            return self.plot_store_with_financials(
                traffic_df=traffic_df, 
                financial_df=f_df, 
                title=f"Target: {active_ticker} // Traffic & Financial Matrix"
            )
            
        elif mode_str in ["BATCH_FLEET", "NATIONWIDE"]:
            return self.plot_mega_density(
                batch_df=display_df, 
                title=f"Fleet Density Matrix // Mode: {execution_mode}"
            )
            
        elif mode_str == "COMPARE":
            d_df = display_df.copy() if display_df is not None else pd.DataFrame()
            
            id_col = None
            for col in ['site_id', 'ticker', 'site']:
                if col in d_df.columns:
                    id_col = col
                    break
            
            if id_col and len(d_df[id_col].unique()) > 1:
                unique_sites = d_df[id_col].unique()
                df_a = d_df[d_df[id_col] == unique_sites[0]]
                df_b = d_df[d_df[id_col] == unique_sites[1]]
                label_a = str(unique_sites[0])[:8]
                label_b = str(unique_sites[1])[:8]
            else:
                if len(d_df) >= 2:
                    halfpoint = len(d_df) // 2
                    df_a = d_df.iloc[:halfpoint].copy()
                    df_b = d_df.iloc[halfpoint:].copy()
                else:
                    df_a = d_df
                    df_b = pd.DataFrame()
                label_a = "Site Delta"
                label_b = "Site Sigma"
                
            return self.plot_comparison(df_a, df_b, label_a=label_a, label_b=label_b)
            
        else:
            return self.plot_timeline_from_dataframe(
                df=traffic_df, 
                title=f"Target: {active_ticker} // Vehicle Tracking Log"
            )



    # def plot_mega_density(self, batch_df: pd.DataFrame, title: str = "COMPREHENSIVE FLEET DENSITY ANALYTICS") -> plt.Figure:
    #     """Layout 2: Generates clean, separate line graphs for each unique location on a shared timeline canvas."""
    #     plt.style.use(self.theme.mpl_style)
    #     fig, ax = plt.subplots(figsize=(11, 5), facecolor=self.theme.bg_color)
        
    #     self._apply_base_styling(ax, title, "// METRICS_TIMELINE", "// CAR_COUNT_SIGNAL")
        
    #     if batch_df is None or batch_df.empty:
    #         ax.text(0.5, 0.5, "NO DATA AVAILABLE FOR THIS SELECTION", color="red", ha="center", va="center")
    #         return fig

    #     # 🧼 Clean copy and force columns to lowercase to match your template structure
    #     df = batch_df.copy()
    #     df.columns = df.columns.str.replace("'", "").str.replace('"', "").str.strip().str.lower()
        
    #     # Enforce numeric typing on your traffic values
    #     df['car_count'] = pd.to_numeric(df['car_count'], errors='coerce')
        
    #     # Parse timeline using your single store logic block
    #     time_col = 'date' if 'date' in df.columns else ('year' if 'year' in df.columns else df.columns[0])
    #     if pd.api.types.is_numeric_dtype(df[time_col]):
    #         df['plot_date'] = pd.to_datetime(df[time_col].astype(int).astype(str) + "-01-01", errors='coerce')
    #     else:
    #         df['plot_date'] = pd.to_datetime(df[time_col], errors='coerce')
            
    #     df = df.dropna(subset=['plot_date', 'car_count'])

    #     # 🔍 Identify the identifier column directly
    #     id_col = 'site_id' if 'site_id' in df.columns else ('latitude' if 'latitude' in df.columns else None)
        
    #     if id_col:
    #         # Sift out every unique site marker present in the dataframe
    #         unique_sites = df[id_col].unique()
    #         colors = ['#00ffcc', '#ffff00', '#00bfff', '#ff9900', '#9932cc', '#66c2a5']
            
    #         # Print a clear debugger message to your console tracking the physical separation
    #         print(f"[DEBUGGER] Total unique sites detected in DataFrame: {len(unique_sites)} -> {list(unique_sites)}")
            
    #         # 📈 Loop over each individual site and plot its line explicitly
    #         for idx, site in enumerate(unique_sites):
    #             site_df = df[df[id_col] == site].sort_values('plot_date')
    #             color = colors[idx % len(colors)]
                
    #             print(f" -> Site [{site}] has {len(site_df)} sequential plot rows.")
                
    #             ax.plot(
    #                 site_df['plot_date'], 
    #                 site_df['car_count'], 
    #                 linestyle='-',
    #                 linewidth=2.0,  # Keeping line bold for now to make sure it's visible!
    #                 alpha=0.8,      # keeping high opacity for testing
    #                 marker='o',
    #                 markersize=5,
    #                 color=color,
    #                 label=f"Site: {str(site).replace('SITE_', '')[:10]}"
    #             )
    #     else:
    #         print("[DEBUGGER] Critical error: No grouping columns found ('site_id' or 'latitude' are missing).")
    #         ax.plot(df['plot_date'], df['car_count'], linestyle='-', label="Raw Tracking Fleet Stream")

    #     ax.legend(loc='upper left', fontsize=8, frameon=True, facecolor=self.theme.bg_color, edgecolor=self.theme.spine_color)
    #     ax.grid(True, which='both', color=self.theme.grid_color, linestyle='--', linewidth=0.5)
        
    #     fig.autofmt_xdate()
    #     plt.tight_layout()
    #     return fig








    def plot_mega_density(self, batch_df: pd.DataFrame, title: str = "COMPREHENSIVE FLEET DENSITY ANALYTICS") -> plt.Figure:
        """Layout 2: Generates separate location tracks and a fleet average on the top panel,
        and plots corporate financials on a aligned bottom sub-plot panel if they exist."""
        import matplotlib.pyplot as plt
        import pandas as pd
        
        plt.style.use(self.theme.mpl_style)
        
        if batch_df is None or batch_df.empty:
            fig, ax = plt.subplots(figsize=(11, 5), facecolor=self.theme.bg_color)
            ax.text(0.5, 0.5, "NO DATA AVAILABLE FOR THIS SELECTION", color="red", ha="center", va="center")
            return fig

        # 🧼 Clean copy and force columns to lowercase to match your template structure
        df = batch_df.copy()
        df.columns = df.columns.str.replace("'", "").str.replace('"', "").str.strip().str.lower()
        
        # Enforce numeric typing on traffic values
        df['car_count'] = pd.to_numeric(df['car_count'], errors='coerce')
        
        # Parse timeline using your single store logic block
        time_col = 'date' if 'date' in df.columns else ('year' if 'year' in df.columns else df.columns)
        if pd.api.types.is_numeric_dtype(df[time_col]):
            df['plot_date'] = pd.to_datetime(df[time_col].astype(int).astype(str) + "-01-01", errors='coerce')
        else:
            df['plot_date'] = pd.to_datetime(df[time_col], errors='coerce')
            
        df = df.dropna(subset=['plot_date', 'car_count']).sort_values('plot_date')

        # Check if valid financial metrics are present anywhere in the matrix
        target_metrics = ['total_revenue', 'capex', 'gross_ppe']
        valid_fin_cols = [c for c in target_metrics if c in df.columns]
        has_real_financials = False
        
        if valid_fin_cols:
            for col in valid_fin_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            has_real_financials = df[valid_fin_cols].dropna(how='all').gt(0).any().any()

        # 🗺️ DYNAMIC CANVAS GRID GRID RESOLUTION
        # If financials exist, we split the figure into a 2-row stacked subplot matrix
        if has_real_financials:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True, 
                                           gridspec_kw={'height_ratios': [2, 1]}, 
                                           facecolor=self.theme.bg_color)
        else:
            fig, ax1 = plt.subplots(figsize=(11, 5), facecolor=self.theme.bg_color)
            ax2 = None

        # Axis 1: Upper Satellite Vehicle Tracking Panel Layout
        self._apply_base_styling(ax1, title, "", "// CAR_COUNT_SIGNAL")
        if not has_real_financials:
            ax1.set_xlabel("// METRICS_TIMELINE", color=self.theme.label_color, fontname=self.theme.font_name)

        # Identify unique site tracking channels
        id_col = 'site_id' if 'site_id' in df.columns else ('latitude' if 'latitude' in df.columns else None)
        
        if id_col:
            unique_sites = df[id_col].unique()
            colors = ['#00ffcc', '#ffff00', '#00bfff', '#ff9900', '#9932cc', '#66c2a5']
            
            # 📈 1. Plot independent location tracks with faded transparency backgrounds
            for idx, site in enumerate(unique_sites):
                site_df = df[df[id_col] == site].sort_values('plot_date')
                color = colors[idx % len(colors)]
                
                ax1.plot(
                    site_df['plot_date'], 
                    site_df['car_count'], 
                    linestyle='-',
                    linewidth=1.5,
                    alpha=0.35,  # Reduced background track opacity
                    marker='o',
                    markersize=4,
                    color=color,
                    zorder=3,
                    label=f"Site: {str(site).replace('SITE_', '')[:10]}"
                )

            # ⚡ 2. Calculate and overlay the macro connected fleet average line
            fleet_average = df.groupby('plot_date')['car_count'].mean().reset_index().sort_values('plot_date')
            if not fleet_average.empty:
                avg_color = '#ff007f'
                if len(unique_sites) > 1:
                    ax1.plot(fleet_average['plot_date'], fleet_average['car_count'], color=avg_color, alpha=0.15, linewidth=6, zorder=4)
                
                ax1.plot(
                    fleet_average['plot_date'], 
                    fleet_average['car_count'], 
                    color=avg_color, 
                    linestyle='-',
                    linewidth=3.2,
                    marker='D',          
                    markersize=6,
                    zorder=5,            
                    label="FLEET AVERAGE (MEAN)"
                )
        else:
            ax1.plot(df['plot_date'], df['car_count'], linestyle='-', label="Raw Tracking Stream")

        ax1.legend(loc='upper left', fontsize=7, frameon=True, facecolor=self.theme.bg_color, edgecolor=self.theme.spine_color)
        ax1.grid(True, which='both', color=self.theme.grid_color, linestyle='--', linewidth=0.5)

        # Axis 2: Dedicated Lower Sub-Plot Corporate Financial Ledger Panel Layout
        if has_real_financials and ax2 is not None:
            self._apply_base_styling(ax2, "", "// METRICS_TIMELINE", "// CORPORATE_LEDGER_VALUES (USD $)")
            
            # Group by time stamps globally to map singular corporate ledger items cleanly
            fin_df = df.groupby('plot_date')[valid_fin_cols].first().reset_index().sort_values('plot_date')
            
            fin_colors = [self.theme.node_color if hasattr(self.theme, 'node_color') else '#3b82f6', '#00ffcc', '#ffff00']
            styles = ['--', ':', '-.']
            
            color_idx = 0
            for metric in target_metrics:
                if metric in fin_df.columns and fin_df[metric].notna().any():
                    color = fin_colors[color_idx % len(fin_colors)]
                    style = styles[color_idx % len(styles)]
                    label_text = metric.replace('_', ' ').upper()
                    
                    ax2.plot(
                        fin_df['plot_date'], fin_df[metric], 
                        color=color, linestyle=style, marker='s', linewidth=1.8, label=label_text
                    )
                    color_idx += 1
            
            ax2.legend(loc='upper left', fontsize=7, frameon=True, facecolor=self.theme.bg_color, edgecolor=self.theme.spine_color)
            ax2.grid(True, which='both', color=self.theme.grid_color, linestyle='--', linewidth=0.5)

        fig.autofmt_xdate()
        plt.tight_layout()
        return fig
