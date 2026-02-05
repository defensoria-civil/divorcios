import sys
sys.path.insert(0, 'backend/src')

from infrastructure.document.pdf_service_impl import TemplatePDFService
from datetime import date

service = TemplatePDFService()
case_data = {
    'type': 'bilateral',
    'apellido': 'Pérez',
    'nombres': 'Juan Carlos',
    'dni': '12345678',
    'nacionalidad': 'Argentina',
    'ocupacion': 'Empleado',
    'domicilio': 'Calle Falsa 123, San Rafael',
    'phone': '2604123456',
    'email': 'juan@example.com',
    'fecha_nacimiento': date(1980, 5, 15),
    'apellido_conyuge': 'González',
    'nombres_conyuge': 'María Laura',
    'dni_conyuge': '87654321',
    'nacionalidad_conyuge': 'Argentina',
    'ocupacion_conyuge': 'Docente',
    'domicilio_conyuge': 'Calle Real 456, San Rafael',
    'phone_conyuge': '2604654321',
    'email_conyuge': 'maria@example.com',
    'fecha_nacimiento_conyuge': date(1982, 8, 20),
    'fecha_matrimonio': date(2005, 3, 10),
    'lugar_matrimonio': 'San Rafael',
    'fecha_separacion': date(2023, 1, 15),
    'acta_numero': '123',
    'acta_libro': 'V',
    'acta_anio': '2005',
    'acta_foja': '45',
    'acta_oficina': 'Registro Civil San Rafael',
    'tiene_bienes': True,
    'info_bienes': 'Vivienda familiar',
    'tiene_hijos': True,
    'info_hijos': 'Dos hijos menores',
    'ultimo_domicilio_conyugal': 'Av Principal 789, San Rafael'
}

pdf_bytes = service.generate_divorce_petition_pdf(case_data)
with open('test_output.pdf', 'wb') as f:
    f.write(pdf_bytes)
print('✅ PDF generado exitosamente en test_output.pdf')
print(f'📄 Tamaño: {len(pdf_bytes):,} bytes')
print('\nVerifica visualmente que:')
print('  - El logo mide 3.5" de ancho (aproximadamente 8.89 cm)')
print('  - Los márgenes son: izquierdo 5cm, derecho 2cm, superior 3cm, inferior 2cm')
