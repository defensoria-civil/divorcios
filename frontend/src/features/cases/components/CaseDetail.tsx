import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import toast from 'react-hot-toast';
import { ArrowLeft, Download, User, Bot, Calendar, Phone, MapPin, Copy } from 'lucide-react';
import { casesApi } from '../api/cases.api';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import ShimmerButton from '@/shared/components/magicui/ShimmerButton';
import BlurFade from '@/shared/components/magicui/BlurFade';
import BorderBeam from '@/shared/components/magicui/BorderBeam';
import { PdfGenerationModal } from './PdfGenerationModal';
import { DocumentsViewer } from './DocumentsViewer';
import { EconomicProfileCard } from './EconomicProfileCard';
import { EconomicBotReport } from './EconomicBotReport';
import { DocRequestModal } from './DocRequestModal';

export function CaseDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const caseId = parseInt(id || '0', 10);
  const [showPdfModal, setShowPdfModal] = useState(false);
  const [showDocModal, setShowDocModal] = useState(false);
  const [opMsg, setOpMsg] = useState('');

  const { data: case_, isLoading, error } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => casesApi.getById(caseId),
    enabled: !!caseId,
  });

  const handleDownloadPDF = () => {
    setShowPdfModal(true);
  };

  const handleWhatsAppContact = () => {
    if (!case_?.phone) {
      toast.error('No hay número de teléfono disponible');
      return;
    }

    const raw = String(case_.phone);
    const digits = raw.split('@')[0].replace(/\D/g, '');
    const isLidLike = raw.includes('@lid') || (digits.length >= 15 && !digits.startsWith('54'));

    if (isLidLike) {
      toast.error('Este contacto está registrado con un ID interno de WhatsApp. Usá “Solicitar documentación por WhatsApp” para escribirle desde el sistema.');
      return;
    }

    // Normalización básica para Argentina
    let msisdn = digits;
    if (msisdn.startsWith('54') && !msisdn.startsWith('549')) {
      msisdn = msisdn.replace(/^54/, '549');
    } else if (!msisdn.startsWith('54')) {
      if (msisdn.length === 10) msisdn = '549' + msisdn; else msisdn = '549' + msisdn;
    }

    const message = encodeURIComponent(
      `Hola ${case_.nombre || 'estimado/a'},\n\nSoy del equipo de la Defensoría Civil de San Rafael.\n\nMe comunico respecto a tu trámite de divorcio (Caso #${case_.id}).\n\n¿En qué puedo ayudarte?`
    );

    const whatsappUrl = `https://wa.me/${msisdn}?text=${message}`;
    console.log('Opening WhatsApp with:', whatsappUrl);
    console.log('Phone number extracted:', msisdn);
    console.log('Original phone field:', case_.phone);

    window.open(whatsappUrl, '_blank');
    toast.success('Abriendo WhatsApp...');
  };

  const handleCopyPhone = () => {
    if (!case_?.phone) {
      toast.error('No hay número disponible');
      return;
    }
    
    const phoneNumber = case_.phone.split('@')[0];
    navigator.clipboard.writeText(phoneNumber);
    toast.success('Número copiado al portapapeles');
  };

  // Función para formatear el teléfono para visualización
  const formatPhoneDisplay = (phone: string) => {
    // Extraer el número sin el sufijo @lid
    const cleanPhone = phone.split('@')[0];
    
    // Si es muy largo (15 dígitos), probablemente sea: CódigoPaís + CódigoArea + Número
    // Formato Argentina: +54 261 xxx-xxxx (54 = Argentina, 261 = Mendoza)
    if (cleanPhone.length === 15 && cleanPhone.startsWith('54')) {
      // Intentar formatear como número argentino
      // 54 261 082 623 0006 96 -> probablemente duplicado o con prefijo extra
      return `+${cleanPhone.slice(0, 2)} ${cleanPhone.slice(2, 5)} ${cleanPhone.slice(5)}`;
    }
    
    // Si tiene 13-14 dígitos, formato internacional estándar
    if (cleanPhone.length >= 11) {
      return `+${cleanPhone.slice(0, 2)} ${cleanPhone.slice(2, 5)} ${cleanPhone.slice(5)}`;
    }
    
    // Formato genérico
    return cleanPhone;
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error || !case_) {
    return (
      <div className="p-6">
        <Card className="p-6">
          <p className="text-red-600 dark:text-red-400">Error cargando caso: {(error as Error)?.message}</p>
          <Button onClick={() => navigate('/cases')} className="mt-4">
            Volver a casos
          </Button>
        </Card>
      </div>
    );
  }

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

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            onClick={() => navigate('/cases')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Volver
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Caso #{case_.id}</h1>
            <p className="mt-1 text-gray-600 dark:text-gray-400">
              Creado el {format(new Date(case_.created_at), "dd 'de' MMMM 'de' yyyy", { locale: es })}
            </p>
          </div>
        </div>
        <ShimmerButton 
          onClick={handleDownloadPDF}
          className="h-10 px-4"
          background="linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)"
          shimmerColor="#60a5fa"
        >
          <Download className="w-4 h-4 mr-2" />
          Descargar PDF
        </ShimmerButton>
      </div>

      {/* Case Info */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Personal Data */}
          <BlurFade delay={0.1}>
            <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">Información Personal</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  Nombre Completo
                </label>
                <p className="text-gray-900 dark:text-gray-100">{case_.nombre || '-'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  DNI
                </label>
                <p className="text-gray-900 dark:text-gray-100">{case_.dni || '-'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  <Phone className="w-4 h-4 inline mr-1" />
                  Teléfono / WhatsApp
                </label>
                <div className="flex items-center gap-2">
                  <p className="text-gray-900 dark:text-gray-100 font-mono text-sm">
                    {formatPhoneDisplay(case_.phone)}
                  </p>
                  <button
                    onClick={handleCopyPhone}
                    className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                    title="Copiar número"
                  >
                    <Copy className="w-3 h-3 text-gray-500 dark:text-gray-400" />
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  <Calendar className="w-4 h-4 inline mr-1" />
                  Fecha de Nacimiento
                </label>
                <p className="text-gray-900 dark:text-gray-100">
                  {case_.fecha_nacimiento 
                    ? format(new Date(case_.fecha_nacimiento), "dd/MM/yyyy")
                    : '-'
                  }
                </p>
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  <MapPin className="w-4 h-4 inline mr-1" />
                  Domicilio
                </label>
                <p className="text-gray-900 dark:text-gray-100">{case_.domicilio || '-'}</p>
              </div>
            </div>
            </Card>
          </BlurFade>

          {/* Marriage Data */}
          {(case_.fecha_matrimonio || case_.lugar_matrimonio) && (
            <BlurFade delay={0.2}>
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">Datos del Matrimonio</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Fecha de Matrimonio
                  </label>
                  <p className="text-gray-900 dark:text-gray-100">
                    {case_.fecha_matrimonio
                      ? format(new Date(case_.fecha_matrimonio), "dd/MM/yyyy")
                      : '-'
                    }
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Lugar de Matrimonio
                  </label>
                  <p className="text-gray-900 dark:text-gray-100">{case_.lugar_matrimonio || '-'}</p>
                </div>
              </div>
            </Card>
            </BlurFade>
          )}

          {/* Economic Profile - Solicitante */}
          <BlurFade delay={0.22}>
            <EconomicProfileCard
              caseId={caseId}
              data={{
                situacion_laboral: case_.situacion_laboral,
                ingreso_mensual_neto: case_.ingreso_mensual_neto as any,
                vivienda_tipo: case_.vivienda_tipo,
                alquiler_mensual: case_.alquiler_mensual as any,
                patrimonio_inmuebles: case_.patrimonio_inmuebles,
                patrimonio_registrables: case_.patrimonio_registrables,
                econ_elegible_preliminar: case_.econ_elegible_preliminar as any,
                econ_razones: case_.econ_razones as any,
                type: case_.type,
              }}
            />
          </BlurFade>

          {/* Economic Profile - Cónyuge (solo conjunta) */}
          {case_.type === 'conjunta' && (
            <BlurFade delay={0.23}>
              <div className="space-y-4">
                <EconomicProfileCard
                  caseId={caseId}
                  data={{
                    situacion_laboral: case_.situacion_laboral_conyuge,
                    ingreso_mensual_neto: case_.ingreso_mensual_neto_conyuge as any,
                    vivienda_tipo: case_.vivienda_tipo_conyuge,
                    alquiler_mensual: case_.alquiler_mensual_conyuge as any,
                    patrimonio_inmuebles: case_.patrimonio_inmuebles_conyuge,
                    patrimonio_registrables: case_.patrimonio_registrables_conyuge,
                    econ_elegible_preliminar: case_.econ_elegible_preliminar_conyuge as any,
                    econ_razones: case_.econ_razones_conyuge as any,
                    type: case_.type,
                  }}
                />
                {/* Informe del bot visible en conjunta */}
                <EconomicBotReport caseId={caseId} summary={
                  (() => {
                    const partes: string[] = [];
                    if (typeof case_.econ_razones === 'string') partes.push(`Solicitante: ${case_.econ_razones}`);
                    if (typeof case_.econ_razones_conyuge === 'string') partes.push(`Cónyuge: ${case_.econ_razones_conyuge}`);
                    return partes.join('\n\n');
                  })()
                } />
              </div>
            </BlurFade>
          )}

          {/* Documents Viewer */}
          <BlurFade delay={0.25}>
            <DocumentsViewer
              caseId={caseId}
              dniImageUrl={case_.dni_image_url}
              dniBackUrl={case_.dni_back_url}
              marriageCertUrl={case_.marriage_cert_url}
              supportDocuments={case_.support_documents as any}
            />
          </BlurFade>

          {/* Conversation Timeline */}
          <BlurFade delay={0.3}>
            <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">Historial de Conversación</h2>
            <div className="space-y-4">
              {case_.messages.length === 0 ? (
                <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                  No hay mensajes aún
                </p>
              ) : (
                case_.messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-3 ${
                      message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                    }`}
                  >
                    <div
                      className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                        message.role === 'user'
                          ? 'bg-blue-500 text-white dark:bg-blue-600'
                          : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {message.role === 'user' ? (
                        <User className="w-4 h-4" />
                      ) : (
                        <Bot className="w-4 h-4" />
                      )}
                    </div>
                    <div
                      className={`flex-1 max-w-lg ${
                        message.role === 'user' ? 'text-right' : 'text-left'
                      }`}
                    >
                      <div
                        className={`inline-block px-4 py-2 rounded-lg ${
                          message.role === 'user'
                            ? 'bg-blue-600 text-white dark:bg-blue-700'
                            : 'bg-gray-200 text-gray-900 dark:bg-gray-700 dark:text-gray-100'
                        }`}
                      >
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {format(new Date(message.created_at), "dd/MM/yyyy HH:mm", { locale: es })}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
            </Card>
          </BlurFade>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Status Card */}
          <BlurFade delay={0.4}>
            <Card className="p-6 relative overflow-hidden">
              {case_.status === 'documentacion_completa' && (
                <BorderBeam 
                  size={200} 
                  duration={10}
                  colorFrom="#10b981"
                  colorTo="#34d399"
                />
              )}
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Estado del Caso</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                  Estado
                </label>
                <span className={`px-3 py-1 inline-flex text-sm font-semibold rounded-full ${getStatusBadgeColor(case_.status)}`}>
                  {getStatusLabel(case_.status)}
                </span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                  Tipo de Divorcio
                </label>
                <p className="text-gray-900 dark:text-gray-100 capitalize">{case_.type || '-'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                  Fase Actual
                </label>
                <p className="text-gray-900 dark:text-gray-100 capitalize">
                  {case_.phase.replace(/_/g, ' ')}
                </p>
              </div>
            </div>
            </Card>
          </BlurFade>

          {/* Competencia (Último domicilio conyugal) */}
          <BlurFade delay={0.45}>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Competencia</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <label className="block text-gray-500 dark:text-gray-400 mb-1">Último domicilio conyugal</label>
                  <p className="text-gray-900 dark:text-gray-100">{case_.ultimo_domicilio_conyugal || '-'}</p>
                </div>
                <div>
                  <label className="block text-gray-500 dark:text-gray-400 mb-1">Juzgado competente (a priori)</label>
                  {case_.ultimo_domicilio_conyugal ? (
                    (case_.ultimo_domicilio_conyugal.toLowerCase().includes('san rafael')) ? (
                      <span className="px-3 py-1 inline-flex text-xs font-semibold rounded-full bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-200">San Rafael</span>
                    ) : (
                      <span className="px-3 py-1 inline-flex text-xs font-semibold rounded-full bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-200">Otra jurisdicción</span>
                    )
                  ) : (
                    <span className="px-3 py-1 inline-flex text-xs font-semibold rounded-full bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">Sin datos</span>
                  )}
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">Este indicador es orientativo y debe ser verificado por un operador.</p>
                </div>
              </div>
            </Card>
          </BlurFade>

          {/* Actions Card */}
          <BlurFade delay={0.5}>
            <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Acciones</h3>
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={handleDownloadPDF}
              >
                <Download className="w-4 h-4 mr-2" />
                Descargar Demanda
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={handleWhatsAppContact}
              >
                <Phone className="w-4 h-4 mr-2" />
                Contactar por WhatsApp
              </Button>

              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => setShowDocModal(true)}
              >
                <Phone className="w-4 h-4 mr-2" />
                Solicitar documentación por WhatsApp
              </Button>

              <div className="text-xs text-gray-500 dark:text-gray-400 pl-2">
                Número: {case_.phone.split('@')[0]}
              </div>

              {/* Enviar mensaje libre */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  Enviar mensaje por WhatsApp (operador)
                </label>
                <textarea
                  className="w-full h-28 p-3 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-900 text-sm"
                  placeholder="Escribí tu mensaje para el usuario..."
                  value={opMsg}
                  onChange={(e) => setOpMsg(e.target.value)}
                />
                <div className="flex justify-end mt-2">
                  <Button
                    onClick={async () => {
                      const text = opMsg.trim();
                      if (!text) return toast.error('Escribí un mensaje');
                      try {
                        await casesApi.sendOperatorMessage(caseId, text);
                        toast.success('Mensaje enviado');
                        setOpMsg('');
                      } catch {
                        toast.error('No se pudo enviar el mensaje');
                      }
                    }}
                  >
                    Enviar
                  </Button>
                </div>
              </div>
            </div>
            </Card>
          </BlurFade>

          {/* Metadata Card */}
          <BlurFade delay={0.6}>
            <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Metadata</h3>
            <div className="space-y-3 text-sm">
              <div>
                <label className="block text-gray-500 dark:text-gray-400 mb-1">ID del Caso</label>
                <p className="text-gray-900 dark:text-gray-100 font-mono">#{case_.id}</p>
              </div>
              <div>
                <label className="block text-gray-500 dark:text-gray-400 mb-1">Fecha de Creación</label>
                <p className="text-gray-900 dark:text-gray-100">
                  {format(new Date(case_.created_at), "dd/MM/yyyy HH:mm", { locale: es })}
                </p>
              </div>
              <div>
                <label className="block text-gray-500 dark:text-gray-400 mb-1">Última Actualización</label>
                <p className="text-gray-900 dark:text-gray-100">
                  {format(new Date(case_.updated_at), "dd/MM/yyyy HH:mm", { locale: es })}
                </p>
              </div>
              <div>
                <label className="block text-gray-500 dark:text-gray-400 mb-1">Mensajes</label>
                <p className="text-gray-900 dark:text-gray-100">{case_.messages.length} mensajes</p>
              </div>
            </div>
            </Card>
          </BlurFade>
        </div>
      </div>

      {/* PDF Generation Modal */}
      {showPdfModal && (
        <PdfGenerationModal
          caseId={caseId}
          onClose={() => setShowPdfModal(false)}
        />
      )}

      {/* Docs Request Modal */}
      {showDocModal && (
        <DocRequestModal caseId={caseId} onClose={() => setShowDocModal(false)} />
      )}
    </div>
  );
}
