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


import asyncio
import pandas as pd
from typing import List
import logging
import numpy as np

logger = logging.getLogger(__name__)

class SatalyzeStrategyResolver:
    """Handles view extraction"""
    def __init__(self, db):
        self.db = db
    
    async def execute_nationwide(self, ticker_clean: str) -> pd.DataFrame:
        """Nationwide cross sectional"""
        alpha_signals_df = await self.db.fetch_alpha_signals_and_peer_ranks()
        if not alpha_signals_df.empty:
            return alpha_signals_df[alpha_signals_df['ticker'] == ticker_clean]
        return alpha_signals_df
    
    async def execute_single_store(self, site_id: str, ticker_clean:str) -> pd.DataFrame:
        """single store basic view"""
        query = """
        SELECT s.site_id, lr.ticker, cc.year, cc.date, s.latitude, s.longitude, cc.car_count, s.total_capacity, cc.raw_image_save_path, cc.label_image_save_path, fin.total_revenue, fin.capex, fin.gross_ppe
        FROM car_counts cc
        LEFT JOIN sites s on cc.site_id = s.site_id
        LEFT JOIN lot_registry lr ON s.site_id = lr.site_id AND cc.year >= lr.active_from AND (lr.active_to IS NULL OR cc.year <= lr.active_to)                    
        LEFT JOIN financial_metrics fin ON lr.ticker = fin.ticker AND cc.year = fin.year
        WHERE cc.site_id = ?
        ORDER BY cc.date ASC;
        """

        target_site = site_id[0] if isinstance(site_id, list) else site_id

        def _sync_read():
            import sqlite3
            with sqlite3.connect(self.db.db_path) as s_conn:
                df = pd.read_sql_query (query, s_conn, params = (target_site,))
                if df.empty and ticker_clean != "PRIVATE_ASSET":
                    return df[df['ticker'] == ticker_clean]
                return df
        return await asyncio.to_thread(_sync_read)
    
    # def execute_batch_fleet(self, logger_df: pd.DataFrame) -> pd.DataFrame:
    #     """Mutli location fleet"""
    #     if logger_df.empty:
    #         return pd.DataFrame(columns=["date", "longitude", "latitude", "car_count", "year"])
    #     return logger_df.sort_values(by="date", ascending=False).reset_index(drop=True)

    async def execute_batch_fleet(self, fleet_site_ids: list, ticker_clean: str) -> pd.DataFrame:
        """Multi-location fleet view pulling full historical timelines for all target sites."""
        if not fleet_site_ids:
            return pd.DataFrame()

        # Clean list to ensure no accidental duplicates or weird data types
        clean_ids = list(set([str(sid).strip() for sid in fleet_site_ids if sid]))
        
        # Dynamically build the exact number of ? placeholders needed for the IN clause
        placeholders = ",".join(["?"] * len(clean_ids))

        query = f"""
        SELECT 
            s.site_id, 
            lr.ticker, 
            cc.year, 
            cc.date, 
            s.latitude, 
            s.longitude, 
            cc.car_count, 
            s.total_capacity, 
            cc.raw_image_save_path, 
            cc.label_image_save_path, 
            fin.total_revenue, 
            fin.capex, 
            fin.gross_ppe
        FROM car_counts cc
        LEFT JOIN sites s ON cc.site_id = s.site_id
        LEFT JOIN lot_registry lr ON s.site_id = lr.site_id 
            AND cc.year >= lr.active_from 
            AND (lr.active_to IS NULL OR cc.year <= lr.active_to)                    
        LEFT JOIN financial_metrics fin ON lr.ticker = fin.ticker 
            AND cc.year = fin.year
        WHERE cc.site_id IN ({placeholders})
        ORDER BY s.site_id ASC, cc.date ASC;
        """

        def _sync_read():
            import sqlite3
            with sqlite3.connect(self.db.db_path) as s_conn:
                # Pass the array of clean IDs directly as query parameters
                df = pd.read_sql_query(query, s_conn, params=clean_ids)
                
                if df.empty and ticker_clean != "PRIVATE_ASSET":
                    return df[df['ticker'] == ticker_clean]
                return df

        return await asyncio.to_thread(_sync_read)


    async def execute_comparison(self, site_ids: List[str]) -> pd.DataFrame:
        """Compares hitroical timelinesa for specfic locations die by side"""
        if not site_ids:
            return pd.DataFrame()
        
        query = """
        SELECT cc.year, cc.date, cc.site_id, cc.car_count, s.total_capacity, 
            (cc.car_count / s.total_capacity) AS site_utilization_rate
        FROM car_counts cc
        JOIN sites s on cc.site_id = s.site_id
        WHERE cc.site_id IN ({})
        ORDER BY cc.date ASC, cc.site_id ASC
        """.format(','.join(['?'] * len(site_ids)))

        def _sync_read():
            import sqlite3
            with sqlite3.connect(self.db.db_path) as s_conn:
                return pd.read_sql_query(query, s_conn, params =list(site_ids))
        
        df = await asyncio.to_thread(_sync_read)

        if not df.empty:
            df = df.pivot_table(
                index = 'date',
                columns = 'site_id', 
                values = ['car_count', 'site_utilization_rate'],
                aggfunc='mean'
            )
            df.columns = [f"{val}_{site}" for val, site in df.columns]
            df = df.reset_index()
        return df 
    


# cd C:\Users\b\Desktop\Satalyz

# PS C:\Users\b\Desktop\Satalyz> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
# >>
# PS C:\Users\b\Desktop\Satalyz> .\env_test\Scripts\Activate.ps1


 

