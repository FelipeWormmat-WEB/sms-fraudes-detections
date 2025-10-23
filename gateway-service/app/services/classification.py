import os
import httpx
import time
import logging
import pickle
from pathlib import Path
import pickle
from scipy.sparse import hstack
from pathlib import Path
from ml_pipeline.preprocess import TextPreprocessor
from ml_pipeline.features import FeatureExtractor
import numpy as np

logger = logging.getLogger("gateway.classification")

# Configuração do logger
if not logger.handlers:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

CLASSIFICATION_URL = os.getenv("CLASSIFICATION_URL", "http://classification-service:8080")

_MODEL = None
_VECTORIZER = None
_SKLEARN_AVAILABLE = False
_FEATURE_NAMES = None
_PREPROCESSOR = TextPreprocessor()
_EXTRACTOR = FeatureExtractor()

def _load_local_model():
    global _MODEL, _VECTORIZER, _FEATURE_NAMES
    base_dir = Path(__file__).parent.parent / "models"  # gateway-service/models
    try:
        with open(base_dir / "best_classifier.pkl", "rb") as f:
            _MODEL = pickle.load(f)
        with open(base_dir / "tfidf_vectorizer.pkl", "rb") as f:
            _VECTORIZER = pickle.load(f)
        with open(base_dir / "feature_names.pkl", "rb") as f:
            _FEATURE_NAMES = pickle.load(f)
        print("✅ Novo modelo avançado carregado!")
    except Exception as e:
        print(f"❌ Erro no load: {e}")

# Carregar o modelo local ao importar este módulo
_load_local_model()

async def _classify_via_http(message: str) -> dict:
    url = f"{CLASSIFICATION_URL}/classify"
    start = time.perf_counter()
    async with httpx.AsyncClient() as client:
        logger.info("HTTP classify -> POST %s len=%d", url, len(message or ""))
        response = await client.post(
            url,
            json={"message": message},
            timeout=30.0,
        )
        elapsed = (time.perf_counter() - start) * 1000
        logger.info("HTTP classify <- %s status=%d elapsed=%.1fms", url, response.status_code, elapsed)
        response.raise_for_status()
        return response.json()


async def classify_message(message: str) -> dict:
    """Classifica a mensagem.
    Preferência: modelo local treinado nos datasets (se disponível),
    senão fallback para o classification-service via HTTP.
    """
    try:
        if _MODEL is not None and _VECTORIZER is not None and _SKLEARN_AVAILABLE:
            import numpy as np
            logger.info("Classificando via modelo local (sklearn)")
            X = _VECTORIZER.transform([message])
            pred = _MODEL.predict(X)[0]
            try:
                proba = _MODEL.predict_proba(X)
                confidence = float(np.max(proba))
            except Exception:
                confidence = 0.95
            logger.info("Resultado local prediction=%s confidence=%.3f", str(pred), confidence)
            return {
                "message": message,
                "prediction": str(pred),
                "confidence": confidence,
                "source": "local-model",
            }
        else:
            logger.info("Classificando via serviço remoto: %s", CLASSIFICATION_URL)
            data = await _classify_via_http(message)
            logger.info(
                "Resultado remoto prediction=%s confidence=%.3f",
                data.get("prediction", "unknown"),
                data.get("confidence", 0.95),
            )
            return {
                "message": data.get("message", message),
                "prediction": data.get("prediction", "unknown"),
                "confidence": data.get("confidence", 0.95),
                "source": "remote-service",
            }
    except Exception as e:
        logger.exception("Erro ao classificar, tentando fallback remoto: %s", e)
        try:
            data = await _classify_via_http(message)
            logger.info(
                "Fallback remoto ok prediction=%s confidence=%.3f",
                data.get("prediction", "unknown"),
                data.get("confidence", 0.95),
            )
            return {
                "message": data.get("message", message),
                "prediction": data.get("prediction", "unknown"),
                "confidence": data.get("confidence", 0.95),
                "source": "remote-service",
            }
        except Exception as e2:
            logger.exception("Fallback remoto falhou: %s", e2)
            return {
                "message": message,
                "prediction": "unknown",
                "confidence": 0.0,
                "error": str(e),
            }
        
# URL do LLM local
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm-service:8001/analyze")

async def analyze_with_local_llm(message: str):
    """Chama o serviço LLM local"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(LLM_SERVICE_URL, json={"message": message}, timeout=30)
            data = resp.json()
            result = data.get("llm_result", None)
            if result is None:
                logger.warning("LLM local retornou vazio")
                return "[LLM failed]"
            return result
    except Exception as e:
        logger.exception("Erro ao chamar LLM local: %s", e)
        return "[LLM failed]"

async def hybrid_classification(message: str, prob: float, pred: str):
    """Se a confiança do modelo local for baixa, chama o LLM"""
    if prob < 0.7:
        llm_result = await analyze_with_local_llm(message)
        return {"prediction": llm_result, "source": "llm"}
    return {"prediction": pred, "source": "naive_bayes"}

