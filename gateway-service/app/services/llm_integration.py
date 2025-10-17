import os
import httpx
import logging
import asyncio

logger = logging.getLogger("gateway.llm")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

async def analyze_with_openai(message: str, max_retries: int = 5, delay: float = 2.0) -> str:
    """
    Chama a API OpenAI Chat Completions de forma segura.
    Faz retry automático em caso de erro 429 ou falhas temporárias.
    """
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": message}],
        "temperature": 0.7
    }

    attempt = 0
    while attempt < max_retries:
        attempt += 1
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(OPENAI_URL, headers=headers, json=payload)
                data = response.json()

                # Tratamento de status code
                if response.status_code == 200:
                    choices = data.get("choices")
                    if choices and len(choices) > 0:
                        content = choices[0]["message"]["content"]
                        return content
                    else:
                        logger.error("OpenAI API retornou sem 'choices': %s", data)
                        return "[LLM Error: no choices returned]"
                
                elif response.status_code == 429:
                    logger.warning("OpenAI 429 Too Many Requests, tentativa %d/%d", attempt, max_retries)
                    await asyncio.sleep(delay * attempt)  # backoff incremental
                    continue
                else:
                    logger.error("OpenAI API returned status %d: %s", response.status_code, data)
                    return f"[LLM Error {response.status_code}]"

        except httpx.RequestError as e:
            logger.exception("Erro de requisição para OpenAI (tentativa %d/%d): %s", attempt, max_retries, e)
            await asyncio.sleep(delay * attempt)
        except Exception as e:
            logger.exception("Erro inesperado no LLM (tentativa %d/%d): %s", attempt, max_retries, e)
            await asyncio.sleep(delay * attempt)

    logger.error("Todas as tentativas falharam para a mensagem: %s", message)
    return "[LLM Failed after retries]"

async def analyze_with_anthropic(message: str):
    """
    Usa o modelo Claude (Anthropic) para mesma tarefa.
    """
    headers = {"x-api-key": ANTHROPIC_API_KEY}
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 200,
        "messages": [
            {"role": "user", "content": f"Classifique como 'spam' ou 'ham' e explique:\n\n{message}"}
        ]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
        data = resp.json()
    
    return data["content"][0]["text"]
