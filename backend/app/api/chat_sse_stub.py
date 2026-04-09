"""SSE streaming endpoint for AI chat."""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.ai_stub import _call
import asyncio, json

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

@router.post("/chat/stream")
async def chat_stream(body: dict):
    async def event_gen():
        chunk = await _call("claude", body.get("message", ""), [])
        for word in chunk.split():
            yield f"data: {json.dumps({'token': word + ' '})}\n\n"
            await asyncio.sleep(0.03)
        yield "data: [DONE]\n\n"
    return StreamingResponse(event_gen(), media_type="text/event-stream")
