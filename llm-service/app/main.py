from fastapi import FastAPI
from app.llm_model import generate_response
from pydantic import BaseModel
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_service")

app = FastAPI(title="LLM Service", version="1.0.0")

class AnalysisRequest(BaseModel):
    text: str
    max_length: int = 150

class AnalysisResponse(BaseModel):
    analysis: str
    status: str

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/analyze")
async def analyze_text(request: AnalysisRequest):
    try:
        logger.info(f"Analisando texto: {request.text[:100]}...")
        
        analysis = generate_response(request.text, request.max_length)
        
        return AnalysisResponse(
            analysis=analysis,
            status="success"
        )
    except Exception as e:
        logger.error(f"Erro na análise: {e}")
        return AnalysisResponse(
            analysis="Erro no processamento",
            status="error"
        )

@app.get("/")
async def root():
    return {"message": "LLM Service está funcionando!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)