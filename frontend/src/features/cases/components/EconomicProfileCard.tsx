import { useState } from 'react';
import { casesApi } from '../api/cases.api';
import { Button } from '@/shared/components/ui/Button';
import { Card } from '@/shared/components/ui/Card';

type Props = {
  caseId: number;
  data: {
    situacion_laboral?: string | null;
    ingreso_mensual_neto?: number | null;
    vivienda_tipo?: string | null;
    alquiler_mensual?: number | null;
    patrimonio_inmuebles?: string | null;
    patrimonio_registrables?: string | null;
    econ_elegible_preliminar?: boolean | null;
    econ_razones?: string | null;
    type?: string | null;
  };
};

export function EconomicProfileCard({ caseId, data }: Props) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    situacion_laboral: data.situacion_laboral || '',
    ingreso_mensual_neto: data.ingreso_mensual_neto || undefined,
    vivienda_tipo: data.vivienda_tipo || '',
    alquiler_mensual: data.alquiler_mensual || undefined,
    patrimonio_inmuebles: data.patrimonio_inmuebles || '',
    patrimonio_registrables: data.patrimonio_registrables || '',
  });

  const save = async () => {
    const updates: Record<string, any> = { ...form };
    // Normalizar números
    if (typeof updates.ingreso_mensual_neto === 'string') {
      updates.ingreso_mensual_neto = parseInt(updates.ingreso_mensual_neto.replace(/\D/g, '') || '0', 10);
    }
    if (typeof updates.alquiler_mensual === 'string') {
      updates.alquiler_mensual = parseInt(updates.alquiler_mensual.replace(/\D/g, '') || '0', 10);
    }
    await casesApi.updateCase(caseId, updates);
    setEditing(false);
    // No refetch aquí: CaseDetail lo refresca por React Query al navegar; si hace falta, se puede invalidar la query desde arriba.
  };

  const disabled = !editing;
  const elegible = data.econ_elegible_preliminar;
  const razones = (() => {
    try {
      return data.econ_razones ? JSON.parse(data.econ_razones) : null;
    } catch {
      return null;
    }
  })();

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Perfil económico (declaración jurada)
        </h3>
        {!editing ? (
          <Button variant="outline" size="sm" onClick={() => setEditing(true)}>Editar</Button>
        ) : (
          <div className="flex gap-2">
            <Button size="sm" onClick={save}>Guardar</Button>
            <Button variant="outline" size="sm" onClick={() => { setEditing(false); setForm({
              situacion_laboral: data.situacion_laboral || '',
              ingreso_mensual_neto: data.ingreso_mensual_neto || undefined,
              vivienda_tipo: data.vivienda_tipo || '',
              alquiler_mensual: data.alquiler_mensual || undefined,
              patrimonio_inmuebles: data.patrimonio_inmuebles || '',
              patrimonio_registrables: data.patrimonio_registrables || '',
            }); }}>Cancelar</Button>
          </div>
        )}
      </div>

      <div className="space-y-4 text-sm">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-gray-500 dark:text-gray-400 mb-1">Situación laboral</label>
            <input
              disabled={disabled}
              className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
              value={form.situacion_laboral}
              onChange={e => setForm(f => ({ ...f, situacion_laboral: e.target.value }))}
              placeholder="desocupado / dependencia / autonomo / informal / jubilado"
            />
            {form.situacion_laboral?.toLowerCase().includes('desocup') && (
              <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                Recordatorio: Certificado Negativo de ANSES: https://servicioswww.anses.gob.ar/censite/index.aspx
              </p>
            )}
          </div>
          <div>
            <label className="block text-gray-500 dark:text-gray-400 mb-1">Ingreso mensual neto (ARS)</label>
            <input
              disabled={disabled}
              className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
              value={form.ingreso_mensual_neto ?? ''}
              onChange={e => setForm(f => ({ ...f, ingreso_mensual_neto: e.target.value }))}
              placeholder="250000"
            />
          </div>
          <div>
            <label className="block text-gray-500 dark:text-gray-400 mb-1">Tipo de vivienda</label>
            <input
              disabled={disabled}
              className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
              value={form.vivienda_tipo}
              onChange={e => setForm(f => ({ ...f, vivienda_tipo: e.target.value }))}
              placeholder="propia / alquilada / cedida"
            />
          </div>
          <div>
            <label className="block text-gray-500 dark:text-gray-400 mb-1">Alquiler mensual (ARS)</label>
            <input
              disabled={disabled || form.vivienda_tipo?.toLowerCase() !== 'alquilada'}
              className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
              value={form.alquiler_mensual ?? ''}
              onChange={e => setForm(f => ({ ...f, alquiler_mensual: e.target.value }))}
              placeholder="120000"
            />
          </div>
        </div>

        <div>
          <label className="block text-gray-500 dark:text-gray-400 mb-1">Patrimonio - Inmuebles</label>
          <textarea
            disabled={disabled}
            className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
            value={form.patrimonio_inmuebles}
            onChange={e => setForm(f => ({ ...f, patrimonio_inmuebles: e.target.value }))}
            placeholder="casa en San Rafael, Mendoza; lote en ..."
          />
        </div>
        <div>
          <label className="block text-gray-500 dark:text-gray-400 mb-1">Patrimonio - Registrables</label>
          <textarea
            disabled={disabled}
            className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
            value={form.patrimonio_registrables}
            onChange={e => setForm(f => ({ ...f, patrimonio_registrables: e.target.value }))}
            placeholder="auto 2015 ABC123 Ford Fiesta; moto 2018 ..."
          />
        </div>

        {typeof elegible === 'boolean' && (
          <div>
            <label className="block text-gray-500 dark:text-gray-400 mb-1">Resultado preliminar BLSG</label>
            <span className={`px-2 py-1 rounded text-xs font-semibold ${elegible ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-200' : 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200'}`}>
              {elegible ? 'Califica a priori' : 'No califica a priori'}
            </span>
            {razones && (
              <pre className="mt-2 text-xs bg-gray-50 dark:bg-gray-900/40 p-2 rounded overflow-x-auto">
                {JSON.stringify(razones, null, 2)}
              </pre>
            )}
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              La evaluación es preliminar y puede ser revisada por un operador luego de ver la documentación.
            </p>
          </div>
        )}
      </div>
    </Card>
  );
}
