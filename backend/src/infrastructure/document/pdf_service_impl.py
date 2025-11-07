from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import Paragraph, Spacer, Image, PageBreak, Frame, PageTemplate, NextPageTemplate
from reportlab.platypus.doctemplate import BaseDocTemplate
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from application.interfaces.document.document_service import DocumentService
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
import os

class TemplatePDFService(DocumentService):
    """
    Genera PDFs a partir de plantillas Jinja2 ubicadas en backend/templates/legal/.
    - Usa ReportLab (Platypus) para formateo básico (títulos, párrafos y espaciados).
    - Soporta templates: divorcio_bilateral.j2 | divorcio_unilateral.j2
    """

    def __init__(self, templates_dir: Path | None = None):
        base = Path(__file__).parent.parent.parent.parent  # backend/src -> backend
        self.templates_dir = templates_dir or (base / "templates" / "legal")
        self.base_dir = base
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(enabled_extensions=(".j2",)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.styles = self._create_legal_styles()

    def _create_legal_styles(self):
        """Crea estilos específicos para documentos legales argentinos."""
        styles = getSampleStyleSheet()
        
        # Estilo para encabezado institucional
        styles.add(ParagraphStyle(
            name='HeaderInstitutional',
            parent=styles['Normal'],
            fontName='Times-Roman',
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
            spaceAfter=6,
        ))
        
        # Estilo para tipo de documento (alineado a derecha)
        styles.add(ParagraphStyle(
            name='DocumentType',
            parent=styles['Normal'],
            fontName='Times-Bold',
            fontSize=12,
            leading=14,
            alignment=TA_RIGHT,  # Cambiado a derecha
            spaceAfter=6,
            spaceBefore=0,
        ))
        
        # Estilo para destinatario (SEÑORA JUEZA)
        styles.add(ParagraphStyle(
            name='Addressee',
            parent=styles['Normal'],
            fontName='Times-Bold',
            fontSize=12,
            leading=18,
            alignment=TA_LEFT,  # Alineado a la izquierda
            spaceAfter=12,
            spaceBefore=12,
        ))
        
        # Estilo para texto normal justificado
        styles.add(ParagraphStyle(
            name='LegalBody',
            parent=styles['Normal'],
            fontName='Times-Roman',
            fontSize=12,
            leading=18,  # interlineado 1.5
            alignment=TA_JUSTIFY,
            firstLineIndent=0,  # Sin sangría por defecto
            leftIndent=0,
            rightIndent=0,
            spaceAfter=12,
        ))
        
        # Estilo para títulos de sección (I. II. III.)
        styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=styles['Normal'],
            fontName='Times-Bold',
            fontSize=12,
            leading=18,
            alignment=TA_LEFT,
            spaceBefore=18,
            spaceAfter=12,
            firstLineIndent=0,
            leftIndent=0,
        ))
        
        # Estilo para texto sin sangría (introducción de secciones)
        styles.add(ParagraphStyle(
            name='LegalBodyNoIndent',
            parent=styles['LegalBody'],
            firstLineIndent=0,
        ))
        
        # Estilo para cierre (ES JUSTICIA)
        styles.add(ParagraphStyle(
            name='Closing',
            parent=styles['Normal'],
            fontName='Times-Roman',
            fontSize=12,
            leading=18,
            alignment=TA_CENTER,
            spaceBefore=24,
            spaceAfter=12,
        ))
        
        return styles

    def _select_template(self, case_data: dict):
        tipo = (case_data.get("type") or "").lower()
        if tipo in ("bilateral", "conjunta", "presentacion bilateral"):
            return "divorcio_bilateral.j2"
        return "divorcio_unilateral.j2"

    def _build_context(self, case_data: dict):
        # Derivaciones útiles (edad si hay fecha_nacimiento)
        def edad(fecha):
            try:
                hoy = datetime.now().date()
                e = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
                return e
            except Exception:
                return None

        persona1 = {
            "apellido": case_data.get("apellido"),
            "nombres": case_data.get("nombres"),
            "dni": case_data.get("dni"),
            "nacionalidad": case_data.get("nacionalidad"),
            "ocupacion": case_data.get("ocupacion"),
            "domicilio": case_data.get("domicilio"),
            "phone": case_data.get("phone"),
            "email": case_data.get("email"),
            "edad": edad(case_data.get("fecha_nacimiento")) if case_data.get("fecha_nacimiento") else None,
        }
        persona2 = {
            "apellido": case_data.get("apellido_conyuge"),
            "nombres": case_data.get("nombres_conyuge"),
            "dni": case_data.get("dni_conyuge"),
            "nacionalidad": case_data.get("nacionalidad_conyuge"),
            "ocupacion": case_data.get("ocupacion_conyuge"),
            "domicilio": case_data.get("domicilio_conyuge"),
            "phone": case_data.get("phone_conyuge"),
            "email": case_data.get("email_conyuge"),
            "edad": edad(case_data.get("fecha_nacimiento_conyuge")) if case_data.get("fecha_nacimiento_conyuge") else None,
        }
        acta = {
            "numero": case_data.get("acta_numero"),
            "libro": case_data.get("acta_libro"),
            "anio": case_data.get("acta_anio"),
            "foja": case_data.get("acta_foja"),
            "oficina": case_data.get("acta_oficina"),
        }
        ctx = {
            "persona1": persona1,
            "persona2": persona2,
            "acta": acta,
            "fecha_matrimonio": case_data.get("fecha_matrimonio"),
            "lugar_matrimonio": case_data.get("lugar_matrimonio"),
            "fecha_separacion": case_data.get("fecha_separacion"),
            "tiene_bienes": case_data.get("tiene_bienes"),
            "info_bienes": case_data.get("info_bienes"),
            "bienes_muebles_text": case_data.get("bienes_muebles_text"),
            "tiene_hijos": case_data.get("tiene_hijos"),
            "info_hijos": case_data.get("info_hijos"),
            "ultimo_domicilio_conyugal": case_data.get("ultimo_domicilio_conyugal") or case_data.get("domicilio"),
            "office_address": case_data.get("office_address") or "E. Civit N° 257, San Rafael",
            "letrada_nombre": case_data.get("letrada_nombre") or "MARIA JORGELINA BAYÓN",
            "defensoría_nombre": case_data.get("defensoria_nombre") or "Cuarta Defensoría de Pobres y Ausentes de la Segunda Circunscripción Judicial de Mendoza",
        }
        return ctx

    def _add_header(self, canv, doc, logo_path, doc_type_text):
        """Dibuja encabezado con logo en el canvas directamente."""
        if not logo_path.exists():
            return
        
        try:
            from reportlab.lib.utils import ImageReader
            from reportlab.platypus import Image as PlatypusImage
            
            # Obtener dimensiones reales de la imagen
            img_reader = ImageReader(str(logo_path))
            img_width, img_height = img_reader.getSize()
            
            # Calcular aspecto ratio
            aspect = img_height / float(img_width)
            
            # El ancho completo disponible es el ancho de la página menos los márgenes
            # Página A4 = 210mm, márgenes izq+der = 70mm, disponible = 140mm
            available_width = 140*mm
            
            # Usar TODO el ancho disponible
            logo_width = available_width
            logo_height = logo_width * aspect
            
            # Limitar altura máxima a 3cm (banner es horizontal, será más bajo)
            max_height = 30*mm
            if logo_height > max_height:
                logo_height = max_height
                logo_width = logo_height / aspect
            
            # Centrar horizontalmente en la página
            x = (A4[0] - logo_width) / 2
            y = A4[1] - 15*mm - logo_height  # 1.5cm desde arriba
            
            # Dibujar la imagen usando el método recomendado
            canv.drawImage(str(logo_path), 
                          x, y, 
                          width=logo_width, 
                          height=logo_height,
                          preserveAspectRatio=True,
                          anchor='sw',
                          mask='auto')
            
        except Exception as e:
            print(f"Error dibujando logo: {e}")
            import traceback
            traceback.print_exc()
    
    def _add_header_to_story(self, story, case_data: dict):
        """Agrega espaciado y títulos al story (el logo se dibuja en canvas)."""
        # El logo se dibuja en el canvas (fuera del frame)
        # NO necesitamos espacio aquí porque el frame ya empieza más abajo
        
        # Tipo de documento (alineado a la derecha)
        tipo = (case_data.get("type") or "").lower()
        if tipo in ("bilateral", "conjunta", "presentacion bilateral"):
            doc_type = "DIVORCIO PRESENTACIÓN BILATERAL"
        else:
            doc_type = "DIVORCIO UNILATERAL"
        
        story.append(Paragraph(doc_type, self.styles['DocumentType']))
        story.append(Paragraph("BENEFICIO DE LITIGAR SIN GASTOS", self.styles['DocumentType']))
        story.append(Spacer(1, 18))  # Espacio antes del contenido
        
        return doc_type

    def generate_divorce_petition_pdf(self, case_data: dict) -> bytes:
        template_name = self._select_template(case_data)
        template = self.env.get_template(template_name)
        context = self._build_context(case_data)
        rendered = template.render(**context)

        buf = BytesIO()
        
        # Preparar logo (usar banner horizontal)
        logo_path = self.base_dir.parent / "data" / "banner-mpd.png"
        
        # Crear BaseDocTemplate para páginas alternadas
        doc = BaseDocTemplate(
            buf,
            pagesize=A4,
        )
        
        # Frame para páginas impares (1, 3, 5...): margen izquierdo amplio
        # Dejar espacio arriba para el logo (5.5cm desde arriba)
        frame_odd = Frame(
            50*mm,  # x1 - margen izquierdo amplio para encuadernación
            20*mm,  # y1 - margen inferior
            A4[0] - 50*mm - 20*mm,  # width
            A4[1] - 55*mm - 20*mm,  # height - dejar 5.5cm arriba para logo
            id='normal',
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0
        )
        
        # Frame para páginas pares (2, 4, 6...): margen derecho amplio
        frame_even = Frame(
            20*mm,  # x1 - margen izquierdo normal
            20*mm,  # y1 - margen inferior
            A4[0] - 50*mm - 20*mm,  # width (mismo ancho de texto)
            A4[1] - 55*mm - 20*mm,  # height - dejar 5.5cm arriba para logo
            id='normal',
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0
        )
        
        # Función de callback para dibujar logo en cada página
        def draw_header(canv, doc):
            canv.saveState()
            # Determinar tipo de documento
            tipo = (case_data.get("type") or "").lower()
            if tipo in ("bilateral", "conjunta", "presentacion bilateral"):
                doc_type = "DIVORCIO PRESENTACIÓN BILATERAL"
            else:
                doc_type = "DIVORCIO UNILATERAL"
            self._add_header(canv, doc, logo_path, doc_type)
            canv.restoreState()
        
        # Crear templates de página con callbacks
        template_odd = PageTemplate(
            id='odd',
            frames=[frame_odd],
            onPage=draw_header
        )
        
        template_even = PageTemplate(
            id='even',
            frames=[frame_even],
            onPage=draw_header
        )
        
        doc.addPageTemplates([template_odd, template_even])
        
        story = []
        
        # Agregar títulos (el logo se dibuja automáticamente en el canvas)
        doc_type = self._add_header_to_story(story, case_data)

        # Procesar el contenido renderizado
        lines = rendered.split("\n")
        i = 0
        page_num = 1
        paragraphs_in_page = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # Detectar títulos de sección (I. II. III. etc.)
            if self._is_section_title(line):
                story.append(Paragraph(line, self.styles['SectionTitle']))
                i += 1
                continue
            
            # Detectar destinatario
            if "SEÑORA JUEZA" in line or "SEÑOR JUEZ" in line:
                story.append(Paragraph(line, self.styles['Addressee']))
                i += 1
                continue
            
            # Detectar cierre
            if line in ["PROVEER DE CONFORMIDAD.", "ES JUSTICIA."]:
                story.append(Paragraph(line, self.styles['Closing']))
                i += 1
                continue
            
            # Agrupar líneas en párrafos
            paragraph_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not self._is_section_title(lines[i].strip()):
                paragraph_lines.append(lines[i].strip())
                i += 1
            
            # Unir líneas del párrafo
            paragraph_text = " ".join(paragraph_lines)
            
            # Determinar si necesita sangría
            if self._needs_indent(paragraph_text):
                story.append(Paragraph(paragraph_text, self.styles['LegalBody']))
            else:
                story.append(Paragraph(paragraph_text, self.styles['LegalBodyNoIndent']))
            
            paragraphs_in_page += 1
            
            # Alternar template cada ~15 párrafos (aproximado para cambio de página)
            # Esta es una heurística - ReportLab manejará los quiebres reales
            if paragraphs_in_page > 15:
                page_num += 1
                paragraphs_in_page = 0
                # Alternar entre odd y even
                next_template = 'even' if page_num % 2 == 0 else 'odd'
                story.append(NextPageTemplate(next_template))

        # Build personalizado con lógica de alternancia
        class AlternatingDocTemplate(BaseDocTemplate):
            def afterPage(self):
                """Alternar template después de cada página."""
                if self.page % 2 == 0:
                    self.handle_nextPageTemplate('odd')  # Próxima será impar
                else:
                    self.handle_nextPageTemplate('even')  # Próxima será par
        
        # Recrear doc como AlternatingDocTemplate
        doc = AlternatingDocTemplate(buf, pagesize=A4)
        doc.addPageTemplates([template_odd, template_even])
        
        doc.build(story)
        pdf = buf.getvalue()
        buf.close()
        return pdf
    
    def _is_section_title(self, text: str) -> bool:
        """Detecta si una línea es un título de sección."""
        roman_numerals = ['I. ', 'II. ', 'III. ', 'IV. ', 'V. ', 'VI. ', 'VII. ', 'VIII. ', 'IX. ', 'X. ']
        return any(text.startswith(num) for num in roman_numerals)
    
    def _needs_indent(self, text: str) -> bool:
        """Determina si un párrafo necesita sangría de primera línea."""
        # En documentos legales argentinos, NO se usa sangría de primera línea
        # Los párrafos se separan con espaciado
        return False
