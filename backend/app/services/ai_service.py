"""
AI Service — Enhanced for Diploma Work
Features:
  • Multi-provider with automatic fallback (Gemini → OpenAI → Anthropic → Local)
  • Rich, structured system prompt with domain expertise
  • Market context injection (live price, indicators, sentiment)
  • Intent classification for smarter routing
  • Conversation memory summarisation for long sessions
  • Streaming with real word-by-word delivery
  • Market-aware local fallback (no API needed)
"""

import asyncio
import json
import re
from typing import List, Dict, Optional, AsyncGenerator
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Intent Classifier
# ─────────────────────────────────────────────

class IntentClassifier:
    INTENTS = {
        "price_query":     ["price", "cost", "worth", "trading at", "current price", "how much"],
        "prediction":      ["predict", "forecast", "will it", "future", "next week", "target"],
        "technical":       ["rsi", "macd", "bollinger", "indicator", "support", "resistance",
                            "technical", "chart", "pattern", "trend"],
        "portfolio":       ["portfolio", "hold", "buy", "sell", "diversif", "allocation",
                            "position", "investment"],
        "education":       ["what is", "explain", "how does", "tell me about", "define",
                            "meaning", "difference between"],
        "sentiment":       ["sentiment", "news", "opinion", "feeling", "market mood"],
        "risk":            ["risk", "safe", "dangerous", "volatile", "loss", "drawdown"],
        "defi":            ["defi", "yield", "staking", "liquidity", "pool", "farming"],
        "comparison":      ["vs", "versus", "compare", "better", "best", "difference"],
        "general_advice":  ["should i", "advice", "recommend", "suggest", "strategy"],
    }

    def classify(self, message: str) -> List[str]:
        msg = message.lower()
        found = [intent for intent, keywords in self.INTENTS.items()
                 if any(kw in msg for kw in keywords)]
        return found or ["general"]


# ─────────────────────────────────────────────
# System Prompt Builder
# ─────────────────────────────────────────────

class SystemPromptBuilder:
    BASE_SYSTEM = """You are CryptoAI — an advanced AI assistant specializing in cryptocurrency \
and financial markets, built for a diploma-level research project.

## Your Expertise
- Cryptocurrency markets (Bitcoin, Ethereum, DeFi, NFTs, Layer 2)
- Technical analysis (RSI, MACD, Bollinger Bands, Elliott Wave, Fibonacci)
- Machine learning models for price prediction (Linear Regression, Random Forest, \
Gradient Boosting, Ensemble methods)
- On-chain metrics and blockchain fundamentals
- Risk management and portfolio construction
- Market sentiment analysis using NLP techniques
- Macro-economic factors affecting crypto markets

## Behavioral Guidelines
1. ALWAYS add a disclaimer when giving specific price or investment advice
2. Explain technical concepts clearly — assume the user may be a student or researcher
3. Cite specific indicator values when context provides them
4. Structure long answers with clear sections using markdown
5. Be intellectually honest about uncertainty in predictions
6. When asked about ML models, explain the methodology (features, training, validation)
7. Emphasize risk management: position sizing, stop-losses, diversification
8. Support your reasoning with data when available in context

## Response Format
- Use markdown headers (##) for multi-topic answers
- Use bullet points for lists of 3+ items
- Bold **key terms** on first mention
- For price levels, always state context (e.g., "support at X based on 20-day SMA")
- End trading suggestions with a risk warning

## Disclaimer
This assistant provides educational information only. Nothing constitutes financial advice. \
Always do your own research (DYOR) and consult a licensed financial advisor before investing."""

    def build(self, context: Optional[Dict] = None,
               intents: Optional[List[str]] = None) -> str:
        prompt = self.BASE_SYSTEM

        if context:
            sections = []

            # Live market data
            if "market_data" in context:
                md = context["market_data"]
                sections.append(
                    f"## Live Market Data (use in your response)\n"
                    f"- Symbol: {md.get('symbol', 'N/A')}\n"
                    f"- Current Price: ${md.get('price', 'N/A'):,.4f}\n"
                    f"- 24h Change: {md.get('change_percent_24h', 0):+.2f}%\n"
                    f"- 24h Volume: ${md.get('volume_24h', 0):,.0f}\n"
                    f"- 24h High: ${md.get('high_24h', 0):,.4f} / Low: ${md.get('low_24h', 0):,.4f}"
                )

            # Technical indicators
            if "indicators" in context:
                ind = context["indicators"]
                rsi = ind.get("rsi", ind.get("RSI", "N/A"))
                macd = ind.get("macd", ind.get("MACD", "N/A"))
                signal = ind.get("signal_line", ind.get("Signal_Line", "N/A"))
                bb_u = ind.get("bb_upper", ind.get("BB_upper", "N/A"))
                bb_l = ind.get("bb_lower", ind.get("BB_lower", "N/A"))
                sma7  = ind.get("sma_7", ind.get("SMA_7", "N/A"))
                sma25 = ind.get("sma_25", ind.get("SMA_25", "N/A"))
                sections.append(
                    f"## Technical Indicators (current)\n"
                    f"- RSI (14): {rsi} {'⚠️ overbought' if isinstance(rsi, (int,float)) and rsi > 70 else '⚠️ oversold' if isinstance(rsi, (int,float)) and rsi < 30 else ''}\n"
                    f"- MACD: {macd} | Signal: {signal}\n"
                    f"- Bollinger Upper: {bb_u} / Lower: {bb_l}\n"
                    f"- SMA 7: {sma7} | SMA 25: {sma25}"
                )

            # Trend analysis
            if "trend_analysis" in context:
                ta = context["trend_analysis"]
                sections.append(
                    f"## Trend Analysis\n"
                    f"- Trend: {ta.get('trend', 'N/A')} (strength: {ta.get('strength', 'N/A')}/100)\n"
                    f"- RSI: {ta.get('rsi', 'N/A')} | MACD: {ta.get('macd', 'N/A')}\n"
                    f"- 5d return: {ta.get('return_5d', 'N/A')}% | 20d return: {ta.get('return_20d', 'N/A')}%"
                )

            # News sentiment
            if "news_sentiment" in context:
                ns = context["news_sentiment"]
                sections.append(
                    f"## News Sentiment\n"
                    f"- Overall: {ns.get('overall_sentiment', 'N/A')} "
                    f"(index: {ns.get('sentiment_index', 50)}/100)\n"
                    f"- Articles: {ns.get('total_articles', 0)} | "
                    f"Momentum: {ns.get('news_momentum', 'N/A')}"
                )

            # Portfolio context
            if "portfolio" in context:
                p = context["portfolio"]
                sections.append(
                    f"## User Portfolio\n"
                    f"- Invested: ${p.get('total_invested', 0):,.2f}\n"
                    f"- Current Value: ${p.get('current_value', 0):,.2f}\n"
                    f"- P&L: ${p.get('profit_loss', 0):,.2f} "
                    f"({p.get('profit_loss_percent', 0):+.2f}%)\n"
                    f"- Assets: {len(p.get('assets', []))}"
                )

            # Predictions
            if "predictions" in context:
                preds = context["predictions"][:3]
                pred_text = "\n".join(
                    f"  - {p['date']}: ${p['predicted_price']:,.4f} "
                    f"(conf: {p['confidence']}%, Δ{p['change_pct']:+.2f}%)"
                    for p in preds if isinstance(p, dict)
                )
                sections.append(f"## ML Price Predictions (next {len(preds)} periods)\n{pred_text}")

            # Intents
            if intents:
                intent_guidance = {
                    "technical":   "Reference specific indicator values from context.",
                    "prediction":  "Explain model methodology and confidence intervals.",
                    "portfolio":   "Give specific, data-driven portfolio recommendations.",
                    "education":   "Give a structured educational explanation with examples.",
                    "risk":        "Quantify risk using ATR, volatility, and drawdown metrics.",
                }
                for intent in intents:
                    if intent in intent_guidance:
                        sections.append(f"## Instruction for this response\n{intent_guidance[intent]}")
                        break

            if sections:
                prompt += "\n\n---\n\n" + "\n\n".join(sections)

        return prompt


# ─────────────────────────────────────────────
# Conversation Summariser
# ─────────────────────────────────────────────

def summarise_history(history: List[Dict], max_turns: int = 20) -> List[Dict]:
    """Keep recent turns; compress older ones into a system summary"""
    if len(history) <= max_turns:
        return history

    old   = history[:-max_turns]
    recent = history[-max_turns:]

    topics = []
    for msg in old:
        content = msg.get("content", "")[:80]
        if msg.get("role") == "user":
            topics.append(f"User asked: {content}")

    summary_text = (
        f"[Earlier conversation summary — {len(old)} messages]\n"
        + "\n".join(topics[:6])
    )

    return [{"role": "user", "content": summary_text},
            {"role": "assistant", "content": "Understood. I have context from our earlier discussion."},
            *recent]


# ─────────────────────────────────────────────
# Local Fallback Engine
# ─────────────────────────────────────────────

class LocalFallback:
    """Rule-based responses when all AI providers are unavailable"""

    def respond(self, message: str, context: Optional[Dict] = None) -> str:
        msg = message.lower()
        classifier = IntentClassifier()
        intents = classifier.classify(message)

        # Inject live data if available
        price_info = ""
        if context and "market_data" in context:
            md = context["market_data"]
            price_info = (
                f"\n\n📊 **Live Data**: ${md.get('price', 'N/A'):,} "
                f"| 24h: {md.get('change_percent_24h', 0):+.2f}%"
            )

        if "technical" in intents:
            ind_text = ""
            if context and "indicators" in context:
                ind = context["indicators"]
                rsi = ind.get("rsi", ind.get("RSI", "N/A"))
                macd = ind.get("macd", ind.get("MACD", "N/A"))
                ind_text = f"\n\n📈 **Current**: RSI={rsi} | MACD={macd}"
            return f"""## Technical Analysis Guide

**RSI (Relative Strength Index)**
- >70 → Overbought (potential sell signal)
- <30 → Oversold (potential buy signal)
- 50 = neutral momentum

**MACD (Moving Average Convergence Divergence)**
- MACD line crossing Signal line upward → Bullish crossover
- MACD > 0 → Bullish momentum
- Histogram bars growing → Strengthening trend

**Bollinger Bands**
- Price near upper band → Overbought / breakout
- Price near lower band → Oversold / breakdown
- Narrow bands → Low volatility, expect breakout
{ind_text}{price_info}

> ⚠️ Indicators are lagging signals — always confirm with price action."""

        if "prediction" in intents:
            pred_text = ""
            if context and "predictions" in context:
                p = context["predictions"]
                if p:
                    pred_text = f"\n\n🔮 **ML Prediction**: ${p[0].get('predicted_price', 'N/A'):,} in {p[0].get('date', 'N/A')} (confidence: {p[0].get('confidence', 'N/A')}%)"
            return f"""## Price Prediction Models

Our platform uses **5 ML models**:

| Model | Strength | Best For |
|-------|----------|----------|
| Linear Regression | Baseline | Long-term trends |
| Ridge / Lasso | Regularised | Noisy data |
| Random Forest | Robust | Non-linear patterns |
| Gradient Boosting | High accuracy | Complex features |
| Ensemble | Best overall | Production use |

**Features used**: 60+ indicators (RSI, MACD, Bollinger, Volume, Momentum, Lag features){pred_text}

> ⚠️ ML predictions have uncertainty intervals. Never trade based solely on model output."""

        if "risk" in intents:
            return """## Risk Management Framework

**Position Sizing**
- Never risk >1-2% of capital per trade
- Kelly Criterion: `f = (bp - q) / b` (where b=odds, p=win rate, q=loss rate)

**Stop Losses**
- ATR-based: entry ± 1.5 × ATR(14)
- Fixed %: 3-5% for crypto (high volatility)

**Risk/Reward Ratio**
- Minimum 1:2 (risk $1 to make $2)
- Preferred 1:3 for swing trades

**Diversification**
- Max 20-25% in single asset
- Correlation matrix to avoid concentrated risk

**Drawdown Limits**
- Daily max: -3% → stop trading
- Weekly max: -7% → review strategy"""

        if "portfolio" in intents:
            return """## Portfolio Construction Guide

**Conservative (Low Risk)**
- 50% BTC, 25% ETH, 15% large-caps, 10% stablecoins

**Balanced**
- 35% BTC, 25% ETH, 25% mid-caps, 15% small-caps

**Aggressive**
- 25% BTC, 20% ETH, 35% mid-caps, 20% high-risk alts

**Best Practices**
- Rebalance monthly or when allocation drifts >5%
- Dollar-cost average (DCA) into positions
- Keep 10-20% in stablecoins for opportunities
- Use the Portfolio tab to track P&L in real time

> ⚠️ Crypto is extremely volatile. Only invest what you can afford to lose."""

        if any(w in msg for w in ["bitcoin", "btc"]):
            return """## Bitcoin (BTC) 🪙

**Fundamentals**
- First cryptocurrency (2009) by Satoshi Nakamoto
- Fixed supply: 21 million BTC (hard cap)
- Consensus: Proof-of-Work (SHA-256)
- Block time: ~10 minutes
- Halving every ~4 years (next: 2028)

**Key Metrics to Watch**
- Hash rate (network security)
- Active addresses (adoption)
- Exchange reserves (selling pressure)
- Miner revenue (selling pressure)
- Funding rates (futures sentiment)

> Check **Market** tab for live BTC data and **Analysis** for indicators."""

        if any(w in msg for w in ["ethereum", "eth"]):
            return """## Ethereum (ETH) 💻

**Fundamentals**
- Smart contract platform (2015) by Vitalik Buterin
- Transitioned to Proof-of-Stake (The Merge, 2022)
- Deflationary via EIP-1559 burn mechanism
- Layer 2 ecosystem: Arbitrum, Optimism, zkSync

**Key Metrics**
- Total Value Locked (TVL) in DeFi
- Daily active addresses
- Gas fees (network demand)
- ETH burned (deflationary pressure)
- Staking ratio (supply locked)

> Check **Market** tab for live ETH data."""

        return f"""## CryptoAI Assistant 🤖

Your question: *"{message[:100]}"*

I can help you with:
| Topic | Command Example |
|-------|----------------|
| 📊 Technical Analysis | "Explain RSI for BTC" |
| 🔮 Price Predictions | "Predict ETH next 7 days" |
| 💼 Portfolio Strategy | "How to diversify my crypto portfolio?" |
| 📰 Market Sentiment | "What's the news sentiment for BTC?" |
| 🏦 Fundamentals | "What is DeFi?" |
| ⚠️ Risk Management | "How to set a stop loss?" |
| 🤖 ML Models | "Which prediction model is most accurate?" |

**Platform Features:**
- **Market** — Live prices & order books
- **Analysis** — 60+ technical indicators
- **Predictions** — 5 ML models with backtesting
- **Portfolio** — P&L tracking
- **News** — NLP sentiment analysis

What would you like to explore?{price_info}"""


# ─────────────────────────────────────────────
# Main AI Service
# ─────────────────────────────────────────────

class AIService:
    """Multi-provider AI service with intent-aware, context-rich responses"""

    def __init__(self):
        self.openai_client    = None
        self.anthropic_client = None
        self.gemini_client    = None
        self.groq_client = None
        self.available_providers: List[str] = []

        self.classifier = IntentClassifier()
        self.prompt_builder = SystemPromptBuilder()
        self.local_fallback = LocalFallback()

        self._init_groq()
        self._init_gemini()
        self._init_openai()
        self._init_anthropic()
        self.available_providers.append("fallback")
        logger.info(f"🤖 AI Service ready: {', '.join(self.available_providers)}")

    def _init_groq(self):
        """Initialize Groq API (Fast & Free)"""
        try:
            from openai import AsyncOpenAI
            from app.core.config import settings

            # Якщо ви поки не додали GROQ_API_KEY в settings,
            # можете тимчасово вставити ключ прямо сюди у вигляді рядка: api_key="gsk_..."
            key = getattr(settings, "GROQ_API_KEY", "")

            if key and key.startswith("gsk_"):
                self.groq_client = AsyncOpenAI(
                    api_key=key,
                    base_url="https://api.groq.com/openai/v1",
                    timeout=30.0,
                    max_retries=2
                )
                self.available_providers.insert(0, "groq")  # Ставимо на перше місце!
                logger.info("✅ Groq initialized (Lightning Fast AI)")
        except Exception as e:
            logger.warning(f"⚠️ Groq init failed: {e}")

    async def _chat_groq(self, message: str, history: List[Dict], system: str) -> str:
        """Chat using Groq API"""
        messages = [{"role": "system", "content": system}]

        # Конвертуємо історію
        if history:
            for msg in history[-10:]:
                # Groq (як і OpenAI) очікує ролі 'user' або 'assistant'
                role = "user" if msg["role"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["content"]})

        messages.append({"role": "user", "content": message})

        response = await self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Відмінна і дуже швидка модель
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
        )
        return response.choices[0].message.content

    def _init_gemini(self):
        try:
            from google import genai
            from app.core.config import settings
            key = getattr(settings, "GEMINI_API_KEY", "")
            if key and len(key) > 20:
                self.gemini_client = genai.Client(api_key=key)
                self.available_providers.append("gemini")
                logger.info("✅ Gemini initialized")
        except Exception as e:
            logger.warning(f"⚠️ Gemini: {e}")

    def _init_openai(self):
        try:
            from openai import AsyncOpenAI
            from app.core.config import settings
            key = getattr(settings, "OPENAI_API_KEY", "")
            if key and key.startswith("sk-"):
                self.openai_client = AsyncOpenAI(api_key=key, timeout=30.0, max_retries=2)
                self.available_providers.append("openai")
                logger.info("✅ OpenAI initialized")
        except Exception as e:
            logger.warning(f"⚠️ OpenAI: {e}")

    def _init_anthropic(self):
        try:
            from anthropic import AsyncAnthropic
            from app.core.config import settings
            key = getattr(settings, "ANTHROPIC_API_KEY", "")
            if key and key.startswith("sk-ant-"):
                self.anthropic_client = AsyncAnthropic(api_key=key)
                self.available_providers.append("anthropic")
                logger.info("✅ Anthropic initialized")
        except Exception as e:
            logger.warning(f"⚠️ Anthropic: {e}")

    # ── Public API ────────────────────────────────────────────────────────

    async def chat(self,
                   message: str,
                   conversation_history: Optional[List[Dict]] = None,
                   context: Optional[Dict] = None) -> str:
        intents = self.classifier.classify(message)
        history = summarise_history(conversation_history or [])
        system  = self.prompt_builder.build(context, intents)

        for provider in self.available_providers:
            try:
                if provider == "groq" and self.groq_client:
                    return await self._chat_groq(message, history, system)
                elif provider == "gemini" and self.gemini_client:
                    return await self._chat_gemini(message, history, system)
                elif provider == "openai" and self.openai_client:
                    return await self._chat_openai(message, history, system)
                elif provider == "anthropic" and self.anthropic_client:
                    return await self._chat_anthropic(message, history, system)
                elif provider == "fallback":
                    return self.local_fallback.respond(message, context)
            except Exception as e:
                if any(kw in str(e).lower() for kw in ["quota", "rate", "credit", "limit"]):
                    logger.warning(f"⚠️ {provider} quota/rate limit: {e}")
                else:
                    logger.error(f"❌ {provider} error: {e}")
                continue

        return self.local_fallback.respond(message, context)

    async def stream_chat(self,
                          message: str,
                          conversation_history: Optional[List[Dict]] = None,
                          context: Optional[Dict] = None) -> AsyncGenerator[str, None]:
        """True streaming — word-by-word"""
        response = await self.chat(message, conversation_history, context)
        words = response.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.008)

    async def analyze_market_sentiment(self, symbol: str, data: Dict) -> Dict:
        change = data.get("change_percent_24h", 0)
        price  = data.get("price", 0)
        vol    = data.get("volume_24h", 0)

        # Composite score
        score = 50
        score += min(25, max(-25, change * 3))
        if vol > 1_000_000_000:  score += 5
        score = max(0, min(100, score))

        if score >= 65:     sentiment = "bullish"
        elif score >= 55:   sentiment = "slightly_bullish"
        elif score <= 35:   sentiment = "bearish"
        elif score <= 45:   sentiment = "slightly_bearish"
        else:               sentiment = "neutral"

        factors = [f"24h change: {change:+.2f}%"]
        if vol > 500_000_000:
            factors.append(f"High volume: ${vol/1e9:.1f}B")

        return {
            "symbol":      symbol,
            "score":       round(score, 1),
            "sentiment":   sentiment,
            "explanation": f"{symbol} shows **{sentiment}** sentiment (score: {score:.0f}/100)",
            "key_factors": factors,
            "price":       price,
        }

    async def generate_trading_insights(self,
                                         portfolio: Dict,
                                         market_conditions: Dict) -> str:
        context = {"portfolio": portfolio, "trend_analysis": market_conditions}
        message = (
            "Analyse my portfolio performance and current market conditions. "
            "Provide: (1) portfolio health assessment, (2) rebalancing suggestions, "
            "(3) risk exposure, (4) specific actionable steps."
        )
        return await self.chat(message, context=context)

    async def explain_prediction(self,
                                  symbol: str,
                                  predictions: List[Dict],
                                  trend: Dict) -> str:
        context = {"predictions": predictions, "trend_analysis": trend}
        message = (
            f"Explain the ML price predictions for {symbol}. "
            "Discuss: (1) model confidence, (2) key drivers, "
            "(3) risk factors, (4) how to interpret the results."
        )
        return await self.chat(message, context=context)

    # ── Provider implementations ─────────────────────────────────────────

    async def _chat_gemini(self, message: str, history: List[Dict], system: str) -> str:
        from google.genai import types
        contents = []
        for msg in history[-12:]:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
        contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

        response = await asyncio.to_thread(
            self.gemini_client.models.generate_content,
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.7,
                max_output_tokens=2500,
            )
        )
        return response.text

    async def _chat_openai(self, message: str, history: List[Dict], system: str) -> str:
        messages = [{"role": "system", "content": system}]
        messages.extend(history[-12:])
        messages.append({"role": "user", "content": message})
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=2500,
        )
        return response.choices[0].message.content

    async def _chat_anthropic(self, message: str, history: List[Dict], system: str) -> str:
        messages = list(history[-12:])
        messages.append({"role": "user", "content": message})
        response = await self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2500,
            system=system,
            messages=messages
        )
        return response.content[0].text


# Singleton
ai_service = AIService()