from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.services.ai_service import ai_service
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = None
    context: Optional[Dict] = None
    stream: bool = False


class ChatResponse(BaseModel):
    response: str
    conversation_history: List[ChatMessage]


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with AI assistant
    """
    try:
        # Convert conversation history to dict format
        history = None
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

        # Get AI response
        response = await ai_service.chat(
            message=request.message,
            conversation_history=history,
            context=request.context
        )

        # Build updated conversation history
        updated_history = history or []
        updated_history.append({"role": "user", "content": request.message})
        updated_history.append({"role": "assistant", "content": response})

        return ChatResponse(
            response=response,
            conversation_history=[
                ChatMessage(role=msg["role"], content=msg["content"])
                for msg in updated_history
            ]
        )

    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response from AI assistant
    """
    try:
        # Convert conversation history to dict format
        history = None
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

        async def generate():
            try:
                async for chunk in ai_service.stream_chat(
                        message=request.message,
                        conversation_history=history,
                        context=request.context
                ):
                    yield f"data: {json.dumps({'content': chunk})}\n\n"

                yield f"data: {json.dumps({'done': True})}\n\n"

            except Exception as e:
                logger.error(f"Error in streaming: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )

    except Exception as e:
        logger.error(f"Error in chat stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sentiment/{symbol}")
async def analyze_sentiment(symbol: str, market_data: Dict):
    """
    Analyze market sentiment for a cryptocurrency
    """
    try:
        sentiment = await ai_service.analyze_market_sentiment(
            symbol=symbol,
            market_data=market_data
        )
        return sentiment

    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insights")
async def generate_insights(portfolio: Dict, market_conditions: Dict):
    """
    Generate personalized trading insights
    """
    try:
        insights = await ai_service.generate_trading_insights(
            portfolio=portfolio,
            market_conditions=market_conditions
        )
        return {"insights": insights}

    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))