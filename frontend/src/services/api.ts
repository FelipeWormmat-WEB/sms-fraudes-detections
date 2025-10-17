export async function analyzeLLM(message: string) {
  const resp = await fetch("http://localhost:8000/analyze_llm", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ message })
  });
  return await resp.json();
}
