import { useState } from "react";
import { analyzeLLM } from "../services/api";

export default function LLMAnalyzer() {
  const [text, setText] = useState("");
  const [result, setResult] = useState("");

  const handleAnalyze = async () => {
    const data = await analyzeLLM(text);
    setResult(data.llm_analysis);
  };

  return (
    <div className="p-4 max-w-lg mx-auto">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Cole a mensagem aqui..."
        className="w-full h-32 border rounded p-2"
      />
      <button
        onClick={handleAnalyze}
        className="bg-blue-600 text-white px-4 py-2 rounded mt-2"
      >
        Analisar com LLM
      </button>

      {result && (
        <div className="mt-4 p-3 border rounded bg-gray-50">
          <strong>Resultado:</strong>
          <p>{result}</p>
        </div>
      )}
    </div>
  );
}
