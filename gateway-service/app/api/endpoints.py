from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import MessageInput, SMSLog
from app.services.classification import classify_message, hybrid_classification
from app.api.schemas import SMSRequest, SMSResponse
import logging
import os
from app.services.classification import classify_message


logger = logging.getLogger("gateway.api")
if not logger.handlers:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

router = APIRouter()

@router.post("/analyze", response_model=SMSResponse)
async def analyze_sms(request: SMSRequest, db: AsyncSession = Depends(get_db)):
    try:
        classification_data = await classify_message(request.message)
        prediction = classification_data.get("prediction", "unknown")
        confidence = classification_data.get("confidence", 0.0)

        # Salvar no banco
        sms_log = SMSLog(message=request.message, prediction=prediction, confidence=confidence)
        db.add(sms_log)
        await db.commit()

        return SMSResponse(
            message=request.message,
            prediction=prediction,
            confidence=confidence,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error in /analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/analyze_llm", response_model=SMSResponse)
async def analyze_message_llm(payload: MessageInput, db: AsyncSession = Depends(get_db)):
    try:
        # Primeiro, classifica via modelo local
        classification_data = await classify_message(payload.message)
        prediction = classification_data.get("prediction", "unknown")
        confidence = classification_data.get("confidence", 0.0)

        # Se confiança baixa, usa LLM local
        hybrid_result = await hybrid_classification(payload.message, confidence, prediction)
        final_pred = hybrid_result.get("prediction")
        source = hybrid_result.get("source")

        # Persiste no banco
        sms = SMSLog(message=payload.message, prediction=final_pred, confidence=confidence)
        db.add(sms)
        await db.commit()

        return SMSResponse(
            message=payload.message,
            prediction=final_pred,
            confidence=confidence,
            status="success",
        )

    except Exception as e:
        logger.exception("Erro em /analyze_llm: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze_hybrid")
async def analyze_message_hybrid(payload: MessageInput):
    """
    Endpoint para classificação híbrida:
    - Naive Bayes se confiável
    - LLM se confiança baixa
    """
    result = await hybrid_classification(payload.message)
    return {"message": payload.message, **result}

@router.get("/health")
async def health_check():
    return {"status": "healthy"}
