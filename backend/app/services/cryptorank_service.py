import aiohttp
from typing import List, Dict, Optional
from datetime import datetime
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class CryptoRankService:
    """Service for CryptoRank API - додатковий джерело даних"""
    
    def __init__(self):
        self.api_key = settings.CRYPTORANK_API_KEY
        self.base_url = "https://api.cryptorank.io/v1"
        
    async def get_currencies(self, limit: int = 50) -> List[Dict]:
        """Get top currencies from CryptoRank"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/currencies"
                params = {
                    "api_key": self.api_key,
                    "limit": limit
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', [])
                    else:
                        logger.error(f"CryptoRank error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"CryptoRank error: {e}")
            return []
    
    async def get_currency_details(self, symbol: str) -> Optional[Dict]:
        """Get detailed info about currency"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/currencies/{symbol}"
                params = {"api_key": self.api_key}
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data')
                    return None
                    
        except Exception as e:
            logger.error(f"Error: {e}")
            return None


cryptorank_service = CryptoRankService()
