from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io

def generar_pdf_certificado(nombre: str, cuil: str, fecha: str):
    """
    Función interna para crear el PDF del certificado.
    """
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # Encabezado Oficial
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, "PROVINCIA DE SANTA FE")
    p.setFont("Helvetica", 12)
    p.drawString(100, 780, "Registro de Deudores Alimentarios Morosos (RDAM)")
    
    p.line(100, 770, 500, 770)
    
    # Cuerpo del Certificado
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, 700, "CERTIFICADO DE ESTADO")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, 650, f"Se certifica que el ciudadano: {nombre}")
    p.drawString(100, 630, f"Con CUIL: {cuil}")
    p.drawString(100, 610, f"Fecha de emisión: {fecha}")
    
    p.drawString(100, 550, "Estado: NO REGISTRA DEUDA ALIMENTARIA.")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer