import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import type { SMSLog } from '../types';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface SMSLogChartProps {
  logs: SMSLog[];
}

export default function SMSLogChart({ logs }: SMSLogChartProps) {
  const spamCount = logs.filter(log => log.prediction === 'spam').length;
  const hamCount = logs.filter(log => log.prediction === 'ham').length;

  const data = {
    labels: ['SPAM', 'HAM'],
    datasets: [
      {
        label: 'Quantidade de Mensagens',
        data: [spamCount, hamCount],
        backgroundColor: ['rgba(255, 99, 132, 0.7)', 'rgba(75, 192, 192, 0.7)'],
        borderColor: ['rgba(255, 99, 132, 1)', 'rgba(75, 192, 192, 1)'],
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Distribuição de Classificações',
      },
    },
  };

  return <Bar data={data} options={options} />;
}
