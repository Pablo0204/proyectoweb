from abc import ABC, abstractmethod
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import cm
from datetime import datetime
import io

class GeneradorActa(ABC):
    def generar_acta(self, trabajo, evaluaciones, promedio_final, estudiante, evaluador):
        self.encabezado(trabajo, estudiante)
        self.cuerpo(evaluaciones)
        self.resumen(promedio_final)
        self.pie(evaluador)
        return self.output()

    @abstractmethod
    def encabezado(self, trabajo, estudiante): pass
    @abstractmethod
    def cuerpo(self, evaluaciones): pass
    @abstractmethod
    def resumen(self, promedio_final): pass
    @abstractmethod
    def pie(self, evaluador): pass
    @abstractmethod
    def output(self): pass

class ActaPDF(GeneradorActa):
    def __init__(self):
        self.buffer = io.BytesIO()
        self.pdf = canvas.Canvas(self.buffer, pagesize=A4)
        self.width, self.height = A4
        self.y = self.height - 50

    def encabezado(self, trabajo, estudiante):
        self.pdf.setFont("Helvetica-Bold", 14)
        self.pdf.drawString(50, self.y, "UNIVERSIDAD ADVENTISTA DE CHILE")
        self.pdf.setFont("Helvetica", 12)
        self.pdf.drawString(50, self.y - 20, "Facultad de Ingeniería y Negocios")
        self.pdf.setFont("Helvetica", 10)
        self.pdf.drawString(50, self.y - 35, "Dirección: Camino a Tanilvoro km. 12, Las Mariposas, Chillán, Chile")
        self.pdf.drawString(50, self.y - 50, "Teléfono: +56 9 5842 7375")
        self.y -= 110

        self.pdf.setFont("Helvetica-Bold", 13)
        self.pdf.drawString(50, self.y, "Acta de Evaluación de Trabajo Académico")
        self.y -= 30

        self.pdf.setFont("Helvetica", 11)
        self.pdf.drawString(50, self.y, f"Título: {trabajo.titulo}")
        self.y -= 20
        self.pdf.drawString(50, self.y, f"Tipo: {trabajo.tipo}")
        self.y -= 20
        self.pdf.drawString(50, self.y, f"Estudiante: {estudiante.nombre}")
        self.y -= 30

    def cuerpo(self, evaluaciones):
        data = [["Criterio", "Nota"]]
        for e in evaluaciones:
            data.append([e["criterio"], f"{e['nota']}"])

        table = Table(data, colWidths=[10*cm, 4*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))

        self.y -= 10
        table.wrapOn(self.pdf, self.width, self.height)
        table.drawOn(self.pdf, 50, self.y - 20 - (20 * len(data)))
        self.y -= (30 + 20 * len(data))

    def resumen(self, promedio_final):
        self.y -= 20
        self.pdf.setFont("Helvetica-Bold", 12)
        self.pdf.drawString(50, self.y, f"Promedio Final: {promedio_final}")
        self.y -= 30

    def pie(self, evaluador):
        fecha = datetime.now().strftime("%d/%m/%Y")
        self.pdf.setFont("Helvetica", 10)
        self.pdf.drawString(50, self.y, f"Fecha de emisión: {fecha}")
        self.y -= 40

        self.pdf.setFont("Helvetica", 11)
        self.pdf.drawString(50, self.y, f"Firma del evaluador: {evaluador.nombre}")
        self.y -= 30
        self.pdf.drawString(50, self.y, "--- Fin del Acta ---")
        self.y -= 20

    def output(self):
        self.pdf.showPage()
        self.pdf.save()
        self.buffer.seek(0)
        return self.buffer.getvalue()
