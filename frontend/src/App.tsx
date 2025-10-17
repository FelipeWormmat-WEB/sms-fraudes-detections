import { useState } from "react";
import "./styles/theme.css";

function App() {
  console.log('[frontend] App mounted')
  const [query, setQuery] = useState("");

  const handleSearch = async () => {
    if (!query.trim()) return;

      try {
        console.log('[frontend] calling gateway /analyze len=%d', query.length)
        const response = await fetch("http://localhost:8000/analyze", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ message: query }),
        });
        console.log('[frontend] /analyze status=%d', response.status)

        if (!response.ok) throw new Error("Erro ao classificar a mensagem");

        const data = await response.json();
        console.log('[frontend] /analyze response', data)
        alert(`Mensagem: ${data.message}\nPredição: ${data.prediction}`);
      } catch (error: any) {
        console.error('[frontend] /analyze error', error);
        alert("Erro ao conectar com o backend: " + error.message);
      }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 font-sans">
      <h1 className="text-4xl font-bold mb-8">Classificador</h1>
      <div className="relative w-full max-w-2xl">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSearch();
          }}
          placeholder="Pesquise no Google ou digite uma URL"
          className="pesquisar-input"
        />
      </div>
      <div className="flex gap-4 mt-6">
        <button onClick={handleSearch} className="search-button-primary">
          Pesquisa Google
        </button>
        <button
          onClick={() => alert("Estou com sorte!")}
          className="estou-com-sorte"
        >
          Estou com sorte
        </button>
      </div>
    </div>
  );
}

export default App;