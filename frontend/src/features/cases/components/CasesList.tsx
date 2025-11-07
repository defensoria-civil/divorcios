import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import toast from 'react-hot-toast';
import { Search, Download, Eye, ChevronLeft, ChevronRight } from 'lucide-react';
import { casesApi } from '../api/cases.api';
import { CaseFilters } from '../types/case.types';
import { Button } from '@/shared/components/ui/Button';
import { Input } from '@/shared/components/ui/Input';
import { Card } from '@/shared/components/ui/Card';

export function CasesList() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<CaseFilters>({
    page: 1,
    pageSize: 50,
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['cases', filters],
    queryFn: () => casesApi.getAll(filters),
  });

  const handleSearch = (search: string) => {
    setFilters({ ...filters, search, page: 1 });
  };

  const handleStatusFilter = (status: string) => {
    setFilters({ 
      ...filters, 
      status: status === filters.status ? undefined : status,
      page: 1 
    });
  };

  const handleTypeFilter = (type: string) => {
    setFilters({ 
      ...filters, 
      type: type === filters.type ? undefined : type,
      page: 1 
    });
  };

  const handlePageChange = (newPage: number) => {
    setFilters({ ...filters, page: newPage });
  };

  const handleDownloadPDF = async (caseId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const toastId = toast.loading('Generando PDF...');
    try {
      const blob = await casesApi.downloadPetition(caseId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `demanda-divorcio-${caseId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('PDF descargado exitosamente', { id: toastId });
    } catch (error) {
      console.error('Error downloading PDF:', error);
      toast.error('Error al descargar el PDF', { id: toastId });
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'new':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
      case 'datos_completos':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200';
      case 'documentacion_completa':
        return 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      'new': 'Nuevo',
      'datos_completos': 'Datos Completos',
      'documentacion_completa': 'Documentación Completa',
    };
    return labels[status] || status;
  };

  if (error) {
    return (
      <div className="p-6">
        <Card className="p-6">
          <p className="text-red-600 dark:text-red-400">Error cargando casos: {(error as Error).message}</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Casos de Divorcio</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Gestión de casos de trámites de divorcio
        </p>
      </div>

      {/* Filters */}
      <Card className="p-6">
        <div className="space-y-4">
          {/* Search */}
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                  <Search className="w-4 h-4" />
                </div>
                <Input
                  placeholder="Buscar por nombre o DNI..."
                  value={filters.search || ''}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
          </div>

          {/* Filter buttons */}
          <div className="flex flex-wrap gap-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 self-center">Filtros:</span>
            
            <Button
              variant={filters.status === 'new' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleStatusFilter('new')}
            >
              Nuevos
            </Button>
            
            <Button
              variant={filters.status === 'datos_completos' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleStatusFilter('datos_completos')}
            >
              Datos Completos
            </Button>
            
            <Button
              variant={filters.status === 'documentacion_completa' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleStatusFilter('documentacion_completa')}
            >
              Documentación Completa
            </Button>

            <div className="border-l border-gray-300 mx-2" />

            <Button
              variant={filters.type === 'unilateral' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleTypeFilter('unilateral')}
            >
              Unilateral
            </Button>
            
            <Button
              variant={filters.type === 'conjunta' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleTypeFilter('conjunta')}
            >
              Conjunta
            </Button>
          </div>
        </div>
      </Card>

      {/* Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800 border-b dark:border-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Nombre
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  DNI
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Tipo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Fase
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Fecha Creación
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-950 divide-y divide-gray-200 dark:divide-gray-800">
              {isLoading ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <p className="mt-2 text-gray-600 dark:text-gray-400">Cargando casos...</p>
                  </td>
                </tr>
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                    No se encontraron casos
                  </td>
                </tr>
              ) : (
                data?.items.map((case_) => (
                  <tr
                    key={case_.id}
                    className="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
                    onClick={() => navigate(`/cases/${case_.id}`)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                      #{case_.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                      {case_.nombre || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                      {case_.dni || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                      <span className="capitalize">{case_.type || '-'}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadgeColor(case_.status)}`}>
                        {getStatusLabel(case_.status)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400 capitalize">
                      {case_.phase.replace(/_/g, ' ')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                      {format(new Date(case_.created_at), "dd/MM/yyyy HH:mm", { locale: es })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/cases/${case_.id}`);
                          }}
                          className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                          title="Ver detalle"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={(e) => handleDownloadPDF(case_.id, e)}
                          className="text-green-600 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300"
                          title="Descargar PDF"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="px-6 py-4 border-t dark:border-gray-800 flex items-center justify-between">
            <div className="text-sm text-gray-700 dark:text-gray-300">
              Mostrando <span className="font-medium">{((data.page - 1) * data.page_size) + 1}</span> a{' '}
              <span className="font-medium">{Math.min(data.page * data.page_size, data.total)}</span> de{' '}
              <span className="font-medium">{data.total}</span> casos
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(data.page - 1)}
                disabled={data.page === 1}
              >
                <ChevronLeft className="w-4 h-4" />
                Anterior
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(data.page + 1)}
                disabled={data.page === data.pages}
              >
                Siguiente
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
