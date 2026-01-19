import akshare as ak
import pandas as pd
import os
import time
from src.utils import DATA_DIR, setup_logger

logger = setup_logger('MarketData')
ETF_CACHE_FILE = os.path.join(DATA_DIR, 'etf_cache.csv')

class MarketData:
    def __init__(self):
        self.etf_df = None
        self._load_or_update_cache()

    def _load_or_update_cache(self):
        # Check if cache exists and is recent (e.g., < 24 hours)
        if os.path.exists(ETF_CACHE_FILE):
            file_time = os.path.getmtime(ETF_CACHE_FILE)
            if time.time() - file_time < 86400: # 24 hours
                try:
                    self.etf_df = pd.read_csv(ETF_CACHE_FILE, dtype=str)
                    logger.info("Loaded ETF list from local cache")
                    return
                except Exception as e:
                    logger.warning(f"Failed to load cache: {e}")
        
        # Update cache
        self.update_cache()

    def update_cache(self):
        logger.info("Updating ETF list from AKShare...")
        try:
            # fund_etf_spot_em returns active ETFs
            self.etf_df = ak.fund_etf_spot_em()
            # Rename columns for consistency if needed, but akshare usually returns:
            # 序号, 代码, 名称, 最新价, ...
            # We mainly need 代码 (code) and 名称 (name)
            self.etf_df.to_csv(ETF_CACHE_FILE, index=False)
            logger.info(f"Updated ETF cache with {len(self.etf_df)} records")
        except Exception as e:
            logger.error(f"Failed to fetch ETF list from AKShare: {e}")
            # If update fails, try to load old cache even if expired
            if os.path.exists(ETF_CACHE_FILE):
                self.etf_df = pd.read_csv(ETF_CACHE_FILE, dtype=str)

    def search_etfs(self, keywords):
        """
        Search ETFs by list of keywords.
        Returns a list of dicts: {'code': ..., 'name': ...}
        """
        if self.etf_df is None or self.etf_df.empty:
            logger.warning("ETF data not available")
            return []

        results = []
        # Ensure Code and Name columns exist. Akshare often uses Chinese column names.
        # Usually '代码' and '名称'
        code_col = '代码'
        name_col = '名称'
        
        if code_col not in self.etf_df.columns or name_col not in self.etf_df.columns:
             # Try to find columns that look like code or name if standard names fail
             logger.error(f"Unexpected columns in ETF data: {self.etf_df.columns}")
             return []

        for keyword in keywords:
            # Simple substring match
            matches = self.etf_df[self.etf_df[name_col].str.contains(keyword, na=False)]
            for _, row in matches.iterrows():
                results.append({
                    'code': str(row[code_col]),
                    'name': row[name_col],
                    'match_keyword': keyword
                })
        
        # Deduplicate by code
        unique_results = []
        seen_codes = set()
        for r in results:
            if r['code'] not in seen_codes:
                unique_results.append(r)
                seen_codes.add(r['code'])
        
        return unique_results

    def get_holdings(self, code):
        """
        Get top 10 holdings for a given ETF code.
        """
        logger.info(f"Fetching holdings for ETF {code}")
        try:
            # Try newer/alternate API names if original is missing
            # fund_portfolio_hold_em fits the naming convention better for recent versions
            if hasattr(ak, 'fund_portfolio_hold_em'):
                # Some akshare functions use 'symbol', others just positional
                # We'll try symbol first
                try:
                    df = ak.fund_portfolio_hold_em(symbol=code)
                except TypeError:
                    df = ak.fund_portfolio_hold_em(code)
            elif hasattr(ak, 'fund_portfolio_hold'):
                 # This usually requires date
                 logger.warning("fund_portfolio_hold requires date, skipping for now")
                 return []
            else:
                 # Fallback
                 df = ak.fund_portfolio_holdings_em(symbol=code)

            if df is None or df.empty:
                return []
            
            # Usually returns columns like: 序号, 股票代码, 股票名称, 占净值比例...
            # We want top 10
            all_holdings = df.to_dict('records')
            
            filtered_holdings = []
            for h in all_holdings:
                s_code = str(h.get('股票代码', ''))
                # Exclude Star Market (688), Beijing (8, 4)
                if s_code.startswith('688') or s_code.startswith('8') or s_code.startswith('4'):
                    continue
                filtered_holdings.append(h)

            return filtered_holdings[:10]  # Return top 10 available after filtering
        except Exception as e:
            logger.error(f"Failed to fetch holdings for {code}: {e}")
            return []
