import { useState } from 'react';
import { FileText, X, ZoomIn, ZoomOut, Download, Image as ImageIcon } from 'lucide-react';
import { Card } from '@/shared/components/ui/Card';
import { Button } from '@/shared/components/ui/Button';
import { casesApi } from '../api/cases.api';
import toast from 'react-hot-toast';

interface DocumentsViewerProps {
  caseId: number;
  dniImageUrl?: string | null;
  marriageCertUrl?: string | null;
}

interface ImageModalProps {
  imageUrl: string;
  title: string;
  onClose: () => void;
}

function ImageModal({ imageUrl, title, onClose }: ImageModalProps) {
  const [zoom, setZoom] = useState(100);

  const handleDownload = async () => {
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.toLowerCase().replace(/\s+/g, '_')}.jpg`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Imagen descargada');
    } catch (error) {
      toast.error('Error al descargar la imagen');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-900 rounded-lg max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {title}
          </h3>
          <div className="flex items-center gap-2">
            {/* Zoom Controls */}
            <div className="flex items-center gap-1 mr-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setZoom(Math.max(50, zoom - 25))}
                disabled={zoom <= 50}
              >
                <ZoomOut className="w-4 h-4" />
              </Button>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300 min-w-[50px] text-center">
                {zoom}%
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setZoom(Math.min(200, zoom + 25))}
                disabled={zoom >= 200}
              >
                <ZoomIn className="w-4 h-4" />
              </Button>
            </div>
            
            {/* Download Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownload}
            >
              <Download className="w-4 h-4 mr-2" />
              Descargar
            </Button>
            
            {/* Close Button */}
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Image Container */}
        <div className="flex-1 overflow-auto p-4 bg-gray-100 dark:bg-gray-800">
          <div className="flex items-center justify-center min-h-full">
            <img
              src={imageUrl}
              alt={title}
              style={{ width: `${zoom}%` }}
              className="max-w-none rounded-lg shadow-lg"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export function DocumentsViewer({ caseId, dniImageUrl, marriageCertUrl }: DocumentsViewerProps) {
  const hasDni = !!dniImageUrl;
  const hasMarriageCert = !!marriageCertUrl;
  const hasDocuments = hasDni || hasMarriageCert;

  if (!hasDocuments) {
    return (
      <Card className="p-6">
        <div className="text-center py-8">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600 dark:text-gray-400">
            No hay documentos cargados aún
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
            El usuario puede enviar fotos de su DNI y acta de matrimonio por WhatsApp
          </p>
        </div>
      </Card>
    );
  }

  const openDoc = (doc: 'dni' | 'marriage_cert') => {
    const url = casesApi.getDocumentUrl(caseId, doc);
    window.open(url, '_blank');
  };

  const downloadDoc = async (doc: 'dni' | 'marriage_cert') => {
    try {
      const url = casesApi.getDocumentUrl(caseId, doc);
      const res = await fetch(url);
      const blob = await res.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `${doc}.file`;
      document.body.appendChild(a);
      a.click();
      URL.revokeObjectURL(a.href);
      document.body.removeChild(a);
    } catch (e) {
      toast.error('No se pudo descargar el documento');
    }
  };

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100 flex items-center gap-2">
        <FileText className="w-5 h-5" />
        Documentación Cargada
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {hasDni && (
          <div className="p-4 border rounded-lg bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
              <FileText className="w-4 h-4" /> DNI del solicitante
            </p>
            <div className="mt-3 flex gap-2">
              <Button variant="outline" onClick={() => openDoc('dni')}>Abrir</Button>
              <Button variant="outline" onClick={() => downloadDoc('dni')}><Download className="w-4 h-4 mr-1"/>Descargar</Button>
            </div>
          </div>
        )}

        {hasMarriageCert && (
          <div className="p-4 border rounded-lg bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
              <FileText className="w-4 h-4" /> Acta de Matrimonio
            </p>
            <div className="mt-3 flex gap-2">
              <Button variant="outline" onClick={() => openDoc('marriage_cert')}>Abrir</Button>
              <Button variant="outline" onClick={() => downloadDoc('marriage_cert')}><Download className="w-4 h-4 mr-1"/>Descargar</Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
