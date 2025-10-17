import asyncio
from app.services.llm_integration import analyze_with_openai

messages = [
    "You have won a free trip to Bahamas! Click here to claim.",
    "Oi, posso te ligar mais tarde?",
    "Atualize sua conta bancária clicando neste link urgente!"
]

async def main():
    for m in messages:
        result = await analyze_with_openai(m)
        print(f"\nMensagem: {m}\n→ Resultado: {result}")

asyncio.run(main())