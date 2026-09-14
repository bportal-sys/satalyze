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
import yfinance as yf 
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class FinancialExtractor:
    """Handles sting index parsing to extract metrics"""

    @staticmethod
    def extract_row(df: pd.DataFrame, label_keywords: List[str]) -> Optional[pd.Series]:
        """Looks for line items"""
        if df.empty:
            return None
        for index_name in df.index:
            if any(keyword.lower() in str(index_name).lower() for keyword in label_keywords):
                return df.loc[index_name]
        return None

class YFinanceClient:
    """Dedicated API client for yfinance library, Finanical metrics"""
    def __init__(self, ticker: str):
        self.ticker_str = ticker
        self.ticker = yf.Ticker(ticker)

    def fetch_raw_statements(self) -> Optional[dict]:
        """Grabs 3 finanical statements from yfinance API"""
        try: 
            financials = self.ticker.financials
            cash_flow = self.ticker.cashflow
            balance_sheet = self.ticker.balance_sheet

            if financials is None or financials.empty:
                logger.info(f'Incomplete statements {self.ticker_str}')
                return None

            return {
                "financials": financials,
                "cash_flow": cash_flow if cash_flow is not None else pd.DataFrame(),
                "balance_sheet": balance_sheet if balance_sheet is not None else pd.DataFrame()
            }

        except Exception as e:
            logger.exception(f"Network or API error {self.ticker_str}: {e}")
            return None

class FinancialDataManager:
    """Extraction, alignment, anf formatting"""
    def __init__(self, extractor: FinancialExtractor = FinancialExtractor()):
        self.extractor = extractor
        
    async def get_annual_metrics_async(self, ticker_str: str, start_date:str, end_date:str) -> pd.DataFrame:
        """Async finanicla extractino form yfinance"""
        return await asyncio.to_thread(self.get_annual_metrics, ticker_str, start_date, end_date)

    def _format_financial_dataframe(self, ticker_str: str, data_dict: Dict[str, pd.Series], start_year: int, end_year: int) -> pd.DataFrame:
        """Dataframe cleaner and formatter"""
        df = pd.DataFrame(data_dict)
        
        for target_col in ['Total_Revenue','CapEx','Gross_PPE']:
            if target_col not in df.columns:
                df[target_col] = None
        
        df.index = pd.to_datetime(df.index)

        df['Year'] = df.index.year
        df['Date'] = df.index.strftime('%Y-%m-%d')

        df['Ticker'] = ticker_str.upper().strip()
        df = df[(df['Year']>= start_year) & (df['Year'] <= end_year)]
        df = df.drop_duplicates(subset=['Year'])

        df = df.sort_values(by = 'Year', ascending=False)
        df = df.reset_index(drop=True)

        if 'CapEx' in df.columns:
            df['CapEx'] = df['CapEx'].apply(lambda x: abs(x) if pd.notna(x) and x is not None else None)

        ordered_columns = ['Ticker', 'Year', 'Date', 'Total_Revenue', 'CapEx', 'Gross_PPE']
        return df.reindex(columns=ordered_columns)

    def get_annual_metrics(self, ticker_str: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Metric timeline using client and extractor"""
        try:
            start_year = int(str(start_date).split("-")[0])
            end_year = int(str(end_date).split("-")[0])
        except Exception as e:
            logger.exception(f"Date string parser failed for yfinance{e}")
            start_year, end_year = 2000, 2030

        client = YFinanceClient(ticker_str)
        statements = client.fetch_raw_statements()

        if not statements:
            return pd.DataFrame()

        revenue_candidates = [
            "Total Revenue", "Revenue", "TotalRevenue", "Operating Revenue", 
            "Total Operating Revenue", "Gross Sales"
        ]
        
        capex_candidates = [
            "Capital Expenditure", "CapEx", "Capital Expenditures", "CapitalExpenditure",
            "Payments For Property Plant And Equipment", "Purchase Of Property Plant And Equipment",
            "Net Income From Investing Activities" # emergency fallback row
        ]
        
        gppe_candidates = [
            "Gross Property Plant And Equipment", "Gross PPE", "Property Plant Equipment Gross",
            "GrossPropertyPlantAndEquipment", "Properties", "Property Plant And Equipment",
            "Total Property Plant And Equipment", "Net Property Plant And Equipment" # fallback if gross isn't split
        ]

        # Extract values using the expanded list maps
        rev = self.extractor.extract_row(statements['financials'], revenue_candidates)
        capex = self.extractor.extract_row(statements['cash_flow'], capex_candidates)
        gppe = self.extractor.extract_row(statements['balance_sheet'], gppe_candidates)

        extracted_data = {}
        if rev is not None: extracted_data['Total_Revenue'] = rev
        if capex is not None: extracted_data['CapEx'] = capex
        if gppe is not None: extracted_data['Gross_PPE'] = gppe

        if not extracted_data:
            logger.warning(f"Zero target metrics for {ticker_str}")
            return pd.DataFrame()

        return self._format_financial_dataframe(ticker_str, extracted_data, start_year, end_year)

class DataSynthesizer:
    """Blends alt dtaa with traditional financial metrics"""

    @staticmethod
    def merge_car_and_f_df(car_df: pd.DataFrame, fin_df: pd.DataFrame) -> pd.DataFrame:
        """Left merge on termporal intervals | replace with DB logic later on"""
        if car_df.empty or fin_df.empty:
            return pd.DataFrame()

        cars = car_df.copy()
        fins = fin_df.copy()

        cars['year'] = cars['year'].astype(int)
        fins['year'] = fins['year'].astype(int)

        merged = pd.merge(cars, fins, on='year', how='left')

        if 'total_Revenue' in merged.columns and 'car_Count' in merged.columns:
            merged['revenue_per_car'] = merged['total_revenue'] / merged['car_count']
        if 'gross_ppe' in merged.columns:
            merged['gross_ppe_per_car'] = merged['gross_ppe'] / merged['car_count']

        return merged


    @staticmethod
    def aggregate_national_fleet(site_df: pd.DataFrame) -> pd.DataFrame:
        """Combines individual locations into unified corporate timeline"""
        if site_df.empty:
            return pd.DataFrame()

        required_cols = {'Ticker', 'Year' ,'Car_Count','Total_Capacity', 'Site_ID'}
        if not required_cols.issubset(site_df.columns):
            logger.warning(f'Error, input missing {required_cols}')
            return pd.DataFrame()

        df = site_df.copy()
        df['Site_Utilization'] = df['Car_Count'] / df['Total_Capacity']

        grouped = df.groupby(['Ticker', 'Year']).agg(
            Sampled_Sites_Count=('Site_ID', 'count'),
            Aggregated_Observed_Cars=('Car_Count','sum'),
            Aggregated_Sampled_Capacity=('Total_Capacity','sum')
        ).reset_index()

        grouped['Nationwide_Utilization_Index'] = (
            grouped['Aggregated_Observed_Cars'] / grouped['Aggregated_Sampled_Capacity']
        )

        return grouped

    @staticmethod
    def generate_alpha_signals(national_metrics_df: pd.DataFrame, corporate_financial_df: pd.DataFrame) -> pd.DataFrame:
        """Combining Car count and financial metrics"""
        if national_metrics_df.empty or corporate_financial_df.empty:
            return pd.DataFrame()

        national_df = national_metrics_df.copy()
        fin_df = corporate_financial_df.copy()
        national_df['Year'] = national_df['Year'].astype(int)
        fin_df['Year'] = fin_df['Year'].astype(int)

        merged = pd.merge(national_df, fin_df, on=['Ticker','Year'], how='left')

        if 'Total_Revenue' in merged.columns:
            merged['Revenue_to_Utilization_Ratio'] = merged['Total_Revenue'] / merged['Nationwide_Utilization_Index']

        if 'CapEx' in merged.columns:
            merged['CapEx_to_Utilization_Velocity'] = merged['CapEx'] / merged['Nationwide_Utilization_Index']

        return merged

    @staticmethod
    def rank_cross_sectional_peers(all_company_signals_df: pd.DataFrame) -> pd.DataFrame:
        """Ranks peers by asset efficiency"""
        if all_company_signals_df.empty or 'Revenue_to_Utilization_Ratio' not in all_company_signals_df.columns:
            return all_company_signals_df

        df = all_company_signals_df.copy()

        df['Peer_Efficiency_Rank'] = df.groupby('Year')['Revenue_to_Utilization_Ratio'].rank(ascending=False, method='dense')

        return df.sort_values(by=['Year', 'Peer_Efficiency_Rank']).reset_index(drop = True)
