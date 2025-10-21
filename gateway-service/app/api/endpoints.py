from sqlalchemy.future import select
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import MessageInput, SMSLog
from app.services.classification import classify_message, hybrid_classification
from app.api.schemas import SMSLogResponse, SMSRequest, SMSResponse
import logging
import os
from app.services.classification import classify_message
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score



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

@router.get("/logs", response_model=List[SMSLogResponse])
async def get_logs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SMSLog).order_by(SMSLog.created_at.desc()))
    logs = result.scalars().all()
    return logs

@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SMSLog))
    logs = result.scalars().all()

    if not logs:
        return {
            "accuracy": 0,
            "precision": 0,
            "recall": 0,
            "f1_score": 0,
            "message": "Não há logs suficientes para calcular métricas"
        }

    # Converter logs para DataFrame
    df = pd.DataFrame([{"message": log.message, "prediction": log.prediction} for log in logs])

    # Verificar se há dados suficientes
    if len(df) < 2:
        return {
            "accuracy": 0,
            "precision": 0,
            "recall": 0,
            "f1_score": 0,
            "message": "Não há dados suficientes para calcular métricas"
        }

    # Embaralhar os dados para garantir aleatoriedade
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    # Dividir dados em treinamento e teste
    X = df["message"]
    y = df["prediction"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Verificar se há dados suficientes nos conjuntos de treinamento e teste
    if len(X_test) == 0 or len(y_test) == 0:
        return {
            "accuracy": 0,
            "precision": 0,
            "recall": 0,
            "f1_score": 0,
            "message": "Não há dados suficientes nos conjuntos de teste para calcular métricas"
        }

    # Vetorizar os textos
    vectorizer = CountVectorizer(preprocessor=lambda text: text.lower())
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # Treinar o modelo
    model = MultinomialNB()
    model.fit(X_train_vec, y_train)

    # Fazer predições
    y_pred = model.predict(X_test_vec)

    # Calcular métricas
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, pos_label="spam", zero_division=0)
    recall = recall_score(y_test, y_pred, pos_label="spam", zero_division=0)
    f1 = f1_score(y_test, y_pred, pos_label="spam", zero_division=0)

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "test_size": len(X_test),
        "train_size": len(X_train)
    }
