import { useEffect, useState } from 'react';
import axios from 'axios';
import type { Metrics } from '../types';

interface MetricsCardProps {
  refreshKey: number;
}

export default function MetricsCard({ refreshKey }: MetricsCardProps) {
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await axios.get<Metrics>('/metrics');
        setMetrics(response.data);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      }
    };
    fetchMetrics();
  }, [refreshKey]);

  if (!metrics) {
    return <div>Loading metrics...</div>;
  }

  return (
    <div className="rounded-lg bg-white p-6 shadow-md">
      <h3 className="mb-4 text-lg font-medium text-gray-700">Performance Metrics</h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-500">Accuracy</p>
          <p className="text-2xl font-bold text-blue-600">{metrics.accuracy.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Precision</p>
          <p className="text-2xl font-bold text-blue-600">{metrics.precision.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Recall</p>
          <p className="text-2xl font-bold text-blue-600">{metrics.recall.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">F1-score</p>
          <p className="text-2xl font-bold text-blue-600">{metrics.f1_score.toFixed(2)}</p>
        </div>
      </div>
      <div className="mt-4 text-sm text-gray-500">
        <p>Labeled samples: {metrics.test_size}</p>
        <p>Total messages: {metrics.total_messages ?? 0}</p>
      </div>
      {metrics.message && <p className="mt-2 text-xs text-gray-500">{metrics.message}</p>}
    </div>
  );
}
