from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from application.interfaces.document.document_service import DocumentService
from datetime import datetime

class SimplePDFService(DocumentService):
    def generate_divorce_petition_pdf(self, case_data: dict) -> bytes:
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4
        y = height - 50
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Defensoría Civil - Petición de Divorcio")
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}")
        y -= 30
        items = [
            ("Tipo de divorcio", case_data.get("type", "")),
            ("Nombre", case_data.get("nombre", "")),
            ("DNI", case_data.get("dni", "")),
            ("Domicilio", case_data.get("domicilio", "")),
        ]
        for label, value in items:
            c.drawString(50, y, f"{label}: {value}")
            y -= 18
        y -= 10
        c.drawString(50, y, "Se solicita el inicio del trámite de divorcio conforme normativa vigente.")
        c.showPage()
        c.save()
        pdf = buf.getvalue()
        buf.close()
        return pdf
