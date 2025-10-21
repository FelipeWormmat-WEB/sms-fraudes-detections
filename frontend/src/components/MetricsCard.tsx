import { useState, useEffect } from 'react';
import axios from 'axios';

interface Metrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
}

export default function MetricsCard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await axios.get('/api/metrics');
        setMetrics(response.data);
      } catch (error) {
        console.error('Erro ao buscar métricas:', error);
      }
    };
    fetchMetrics();
  }, []);

  if (!metrics) {
    return <div>Carregando métricas...</div>;
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h3 className="text-lg font-medium text-gray-700 mb-4">Métricas de Desempenho</h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-500">Acurácia</p>
          <p className="text-2xl font-bold text-blue-600">{metrics.accuracy.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Precisão</p>
          <p className="text-2xl font-bold text-blue-600">{metrics.precision.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Recall</p>
          <p className="text-2xl font-bold text-blue-600">{metrics.recall.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">F1-Score</p>
          <p className="text-2xl font-bold text-blue-600">{metrics.f1_score.toFixed(2)}</p>
        </div>
      </div>
    </div>
  );
}
