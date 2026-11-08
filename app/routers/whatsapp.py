from fastapi import APIRouter, Depends, Form, Response
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.whatsapp_service import WhatsAppBotService

router = APIRouter(prefix="/api/v1/whatsapp", tags=["WhatsApp Bot Webhook & Simulator"])

class WhatsAppSimulateRequest(BaseModel):
    user_phone: str = "+919876543210"
    message_text: Optional[str] = "Nehru Place to Kashmere Gate"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class WhatsAppSimulateResponse(BaseModel):
    user_phone: str
    incoming_query: Optional[str]
    bot_reply: str

@router.post("/simulate", response_model=WhatsAppSimulateResponse)
async def simulate_whatsapp_chat(
    req: WhatsAppSimulateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Test and simulate WhatsApp interactions without needing a live Twilio account.
    """
    reply = await WhatsAppBotService.handle_incoming_message(
        session=db,
        user_phone=req.user_phone,
        message_text=req.message_text,
        latitude=req.latitude,
        longitude=req.longitude
    )
    return WhatsAppSimulateResponse(
        user_phone=req.user_phone,
        incoming_query=req.message_text or f"GPS ({req.latitude}, {req.longitude})",
        bot_reply=reply
    )

@router.post("/webhook")
async def twilio_whatsapp_webhook(
    From: str = Form(...),
    Body: Optional[str] = Form(None),
    Latitude: Optional[float] = Form(None),
    Longitude: Optional[float] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Standard Twilio WhatsApp Webhook endpoint.
    Point your Twilio Sandbox WhatsApp Incoming Webhook URL here!
    """
    bot_reply = await WhatsAppBotService.handle_incoming_message(
        session=db,
        user_phone=From,
        message_text=Body,
        latitude=Latitude,
        longitude=Longitude
    )

    # Return standard TwiML XML
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{bot_reply}</Message>
</Response>"""
    return Response(content=twiml_response, media_type="application/xml")
