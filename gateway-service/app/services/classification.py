import logging
import os
import pickle
import time
import unicodedata
from pathlib import Path
from typing import Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger("gateway.classification")
if not logger.handlers:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

CLASSIFICATION_URL = settings.CLASSIFICATION_URL
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm-service:8001/analyze")

_MODEL = None
_VECTORIZER = None
_SKLEARN_AVAILABLE = False


def _load_local_model() -> None:
    global _MODEL, _VECTORIZER, _SKLEARN_AVAILABLE
    try:
        base_dir = Path(__file__).resolve().parents[2]
        model_path = base_dir / "models" / "sms_classifier.pkl"
        vectorizer_path = base_dir / "models" / "vectorizer.pkl"
        if model_path.exists() and vectorizer_path.exists():
            with open(model_path, "rb") as model_file:
                _MODEL = pickle.load(model_file)
            with open(vectorizer_path, "rb") as vectorizer_file:
                _VECTORIZER = pickle.load(vectorizer_file)
            _SKLEARN_AVAILABLE = True
            logger.info("Local model loaded")
    except Exception as exc:
        logger.exception("Failed to load local model: %s", exc)


_load_local_model()


def normalize_prediction(prediction: Any) -> str:
    if prediction is None:
        return "unknown"

    raw = str(prediction)
    normalized = (
        unicodedata.normalize("NFKD", raw)
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
        .lower()
    )

    spam_tokens = ("spam", "fraude", "fraud", "scam", "phishing")
    ham_tokens = ("ham", "legitimo", "legit", "normal", "seguro")

    if any(token in normalized for token in spam_tokens):
        return "spam"
    if any(token in normalized for token in ham_tokens):
        return "ham"
    return "unknown"


def _safe_confidence(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


async def _classify_via_http(message: str) -> dict:
    url = f"{CLASSIFICATION_URL}/classify"
    start = time.perf_counter()
    headers = {"X-Internal-Service-Token": settings.INTERNAL_SERVICE_TOKEN}
    async with httpx.AsyncClient() as client:
        logger.info("HTTP classify -> %s len=%d", url, len(message or ""))
        response = await client.post(url, json={"message": message}, headers=headers, timeout=30.0)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info("HTTP classify <- %s status=%d elapsed=%.1fms", url, response.status_code, elapsed_ms)
        response.raise_for_status()
        return response.json()


async def classify_message(message: str) -> dict:
    """Classifies a message using local model first, then remote fallback."""
    try:
        if _MODEL is not None and _VECTORIZER is not None and _SKLEARN_AVAILABLE:
            import numpy as np

            logger.info("Classifying with local model")
            features = _VECTORIZER.transform([message])
            prediction = normalize_prediction(_MODEL.predict(features)[0])
            try:
                confidence = float(np.max(_MODEL.predict_proba(features)))
            except Exception:
                confidence = 0.95

            return {
                "message": message,
                "prediction": prediction,
                "confidence": confidence,
                "source": "local-model",
            }

        logger.info("Classifying with remote service")
        data = await _classify_via_http(message)
        return {
            "message": data.get("message", message),
            "prediction": normalize_prediction(data.get("prediction")),
            "confidence": _safe_confidence(data.get("confidence"), 0.95),
            "source": "remote-service",
        }
    except Exception as exc:
        logger.exception("Primary classification failed, trying remote fallback: %s", exc)
        try:
            data = await _classify_via_http(message)
            return {
                "message": data.get("message", message),
                "prediction": normalize_prediction(data.get("prediction")),
                "confidence": _safe_confidence(data.get("confidence"), 0.95),
                "source": "remote-service",
            }
        except Exception as fallback_exc:
            logger.exception("Remote fallback failed: %s", fallback_exc)
            return {
                "message": message,
                "prediction": "unknown",
                "confidence": 0.0,
                "source": "error",
                "error": str(exc),
            }


async def analyze_with_local_llm(message: str) -> str:
    try:
        headers = {"X-Internal-Service-Token": settings.INTERNAL_SERVICE_TOKEN}
        async with httpx.AsyncClient() as client:
            response = await client.post(LLM_SERVICE_URL, json={"text": message}, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

        llm_output = data.get("analysis") or data.get("llm_result") or data.get("prediction")
        normalized = normalize_prediction(llm_output)
        if normalized == "unknown":
            logger.warning("Ambiguous LLM output: %s", str(llm_output)[:120])
        return normalized
    except Exception as exc:
        logger.exception("LLM analysis failed: %s", exc)
        return "unknown"


async def hybrid_classification(
    message: str,
    prob: Optional[float] = None,
    pred: Optional[str] = None,
    threshold: Optional[float] = None,
) -> dict:
    """Uses LLM only when base classifier confidence is below threshold."""
    if prob is None or pred is None:
        base = await classify_message(message)
        pred = base.get("prediction", "unknown")
        prob = _safe_confidence(base.get("confidence"), 0.0)
        base_source = base.get("source", "unknown")
    else:
        pred = normalize_prediction(pred)
        prob = _safe_confidence(prob, 0.0)
        base_source = "provided"

    effective_threshold = threshold if threshold is not None else settings.HYBRID_LLM_THRESHOLD
    if prob < effective_threshold:
        llm_prediction = await analyze_with_local_llm(message)
        if llm_prediction != "unknown":
            return {
                "prediction": llm_prediction,
                "source": "llm",
                "base_prediction": pred,
                "base_confidence": prob,
            }
        return {
            "prediction": pred,
            "source": f"{base_source}-fallback",
            "base_prediction": pred,
            "base_confidence": prob,
        }

    return {
        "prediction": pred,
        "source": base_source,
        "base_prediction": pred,
        "base_confidence": prob,
    }
