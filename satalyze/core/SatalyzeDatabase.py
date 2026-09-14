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
import sqlite3
import uuid
import asyncio
from typing import Optional, AsyncIterator
from contextlib import asynccontextmanager
import aiosqlite
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class SatalyzeDatabaseManager:
    """Async database for car detections and finanical metrics"""
    def __init__(self, db_path: str = "satalyze.db"):
        self.db_path = db_path

    @asynccontextmanager
    async def _get_connection(self) -> AsyncIterator[aiosqlite.Connection]:
        """Establish connection async"""
        conn = None
        try:
            conn = await aiosqlite.connect(self.db_path, timeout=30.0, check_same_thread = False)
            conn.isolation_level = None

            await conn.execute("PRAGMA foreign_keys = ON;")
            await conn.execute("PRAGMA journal_mode = WAL;")
            await conn.execute("PRAGMA synchronous = NORMAL;")
            await conn.execute("PRAGMA cache_size = -64000;")

            yield conn
        except (aiosqlite.Error, sqlite3.Error) as e: 
            logger.exception(f"Connection error {e}")
            raise
        finally: 
            if conn:
                await conn.close()

    async def init_db(self):
        """Tables and views initialize"""
        async with self._get_connection() as conn:
            try: 
                await conn.execute("BEGIN IMMEDIATE;")

                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS ui_settings (
                        key TEXT PRIMARY KEY, 
                        value TEXT
                    )
                """)

                # sites default parking lt size 100 ( change later on  to dynamaic)
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS sites (
                    site_id TEXT PRIMARY KEY,
                    total_capacity REAL NOT NULL DEFAUlT 100.0,
                    latitude REAL NOT NULL CHECK(latitude BETWEEN -90.0 AND 90.0),
                    longitude REAL NOT NULL CHECK(longitude BETWEEN -180.0 AND 180.0),
                    UNIQUE(latitude, longitude) 
                    );
                ''')


                # car counts
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS car_counts(
                    observation_id TEXT PRIMARY KEY,
                    site_id TEXT NOT NULL, 
                    year INTEGER NOT NULL CHECK(year > 1900),
                    date TEXT NOT NULL, 
                    car_count REAL NOT NULL CHECK(car_count >= 0),
                    raw_image_save_path TEXT NOT NULL UNIQUE,
                    label_image_save_path TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (site_id) REFERENCES sites(site_id) ON DELETE CASCADE
                    );
                ''')

                # lot to ticker registry
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS lot_registry (
                    ticker TEXT NOT NULL CHECK(length(ticker) BETWEEN 1 AND 10),
                    site_id TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    active_from INTEGER NOT NULL CHECK(active_from > 1900),
                    active_to INTEGER DEFAULT NULL,
                    PRIMARY KEY (site_id, active_from),
                    FOREIGN KEY (site_id) REFERENCES sites(site_id) ON DELETE RESTRICT
                    );
                ''')

                # financial metrics table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS financial_metrics (
                    ticker TEXT NOT NULL,
                    year INTEGER NOT NULL CHECK(year > 1900),
                    date TEXT,
                    total_revenue REAL NOT NULL CHECK(total_revenue >= 0.0),
                    capex REAL CHECK(capex >= 0.0),
                    gross_ppe REAL CHECK(gross_ppe >= 0.0),
                    PRIMARY KEY (ticker, year, date)
                    );
                ''')


                await conn.execute("CREATE INDEX IF NOT EXISTS idx_cc_site_date ON car_counts(site_id, date);")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_lot_lookup ON lot_registry(ticker, active_from, active_to);")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_lot_coords ON lot_registry(latitude, longitude);")


                await conn.execute('''
                    CREATE VIEW IF NOT EXISTS v_nationwide_store_aggregation AS
                    SELECT 
                        COALESCE(lr.ticker, s.site_id) AS ticker,
                        cc.year,
                        cc.date,
                        COUNT(s.site_id) AS sampled_site_count,
                        SUM(cc.car_count) AS aggregated_observed_cars,
                        SUM(s.total_capacity) AS aggregated_sample_capacity,
                        (SUM(cc.car_count) / SUM(s.total_capacity)) AS nationwide_utilization_index
                    FROM car_counts cc
                    LEFT JOIN sites s on cc.site_id = s.site_id
                    LEFT JOIN lot_registry lr ON s.site_id = lr.site_id AND cc.year >= lr.active_from AND (lr.active_to IS NULL OR cc.year <=lr.active_to)
                    GROUP BY COALESCE(lr.ticker, s.site_id), cc.year, cc.date;
                ''')


                await conn.execute('''
                    CREATE VIEW IF NOT EXISTS v_alpha_and_peer_ranks AS
                    SELECT 
                        nat.*,
                        fin.total_revenue,
                        fin.capex,
                        fin.gross_ppe,
                        CASE
                            WHEN fin.total_revenue IS NOT NULL THEN (fin.total_revenue / nat.nationwide_utilization_index)
                            ELSE NULL
                        END AS revenue_to_utilization_ratio,
                        CASE
                            WHEN fin.capex IS NOT NULL THEN (fin.capex / nat.nationwide_utilization_index)
                            ELSE NULL
                        END AS capex_to_utilization_ratio,
                        CASE
                            WHEN fin.gross_ppe IS NOT NULL THEN (fin.gross_ppe / nat.nationwide_utilization_index)
                            ELSE NULL
                        END AS gppe_to_utilization_ratio,
                        CASE
                            WHEN fin.total_revenue IS NOT NULL THEN
                                DENSE_RANK() OVER (PARTITION BY nat.year ORDER BY (fin.total_revenue / nat.nationwide_utilization_index) DESC)
                            ELSE NULL
                        END AS peer_efficiency_rank
                    FROM v_nationwide_store_aggregation nat
                    LEFT JOIN financial_metrics fin ON nat.ticker = fin.ticker AND nat.year = fin.year;
                ''')


                await conn.execute("COMMIT;")
                logger.info(f'Schemas successfully created')

            except (aiosqlite.Error, sqlite3.Error) as e:
                await conn.execute("ROLLBACK;")
                logger.exception(f'Initilaization of schemas failed {e}')
                raise

    async def get_settings(self, key: str, default:str = None) -> str:
        query = "SELECT value FROM ui_settings where key = ?"

        try:
            async with self._get_connection() as conn:
                async with conn.execute(query, (key,)) as cursor: 
                    row = await cursor.fetchone()
                    if row and row[0] is not None:
                        return str(row[0]).strip()
                    return default
        except Exception as e:
            logger.warning(f'Could not gather saved settings reverting to default {e}')
            return default

    async def set_settings(self, key: str, value: str)-> None:
        try:
            async with self._get_connection() as conn:
                await conn.execute(
                    "INSERT OR REPLACE INTO ui_settings (key, value) VALUES (?, ?)", (key, str(value))
                )
        except Exception as e:
            logger.warning(f'Could not save settings. {e}')

    async def check_if_img_processed(self, image_path: str) -> bool:
        """Fast check to see if image already exists | prevent unneccessary gee api call"""
        query = """
            SELECT 1 FROM car_counts
            WHERE raw_image_save_path = ? or label_image_save_path = ?
            LIMIT 1;
        """

        try: 
            async with self._get_connection() as conn:
                async with conn.execute(query, (image_path, image_path)) as cursor:
                    row = await cursor.fetchone()
                    return row is not None
        except (aiosqlite.Error, sqlite3.Error) as e:
            logger.warning(f"Lookup failed for path {image_path}, | {e}")
            return False


    async def insert_streaming_observation(self, 
                                           site_id: str, year: int, car_count: float, total_capacity: float,
                                           lat: float, lon: float, raw_image_save_path: str, label_image_save_path: str, date) -> bool:
        """Writes telemetry profiles"""
        obs_id = f"OBS_{uuid.uuid4().hex[:12]}"

        try:
            async with self._get_connection() as conn:
                await conn.execute("BEGIN IMMEDIATE TRANSACTION;")
                await conn.execute("""
                    INSERT OR IGNORE INTO sites (site_id, total_capacity, latitude, longitude)
                    VALUES (?, ?, ?, ?);
                """, (site_id, float(total_capacity), float(lat), float(lon)))

                await conn.execute("""
                    INSERT INTO car_counts (observation_id, site_id, year, car_count, raw_image_save_path, label_image_save_path, date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(label_image_save_path) DO UPDATE SET
                        car_count = excluded.car_count, year = excluded.year, date = excluded.date;
                """, (obs_id, site_id, int(year), float(car_count), raw_image_save_path, label_image_save_path, date))
                
                await conn.commit()
                return True
        except Exception as e:
            await conn.rollback()
            logger.warning(f'Writing database error {e}')
            return False
        

    async def assign_site_to_lot(self, ticker: str, year: int, site_id: str, lat: float, lon: float) -> bool:
        """Maps coordinates to a ticker symbol"""
        cleaned_ticker = ticker.upper().strip() if ticker else ""
        if not cleaned_ticker or len(cleaned_ticker) > 10 or "PRIVATE" in cleaned_ticker:
            logger.info(f"skipping lot registry, no valid ticker {ticker}")
            return False
        
        query = """ 
            INSERT OR REPLACE INTO lot_registry (ticker, site_id, latitude, longitude, active_from, active_to)
            VALUES (?, ?, ?, ?, ?, NULL);
        """ 

        try: 
            async with self._get_connection() as conn:
                await conn.execute("BEGIN IMMEDIATE;")
                await conn.execute("""
                    INSERT OR IGNORE INTO sites (site_id, latitude, longitude)
                    VALUES (?, ?, ?);
                """, (site_id, float(lat), float(lon)))

                await conn.execute(""" 
                    INSERT INTO lot_registry (ticker, site_id, latitude, longitude, active_from, active_to)
                    VALUES (?, ?, ?, ?, ?, NULL)
                    ON CONFLICT(site_id, active_from)
                    DO UPDATE SET ticker = excluded.ticker, latitude = excluded.latitude, longitude = excluded.longitude;
                """, (cleaned_ticker, site_id, float(lat), float(lon), int(year)) )
                await conn.execute("COMMIT;")
                return True
            
        except (aiosqlite.Error, sqlite3.Error) as e:
            logger.exception(f'Database commit error for ticker to coord binding {e}')
            return False

    async def save_financial_dataframe(self, df_finance: pd.DataFrame):
        """Finanical metrics dataframe to db"""
        if df_finance.empty:
            return

        required_fields = {'Ticker','Year', 'Date', 'Total_Revenue','CapEx','Gross_PPE'}
        if not required_fields.issubset(df_finance.columns):
            logger.warning(f'Missing schema attributes {required_fields - set(df_finance.columns)}')
            raise ValueError(f'Missing schema attributes {required_fields - set(df_finance.columns)}')

        def _prepare_payloads(df: pd.DataFrame):
            payloads = []
            for _, row in df.iterrows():
                rev = row['Total_Revenue']

                if pd.isna(rev) or rev is None or str(rev).strip() == "" or float(rev) == 0.0:
                    logger.debug(f'Missing rev for {row['Ticker']} in year {row['Year']}')
                    rev = 0.0
                else:
                    rev = float(rev)

                payloads.append((
                    row['Ticker'].upper().strip(),
                    int(row['Year']),
                    str(row["Date"]).strip(),
                    rev,
                    float(row['CapEx']) if pd.notna(row['CapEx']) else None,
                    float(row['Gross_PPE']) if pd.notna(row['Gross_PPE']) else None
                ))
                
            return payloads

        metrics_payload = await asyncio.to_thread(_prepare_payloads, df_finance)

        async with self._get_connection() as conn:
            try: 
                await conn.execute("BEGIN IMMEDIATE;")
                await conn.executemany("""
                    INSERT INTO financial_metrics (ticker, year, date, total_revenue, capex, gross_ppe)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ticker, year, date) DO UPDATE SET
                        total_revenue = excluded.total_revenue,
                        capex = excluded.capex, 
                        gross_ppe = excluded.gross_ppe;
                """, metrics_payload)
                await conn.execute("COMMIT;")
                logger.info("Database physical disk write transaction successfully locked.")
            except (aiosqlite.Error, sqlite3.Error) as e:
                await conn.execute("ROLLBACK;")
                logger.exception(f"Finanical processing failed {e}")
                raise
            
    async def fetch_combined_raw_data(self, ticker: Optional[str]= None) -> pd.DataFrame:
        """Extracts Data from db"""
        base_query = """
            SELECT s.site_id, lr.ticker, cc.year, cc.date, s.latitude, s.longitude, cc.car_count, s.total_capacity, cc.raw_image_save_path, cc.label_image_save_path, fin.total_revenue, fin.capex, fin.gross_ppe
            FROM car_counts cc
            LEFT JOIN sites s on cc.site_id = s.site_id
            LEFT JOIN lot_registry lr ON s.site_id = lr.site_id AND cc.year >= lr.active_from AND (lr.active_to IS NULL OR cc.year <= lr.active_to)                    
            LEFT JOIN (SELECT ticker, year, MIN(date) as date, total_revenue, capex, gross_ppe FROM financial_metrics GROUP BY ticker, year) fin ON lr.ticker = fin.ticker AND cc.year = fin.year
        """

        def _sync_read():
            with sqlite3.connect(self.db_path) as s_conn:
                if not ticker or "PRIVATE" in ticker.upper():
                    full_query = f"{base_query} GROUP BY s.site_id, cc.date;"
                    return pd.read_sql_query(full_query, s_conn)
                
                full_query = f"{base_query} WHERE lr.ticker = ? GROUP BY s.site_id, cc.date;"
                return pd.read_sql_query(full_query, s_conn, params=(ticker.upper().strip(),))
                

        try: 
            df = await asyncio.to_thread(_sync_read)
            df.columns = df.columns.str.replace("'","").str.replace('"',"").str.strip()

            if not df.empty and 'total_revenue' in df.columns:
                df = df.sort_values(by='year', ascending= True)
                fin_cols = ['total_revenue','capex','gross_ppe']

                df[fin_cols] = df.groupby('ticker')[fin_cols].bfill()
                df[fin_cols] = df.groupby('ticker')[fin_cols].ffill()
        except Exception as e:
            logger.exception(f'Database retrieval error {e}')
            return pd.DataFrame()

        # 2. Force clean your column names globally right here
        df.columns = df.columns.str.replace("'", "").str.replace('"', "").str.strip()

        # 🪵 LOG 2: This is now fully alive and will print beautifully!
        logger.info("==================================================")
        logger.info(" COMBINED DATAFRAME STATUS (After SQL Left Joins) ")
        logger.info("==================================================")
        logger.info(f" Total Rows Returned by SQL: {len(df)}")
        
        if not df.empty:
            valid_rev = df['total_revenue'].notna().sum()
            null_rev = df['total_revenue'].isna().sum()
            logger.info(f" -> 'total_revenue' metrics: {valid_rev} rows match | {null_rev} rows turned to NULL/NaN")
            logger.info(f" Unique tickers found in output matrix: {df['ticker'].dropna().unique()}")
        else:
            logger.warning(" -> The SQL join statements returned 0 total dataset rows.")
        logger.info("==================================================")

        # 3. NOW it is safe to exit the function completely
        return df


    async def fetch_alpha_signals_and_peer_ranks(self) -> pd.DataFrame:
        """Pulls calculated metrics nationwide"""
        query = "SELECT * FROM v_alpha_and_peer_ranks ORDER BY year ASC, peer_efficiency_rank ASC;"

        def _sync_read():
            with sqlite3.connect(self.db_path) as s_conn:
                return pd.read_sql_query(query, s_conn)

        try: 
            return await asyncio.to_thread(_sync_read)
        except Exception as e:
            logger.exception(f'View extraction failed {e}')
            return pd.DataFrame()

    async def upsert_site_capacity(self, site_id: str, capacity: float) -> bool:
        """Updates the total capacity in the sites table"""
        query = """
            UPDATE sites
            SET total_capacity = ?
            WHERE site_id = ?
        """

        try: 
            async with self._get_connection() as conn:
                await conn.execute("BEGIN IMMEDIATE;")
                await conn.execute(query, (float(capacity), site_id))
                await conn.execute("COMMIT;")
                return True
        except(aiosqlite.Error, sqlite3.Error) as e:
            logger.warning(f'Failed to update total capacity {e}')
            return False