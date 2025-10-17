import os
import openai
import logging

logger = logging.getLogger("llm_service")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# Configura a chave da OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_response(prompt: str, max_tokens: int = 256):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente útil."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Erro ao chamar a API da OpenAI: {e}")
        return f"Erro ao gerar resposta: {e}"
