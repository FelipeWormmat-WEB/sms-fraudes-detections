import { getApiKey } from "./auth";

export async function analyzeLLM(message: string) {
  const apiKey = getApiKey();
  const headers: Record<string, string> = {"Content-Type": "application/json"};
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }

  const resp = await fetch("/api/analyze_llm", {
    method: "POST",
    headers,
    body: JSON.stringify({ message })
  });
  return await resp.json();
}
