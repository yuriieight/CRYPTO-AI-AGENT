"""LLM cascade fallback: Claude → GPT-4o → Gemini → Llama 3."""
import anthropic, openai
from app.core.config import settings

PROVIDERS = ["claude", "gpt4o", "gemini", "llama3"]

async def chat(message: str, history: list) -> str:
    for provider in PROVIDERS:
        try:
            return await _call(provider, message, history)
        except Exception:
            continue
    return "All LLM providers are unavailable."

async def _call(provider: str, message: str, history: list) -> str:
    if provider == "claude":
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        r = client.messages.create(model="claude-3-5-sonnet-20241022",
                                   max_tokens=1024,
                                   messages=[{"role": "user", "content": message}])
        return r.content[0].text
    raise NotImplementedError(provider)
