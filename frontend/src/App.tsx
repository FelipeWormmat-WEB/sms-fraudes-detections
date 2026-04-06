import { useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import Dashboard from './components/Dashboard';
import MessageForm from './components/MessageForm';
import { clearApiKey, setApiKey } from './services/auth';
import type { SMSLog } from './types';

export default function App() {
  const [logs, setLogs] = useState<SMSLog[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [apiKeyInput, setApiKeyInput] = useState<string>('');

  const fetchLogs = async () => {
    try {
      const response = await axios.get<SMSLog[]>('/logs');
      setLogs(response.data);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        toast.error(error.response?.data?.detail ?? 'Failed to fetch logs');
      } else {
        toast.error('Unexpected error while fetching logs');
      }
    }
  };

  const handleSubmit = async (message: string) => {
    setIsLoading(true);
    try {
      const response = await axios.post('/analyze', { message });
      toast.success(
        `Classified as: ${response.data.prediction} (confidence: ${response.data.confidence.toFixed(2)})`
      );
      await fetchLogs();
    } catch (error) {
      if (axios.isAxiosError(error)) {
        toast.error(`Classification failed: ${error.response?.data?.detail ?? error.message}`);
      } else {
        toast.error('Unexpected error while classifying message');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveApiKey = () => {
    const value = apiKeyInput.trim();
    if (!value) {
      clearApiKey();
      toast.info('API key removed');
      fetchLogs();
      return;
    }
    setApiKey(value);
    toast.success('API key loaded for this session');
    fetchLogs();
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="mb-8 text-center text-3xl font-bold text-indigo-700">SMS Fraud Detection Dashboard</h1>

      <div className="mb-6 rounded-lg bg-white p-4 shadow-md">
        <label htmlFor="api-key" className="mb-2 block text-sm font-medium text-gray-700">
          API Key
        </label>
        <p className="mb-2 text-xs text-gray-500">
          A chave fica apenas na mem&oacute;ria desta sess&atilde;o e n&atilde;o &eacute; persistida no navegador.
        </p>
        <div className="flex gap-2">
          <input
            id="api-key"
            type="password"
            value={apiKeyInput}
            onChange={(event) => setApiKeyInput(event.target.value)}
            placeholder="sms_xxx"
            className="w-full rounded-md border border-gray-300 px-3 py-2"
          />
          <button
            type="button"
            onClick={handleSaveApiKey}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Save
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
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
