import SMSLogChart from './SMSLogChart';
import type { SMSLog } from '../types';

interface DashboardProps {
  logs: SMSLog[];
}

export default function Dashboard({ logs }: DashboardProps) {
  const spamCount = logs.filter(log => log.prediction === 'spam').length;
  const hamCount = logs.filter(log => log.prediction === 'ham').length;
  const total = logs.length;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-medium text-gray-700">Total de Mensagens</h3>
          <p className="mt-2 text-3xl font-bold text-gray-900">{total}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-medium text-gray-700">Mensagens SPAM</h3>
          <p className="mt-2 text-3xl font-bold text-red-600">{spamCount}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-medium text-gray-700">Mensagens HAM</h3>
          <p className="mt-2 text-3xl font-bold text-green-600">{hamCount}</p>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-medium text-gray-700 mb-4">Gráfico de Classificações</h3>
        <SMSLogChart logs={logs} />
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-medium text-gray-700 mb-4">Últimas Mensagens</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Mensagem</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Classificação</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Confiança</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {logs.slice(0, 5).map((log, index) => (
                <tr key={index} className={log.prediction === 'spam' ? 'bg-red-50' : 'bg-green-50'}>
                  <td className="px-6 py-4 whitespace-normal max-w-xs break-words">{log.message}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${log.prediction === 'spam' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                      {log.prediction}
                    </span>
                  </td>
                  <td className="px-6 py-4">{log.confidence.toFixed(2)}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{new Date(log.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
