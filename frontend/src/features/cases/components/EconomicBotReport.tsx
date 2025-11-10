import { useState } from 'react';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { casesApi } from '../api/cases.api';

/**
 * Muestra el informe preliminar generado por el bot para el perfil económico
 * y permite al operador aprobarlo para incorporarlo a la base semántica.
 */
export function EconomicBotReport({
  caseId,
  summary,
}: {
  caseId: number;
  summary: string;
}) {
  const [approved, setApproved] = useState(false);
  const [saving, setSaving] = useState(false);

  const approve = async () => {
    setSaving(true);
    try {
      // Reusar endpoint de update para disparar una acción backend (ingesta de conocimiento)
      await casesApi.updateCase(caseId, { econ_bot_report_approved: true, econ_bot_report_text: summary });
      setApproved(true);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Informe preliminar del bot (BLSG)</h3>
        <Button disabled={approved || saving} size="sm" onClick={approve}>
          {approved ? 'Aprobado' : 'Aprobar e incorporar al conocimiento'}
        </Button>
      </div>
      <pre className="text-sm bg-gray-50 dark:bg-gray-900/40 p-3 rounded whitespace-pre-wrap">
        {summary || 'Sin informe disponible'}
      </pre>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
        Al aprobar, el sistema incorporará este análisis a la base semántica para mejorar futuros diagnósticos automáticos.
      </p>
    </Card>
  );
}
