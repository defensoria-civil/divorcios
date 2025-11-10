import { useEffect, useState } from 'react';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';
import { casesApi } from '../api/cases.api';

export function DocRequestModal({ caseId, onClose }: { caseId: number; onClose: () => void }) {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await casesApi.getDocsRequestPreview(caseId);
        setText(res.text || '');
      } catch {
        setText('');
      } finally {
        setLoading(false);
      }
    })();
  }, [caseId]);

  const send = async () => {
    setSending(true);
    try {
      await casesApi.sendDocsRequest(caseId, text);
      onClose();
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <Card className="w-full max-w-2xl p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Solicitar documentación por WhatsApp</h3>
        {loading ? (
          <div className="text-sm text-gray-500 dark:text-gray-400">Cargando vista previa...</div>
        ) : (
          <>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
              Revisá y editá el mensaje que se enviará al usuario. Al confirmar, el pedido se envía por este chat de WhatsApp.
            </p>
            <textarea
              className="w-full h-64 p-3 border border-gray-300 dark:border-gray-700 rounded bg-white dark:bg-gray-900 text-sm"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="outline" onClick={onClose}>Cancelar</Button>
              <Button onClick={send} disabled={sending}>{sending ? 'Enviando...' : 'Enviar ahora'}</Button>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
