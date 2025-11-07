import { useState, useEffect } from 'react';
import { X, CheckCircle2, AlertCircle, Loader2, Download, FileText } from 'lucide-react';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { Input } from '@/shared/components/ui/Input';
import toast from 'react-hot-toast';
import { casesApi } from '../api/cases.api';

interface FieldInfo {
  field: string;
  label: string;
  value: string | null;
}

interface ValidationData {
  case_id: number;
  is_valid: boolean;
  complete_fields: FieldInfo[];
  missing_fields: FieldInfo[];
  optional_fields: FieldInfo[];
  completion_percentage: number;
}

interface PdfGenerationModalProps {
  caseId: number;
  onClose: () => void;
}

type Step = 'validating' | 'incomplete' | 'generating' | 'preview' | 'complete';

export function PdfGenerationModal({ caseId, onClose }: PdfGenerationModalProps) {
  const [step, setStep] = useState<Step>('validating');
  const [validation, setValidation] = useState<ValidationData | null>(null);
  const [missingData, setMissingData] = useState<Record<string, string>>({});
  const [progress, setProgress] = useState(0);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  useEffect(() => {
    validateCaseData();
    
    // Cleanup: liberar URL del blob al desmontar
    return () => {
      if (pdfUrl) {
        window.URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [caseId]);

  const validateCaseData = async () => {
    setStep('validating');
    setProgress(10);
    
    try {
      const data = await casesApi.validateCase(caseId);
      setValidation(data);
      setProgress(100);
      
      // Si está completo, pasar directamente a generación
      if (data.is_valid) {
        setTimeout(() => generatePDF(), 500);
      } else {
        setStep('incomplete');
      }
    } catch (error) {
      console.error('Error validating case:', error);
      toast.error('Error al validar los datos del caso');
      onClose();
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setMissingData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const generatePDF = async (preview: boolean = true) => {
    setStep('generating');
    setProgress(0);
    
    // Simular progreso
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) return prev;
        return prev + 10;
      });
    }, 200);
    
    try {
      const blob = await casesApi.downloadPetition(caseId);
      clearInterval(progressInterval);
      setProgress(100);
      
      const url = window.URL.createObjectURL(blob);
      
      if (preview) {
        // Mostrar previsualización
        setPdfUrl(url);
        setStep('preview');
        toast.success('PDF generado - Previsualización lista');
      } else {
        // Descargar directamente
        const a = document.createElement('a');
        a.href = url;
        a.download = `demanda-divorcio-caso-${caseId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        setStep('complete');
        toast.success('PDF descargado exitosamente');
      }
    } catch (error) {
      clearInterval(progressInterval);
      console.error('Error generating PDF:', error);
      toast.error('Error al generar el PDF');
      onClose();
    }
  };
  
  const handleDownloadFromPreview = () => {
    if (!pdfUrl) return;
    
    const a = document.createElement('a');
    a.href = pdfUrl;
    a.download = `demanda-divorcio-caso-${caseId}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    setStep('complete');
    toast.success('PDF descargado exitosamente');
  };

  const handleSaveAndGenerate = async () => {
    if (!validation) return;
    
    // Validar que todos los campos faltantes estén completados
    const allFieldsFilled = validation.missing_fields.every(
      field => missingData[field.field] && missingData[field.field].trim() !== ''
    );
    
    if (!allFieldsFilled) {
      toast.error('Por favor, completa todos los campos requeridos');
      return;
    }
    
    const toastId = toast.loading('Guardando datos...');
    
    try {
      // Actualizar caso con los datos faltantes
      await casesApi.updateCase(caseId, missingData);
      toast.success('Datos actualizados', { id: toastId });
      
      // Generar PDF
      await generatePDF();
    } catch (error) {
      console.error('Error saving data:', error);
      toast.error('Error al guardar los datos', { id: toastId });
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <FileText className="w-6 h-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                Generar Demanda de Divorcio
              </h2>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Validating Step */}
          {step === 'validating' && (
            <div className="space-y-6">
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
                  <p className="text-gray-600 dark:text-gray-400">
                    Validando datos del caso...
                  </p>
                  <div className="mt-4 w-64 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-600 transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Incomplete Data Step */}
          {step === 'incomplete' && validation && (
            <div className="space-y-6">
              {/* Progress Bar */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Progreso de completitud
                  </span>
                  <span className="text-sm font-bold text-blue-600">
                    {validation.completion_percentage}%
                  </span>
                </div>
                <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-500"
                    style={{ width: `${validation.completion_percentage}%` }}
                  />
                </div>
              </div>

              {/* Complete Fields */}
              <div>
                <h3 className="text-sm font-semibold text-green-600 dark:text-green-400 mb-3 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  Campos Completos ({validation.complete_fields.length})
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  {validation.complete_fields.map((field) => (
                    <div
                      key={field.field}
                      className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg"
                    >
                      <p className="text-xs text-green-600 dark:text-green-400 font-medium mb-1">
                        {field.label}
                      </p>
                      <p className="text-sm text-gray-900 dark:text-gray-100 truncate">
                        {field.value || '-'}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Missing Fields */}
              {validation.missing_fields.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-red-600 dark:text-red-400 mb-3 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    Campos Faltantes ({validation.missing_fields.length})
                  </h3>
                  <div className="space-y-3">
                    {validation.missing_fields.map((field) => (
                      <div
                        key={field.field}
                        className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
                      >
                        <label className="block text-sm font-medium text-red-700 dark:text-red-300 mb-2">
                          {field.label} *
                        </label>
                        <Input
                          type="text"
                          placeholder={`Ingrese ${field.label.toLowerCase()}`}
                          value={missingData[field.field] || ''}
                          onChange={(e) => handleInputChange(field.field, e.target.value)}
                          className="w-full"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Optional Fields */}
              {validation.optional_fields.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-blue-600 dark:text-blue-400 mb-3">
                    Información Adicional
                  </h3>
                  <div className="grid grid-cols-2 gap-3">
                    {validation.optional_fields.map((field) => (
                      <div
                        key={field.field}
                        className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg"
                      >
                        <p className="text-xs text-blue-600 dark:text-blue-400 font-medium mb-1">
                          {field.label}
                        </p>
                        <p className="text-sm text-gray-900 dark:text-gray-100">
                          {typeof field.value === 'boolean' 
                            ? (field.value ? 'Sí' : 'No')
                            : (field.value || '-')
                          }
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                <Button variant="outline" onClick={onClose} className="flex-1">
                  Cancelar
                </Button>
                <Button
                  onClick={validation.is_valid ? generatePDF : handleSaveAndGenerate}
                  className="flex-1"
                >
                  {validation.missing_fields.length > 0 
                    ? 'Guardar y Generar PDF'
                    : 'Generar PDF'
                  }
                </Button>
              </div>
            </div>
          )}

          {/* Generating Step */}
          {step === 'generating' && (
            <div className="space-y-6">
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
                  <p className="text-gray-900 dark:text-gray-100 font-semibold mb-2">
                    Generando documento PDF...
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Esto puede tomar unos segundos
                  </p>
                  <div className="mt-6 w-64 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-600 transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <p className="mt-2 text-xs text-gray-500 dark:text-gray-500">
                    {progress}%
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Preview Step */}
          {step === 'preview' && pdfUrl && (
            <div className="space-y-4">
              <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Previsualización del Documento
                </h3>
                
                {/* PDF Viewer */}
                <div className="bg-white dark:bg-gray-900 rounded-lg overflow-hidden" style={{ height: '500px' }}>
                  <iframe
                    src={pdfUrl}
                    className="w-full h-full"
                    title="PDF Preview"
                  />
                </div>
                
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-3 text-center">
                  Revisá el documento antes de descargarlo. Podés hacer zoom y navegar las páginas.
                </p>
              </div>
              
              {/* Actions */}
              <div className="flex gap-3">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    window.URL.revokeObjectURL(pdfUrl);
                    setPdfUrl(null);
                    setStep('incomplete');
                  }} 
                  className="flex-1"
                >
                  Volver a Editar
                </Button>
                <Button
                  onClick={handleDownloadFromPreview}
                  className="flex-1"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Descargar PDF
                </Button>
              </div>
            </div>
          )}

          {/* Complete Step */}
          {step === 'complete' && (
            <div className="space-y-6">
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                    <CheckCircle2 className="w-10 h-10 text-green-600 dark:text-green-400" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                    ¡PDF Generado Exitosamente!
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-6">
                    El documento ha sido descargado automáticamente
                  </p>
                  <Button onClick={onClose} className="px-8">
                    Cerrar
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
