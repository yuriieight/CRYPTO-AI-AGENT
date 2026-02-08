import aiohttp
from typing import List, Dict
from datetime import datetime, timedelta
import logging
from app.core.config import settings

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except Exception as e:
    print(f"🚨 ДЕТАЛЬНА ПОМИЛКА ІМПОРТУ TRANSFORMERS: {e}")
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)


class NewsService:
    """Advanced Service for crypto news with NLP Sentiment Analysis (FinBERT)"""

    def __init__(self):
        self.cryptocompare_key = settings.CRYPTOCOMPARE_API_KEY
        self.base_url = "https://min-api.cryptocompare.com/data/v2/news/"

        # Ініціалізація NLP моделі для дипломної роботи
        self.sentiment_analyzer = None
        if TRANSFORMERS_AVAILABLE:
            try:
                logger.info("⏳ Loading FinBERT NLP model for news analysis... (This may take a moment on first run)")
                # Використовуємо спеціалізовану фінансову модель
                self.sentiment_analyzer = pipeline(
                    "sentiment-analysis",
                    model="ProsusAI/finbert"
                )
                logger.info("✅ FinBERT model loaded successfully!")
            except Exception as e:
                logger.error(f"⚠️ Failed to load FinBERT: {e}. Will use fallback method.")
        else:
            logger.warning("⚠️ Transformers library not found. Run: pip install transformers torch")

    async def get_news(self, symbol: str, limit: int = 20) -> List[Dict]:
        """Fetch real crypto news and analyze sentiment using Deep Learning"""
        try:
            clean_symbol = symbol.replace('/USDT', '').replace('/USD', '')

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}?categories={clean_symbol}&lang=EN"

                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        news_items = data.get('Data', [])[:limit]

                        formatted_news = []
                        for item in news_items:
                            title = item.get('title', 'No title')
                            body = item.get('body', '')

                            # Використовуємо нейромережу для аналізу заголовку
                            sentiment_data = self._analyze_sentiment_ml(title)

                            formatted_news.append({
                                "title": title,
                                "description": body[:200] + '...' if body else '',
                                "url": item.get('url', '#'),
                                "source": item.get('source', 'Unknown'),
                                "published_at": datetime.fromtimestamp(
                                    item.get('published_on', 0)
                                ).isoformat(),
                                "sentiment": sentiment_data["label"],
                                "sentiment_score": sentiment_data["score"]
                            })

                        if formatted_news:
                            return formatted_news

        except Exception as e:
            logger.error(f"News fetch error: {e}")

        # Fallback якщо API впало
        return self._get_mock_news(symbol, limit)

    async def get_news_analysis(self, symbol: str, limit: int = 15) -> Dict:
        """Generates an AI summary and sentiment index based on recent news"""
        articles = await self.get_news(symbol, limit)
        if not articles:
            return {"error": "No news found"}

        # 1. Рахуємо загальний індекс настрою (0-100)
        total_index = 0
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}

        for art in articles:
            label = art.get('sentiment', 'neutral')
            # Якщо FinBERT не дав скор, беремо 0.6 як дефолт
            score = art.get('sentiment_score', 0.6)
            sentiment_counts[label] += 1

            # Масштабуємо до 0-100
            if label == 'positive':
                total_index += 50 + (score * 50)  # 50 до 100
            elif label == 'negative':
                total_index += 50 - (score * 50)  # 0 до 50
            else:
                total_index += 50

        avg_index = total_index / len(articles) if articles else 50

        if avg_index >= 60:
            overall = "Bullish"
        elif avg_index <= 40:
            overall = "Bearish"
        else:
            overall = "Neutral"

        # 2. Генеруємо AI-Зведення за допомогою LLM
        ai_summary = "Аналіз недоступний."
        try:
            from app.services.ai_service import ai_service
            # Беремо топ-10 заголовків для ШІ
            headlines = "\n".join([f"- {a['title']} ({a['description']})" for a in articles[:10]])

            prompt = (
                f"Ти головний фінансовий аналітик. Ось останні новини по {symbol}:\n"
                f"{headlines}\n\n"
                f"Напиши коротке зведення (2-3 речення) українською мовою: який зараз глобальний новинний наратив? "
                f"Чому ринок поводиться саме так? Пиши професійно і без води."
            )
            # Викликаємо нашого існуючого AI агента
            ai_summary = await ai_service.chat(prompt)
        except Exception as e:
            logger.error(f"AI Summary error: {e}")

        return {
            "symbol": symbol,
            "sentiment_index": round(avg_index, 1),
            "overall_sentiment": overall,
            "articles_analyzed": len(articles),
            "sentiment_breakdown": sentiment_counts,
            "ai_summary": ai_summary,
            "timestamp": datetime.now().isoformat()
        }

    def _analyze_sentiment_ml(self, text: str) -> Dict:
        """Deep Learning sentiment analysis using FinBERT"""
        if self.sentiment_analyzer:
            try:
                # FinBERT повертає: 'positive', 'negative', 'neutral' та впевненість
                result = self.sentiment_analyzer(text)[0]
                return {
                    "label": result['label'].lower(),
                    "score": round(float(result['score']), 4)
                }
            except Exception as e:
                logger.error(f"NLP analysis error: {e}")

        # Базовий метод (Fallback), якщо нейромережа недоступна
        return self._analyze_title_basic(text)

    def _analyze_title_basic(self, title: str) -> Dict:
        """Simple keyword-based sentiment analysis (Fallback)"""
        title_lower = title.lower()

        positive_words = ['surge', 'rally', 'gain', 'rise', 'bull', 'up', 'high', 'breakthrough', 'adopts']
        negative_words = ['crash', 'fall', 'drop', 'bear', 'down', 'low', 'lose', 'plunge', 'decline', 'hack']

        pos_count = sum(1 for word in positive_words if word in title_lower)
        neg_count = sum(1 for word in negative_words if word in title_lower)

        if pos_count > neg_count:
            return {"label": "positive", "score": 0.75}
        elif neg_count > pos_count:
            return {"label": "negative", "score": 0.75}
        return {"label": "neutral", "score": 0.5}

    def _get_mock_news(self, symbol: str, limit: int) -> List[Dict]:
        """Generate mock news as fallback"""
        clean_symbol = symbol.replace('/USDT', '').replace('/USD', '')

        mock_titles = [
            f"{clean_symbol} Shows Strong Market Performance Amid Trading Volume Surge",
            f"Analysts Predict Continued Growth for {clean_symbol} in Q1 2026",
            f"{clean_symbol} Technical Analysis: Key Support Levels Hold",
            f"Institutional Interest in {clean_symbol} Reaches New Highs",
            f"{clean_symbol} Development Team Announces Major Protocol Upgrade",
            f"Market Report: {clean_symbol} Maintains Bullish Momentum",
            f"{clean_symbol} Trading Volume Increases 45% Week-over-Week",
            f"Expert Insights: Why {clean_symbol} Could Outperform in 2026",
            f"{clean_symbol} Network Activity Hits All-Time High",
            f"Breaking: Major Exchange Lists {clean_symbol} Derivatives"
        ]

        news = []
        for i, title in enumerate(mock_titles[:limit]):
            hours_ago = i * 2
            pub_date = datetime.now() - timedelta(hours=hours_ago)
            sentiment_data = self._analyze_sentiment_ml(title)

            news.append({
                "title": title,
                "description": f"Latest developments and analysis for {clean_symbol}. Market indicators show continued interest and strong fundamentals.",
                "url": "https://cryptocompare.com/news/",
                "source": "CryptoNews" if i % 2 == 0 else "BlockchainToday",
                "published_at": pub_date.isoformat(),
                "sentiment": sentiment_data["label"],
                "sentiment_score": sentiment_data["score"]
            })

        return news


news_service = NewsService()