import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import MessageForm from './components/MessageForm';
import Dashboard from './components/Dashboard';
import type { SMSLog } from './types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function App() {
  const [logs, setLogs] = useState<SMSLog[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchLogs = async () => {
    try {
      const response = await axios.get<SMSLog[]>(`${API_URL}/api/logs`);
      setLogs(response.data);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        toast.error(`Erro ao buscar logs: ${error.message}`);
      } else {
        toast.error(`Erro inesperado ao buscar logs`);
      }
    }
  };

  const handleSubmit = async (message: string) => {
    setIsLoading(true);
    try {
      const response = await axios.post('/api/analyze', { message });
      toast.success(`Mensagem classificada como: ${response.data.prediction} (confiança: ${response.data.confidence.toFixed(2)})`);
      await fetchLogs();
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error('Erro ao classificar mensagem:', error.response?.data || error.message);
        toast.error(`Erro ao classificar mensagem: ${error.response?.data?.detail || error.message}`);
      } else {
        toast.error(`Erro inesperado ao classificar mensagem`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-bold text-center text-indigo-700 mb-8">SMS Fraud Detection Dashboard</h1>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <MessageForm onSubmit={handleSubmit} isLoading={isLoading} />
        </div>
        <div className="lg:col-span-2">
          <Dashboard logs={logs} />
        </div>
      </div>
    </div>
  );
}
