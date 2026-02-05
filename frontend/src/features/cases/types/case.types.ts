export interface Case {
  id: number;
  phone: string;
  status: string;
  type: string | null;
  phase: string;
  nombre: string | null;
  dni: string | null;
  fecha_nacimiento: string | null;
  domicilio: string | null;
  fecha_matrimonio: string | null;
  lugar_matrimonio: string | null;
  ultimo_domicilio_conyugal?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
}

export interface SupportDocument {
  id: number;
  doc_type: 'anses_cert' | 'afip_constancia' | 'recibo_sueldo' | 'jubilacion_comprobante' | 'otro';
  mime_type?: string | null;
  created_at: string;
}

export interface CaseDetail extends Case {
  messages: Message[];
  dni_image_url?: string | null;
  dni_back_url?: string | null;
  marriage_cert_url?: string | null;
  support_documents?: SupportDocument[];
  // Perfil económico
  situacion_laboral?: string | null;
  ingreso_mensual_neto?: number | null;
  vivienda_tipo?: string | null;
  alquiler_mensual?: number | null;
  patrimonio_inmuebles?: string | null;
  patrimonio_registrables?: string | null;
  econ_elegible_preliminar?: boolean | null;
  econ_razones?: string | null;
  // Cónyuge (solo para conjunta)
  situacion_laboral_conyuge?: string | null;
  ingreso_mensual_neto_conyuge?: number | null;
  vivienda_tipo_conyuge?: string | null;
  alquiler_mensual_conyuge?: number | null;
  patrimonio_inmuebles_conyuge?: string | null;
  patrimonio_registrables_conyuge?: string | null;
  econ_elegible_preliminar_conyuge?: boolean | null;
  econ_razones_conyuge?: string | null;
}

export interface CaseFilters {
  page?: number;
  pageSize?: number;
  status?: string;
  type?: string;
  search?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export const CaseStatus = {
  NEW: 'new',
  DATOS_COMPLETOS: 'datos_completos',
  DOCUMENTACION_COMPLETA: 'documentacion_completa',
} as const;

export const CaseType = {
  UNILATERAL: 'unilateral',
  CONJUNTA: 'conjunta',
} as const;

export const CasePhase = {
  INICIO: 'inicio',
  TIPO_DIVORCIO: 'tipo_divorcio',
  NOMBRE: 'nombre',
  DNI: 'dni',
  FECHA_NACIMIENTO: 'fecha_nacimiento',
  DOMICILIO: 'domicilio',
  DOCUMENTACION: 'documentacion',
} as const;
