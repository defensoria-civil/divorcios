import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp, Users, FileText, Clock } from 'lucide-react';
import { useAuthStore } from '@/features/auth/store/authStore';
import { Card } from '@/shared/components/ui/Card';
import { Button } from '@/shared/components/ui/Button';
import { metricsApi } from '../api/metrics.api';
import NumberTicker from '@/shared/components/magicui/NumberTicker';
import BlurFade from '@/shared/components/magicui/BlurFade';
import BorderBeam from '@/shared/components/magicui/BorderBeam';
import DotPattern from '@/shared/components/magicui/DotPattern';

export function Dashboard() {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ['metrics', 'summary'],
    queryFn: metricsApi.getSummary,
    refetchInterval: 30000, // Auto-refresh cada 30 segundos
  });

  const { data: byStatus, isLoading: loadingStatus } = useQuery({
    queryKey: ['metrics', 'by_status'],
    queryFn: metricsApi.getByStatus,
    refetchInterval: 30000,
  });

  const { data: timeline, isLoading: loadingTimeline } = useQuery({
    queryKey: ['metrics', 'timeline'],
    queryFn: () => metricsApi.getTimeline(30),
    refetchInterval: 30000,
  });

  const COLORS = {
    new: '#94a3b8',
    datos_completos: '#3b82f6',
    documentacion_completa: '#10b981',
  };

  const STATUS_LABELS: Record<string, string> = {
    'new': 'Nuevos',
    'datos_completos': 'Datos Completos',
    'documentacion_completa': 'Documentación Completa',
  };

  const isLoading = loadingSummary || loadingStatus || loadingTimeline;

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 relative">
      {/* Dot Pattern Background */}
      <DotPattern className="opacity-40" />
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Dashboard</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Bienvenido, {user?.name}
          </p>
        </div>
        <Button onClick={() => navigate('/cases')}>
          Ver Todos los Casos
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <BlurFade delay={0.1}>
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Casos Totales</p>
                <div className="mt-2">
                  <NumberTicker 
                    value={summary?.total_cases || 0} 
                    className="text-3xl font-bold text-gray-900 dark:text-gray-100"
                  />
                </div>
              </div>
              <div className="p-3 bg-blue-100 dark:bg-blue-900/50 rounded-lg">
                <FileText className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-4">
              {summary?.recent_cases_7d || 0} nuevos esta semana
            </p>
          </Card>
        </BlurFade>

        <BlurFade delay={0.2}>
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Últimos 7 Días</p>
                <div className="mt-2">
                  <NumberTicker 
                    value={summary?.recent_cases_7d || 0}
                    className="text-3xl font-bold text-gray-900 dark:text-gray-100"
                  />
                </div>
              </div>
              <div className="p-3 bg-green-100 dark:bg-green-900/50 rounded-lg">
                <TrendingUp className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-4">
              Casos nuevos esta semana
            </p>
          </Card>
        </BlurFade>

        <BlurFade delay={0.3}>
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Últimos 30 Días</p>
                <div className="mt-2">
                  <NumberTicker 
                    value={summary?.recent_cases_30d || 0}
                    className="text-3xl font-bold text-gray-900 dark:text-gray-100"
                  />
                </div>
              </div>
              <div className="p-3 bg-purple-100 dark:bg-purple-900/50 rounded-lg">
                <Clock className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-4">
              Casos este mes
            </p>
          </Card>
        </BlurFade>

        <BlurFade delay={0.4}>
          <Card className="p-6 relative overflow-hidden">
            <BorderBeam 
              size={250} 
              duration={12}
              colorFrom="#10b981"
              colorTo="#34d399"
            />
            <div className="flex items-center justify-between relative z-10">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Completados</p>
                <div className="mt-2">
                  <NumberTicker 
                    value={summary?.by_status?.documentacion_completa || 0}
                    className="text-3xl font-bold text-gray-900 dark:text-gray-100"
                  />
                </div>
              </div>
              <div className="p-3 bg-green-100 dark:bg-green-900/50 rounded-lg">
                <Users className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-4 relative z-10">
              Documentación completa
            </p>
          </Card>
        </BlurFade>
      </div>

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Status Distribution */}
        <BlurFade delay={0.5}>
          <Card className="p-6">
          <h2 className="text-xl font-semibold mb-6 text-gray-900 dark:text-gray-100">Distribución por Estado</h2>
          {byStatus && byStatus.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={byStatus}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ status, count, percent }) => 
                    `${STATUS_LABELS[status] || status}: ${count} (${(percent * 100).toFixed(0)}%)`
                  }
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {byStatus.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[entry.status as keyof typeof COLORS] || '#94a3b8'} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value, _name, props) => [
                    value, 
                    STATUS_LABELS[props.payload.status] || props.payload.status
                  ]}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
              No hay datos disponibles
            </div>
          )}
          </Card>
        </BlurFade>

        {/* Timeline */}
        <BlurFade delay={0.6}>
          <Card className="p-6">
          <h2 className="text-xl font-semibold mb-6 text-gray-900 dark:text-gray-100">Casos Creados (Últimos 30 Días)</h2>
          {timeline && timeline.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={timeline}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(date) => {
                    const d = new Date(date);
                    return `${d.getDate()}/${d.getMonth() + 1}`;
                  }}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(date) => {
                    const d = new Date(date);
                    return d.toLocaleDateString('es-ES', { day: '2-digit', month: 'long' });
                  }}
                  formatter={(value) => [value, 'Casos']}
                />
                <Legend formatter={() => 'Casos nuevos'} />
                <Line 
                  type="monotone" 
                  dataKey="count" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6' }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
              No hay datos disponibles
            </div>
          )}
          </Card>
        </BlurFade>
      </div>

      {/* Quick Actions */}
      <BlurFade delay={0.7}>
        <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">Acciones Rápidas</h2>
        <div className="flex flex-wrap gap-3">
          <Button onClick={() => navigate('/cases')}>Ver Todos los Casos</Button>
          <Button variant="outline" onClick={() => navigate('/cases?status=new')}>
            Ver Casos Nuevos
          </Button>
          <Button variant="outline" onClick={() => navigate('/cases?status=documentacion_completa')}>
            Ver Casos Completados
          </Button>
        </div>
        </Card>
      </BlurFade>
    </div>
  );
}
