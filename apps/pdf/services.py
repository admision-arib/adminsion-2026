from io import BytesIO
from pathlib import Path
from datetime import datetime
from xml.sax.saxutils import escape

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle


# -------------------------------------------------
# Utilidades
# -------------------------------------------------
def limpiar(valor):
    if not valor:
        return "-"
    return escape(str(valor).strip())


def p(texto, bold=False, size=9):
    return Paragraph(
        limpiar(texto),
        ParagraphStyle(
            name="p",
            fontName="Helvetica-Bold" if bold else "Helvetica",
            fontSize=size,
            leading=size + 4,
            textColor=colors.HexColor("#111827"),
            alignment=TA_LEFT,
        ),
    )


# -------------------------------------------------
# Encabezado institucional
# -------------------------------------------------
def dibujar_encabezado(c, w, h, anio):
    mx = 15 * mm
    y = h - 15 * mm

    logo_minedu = Path(settings.BASE_DIR) / "static/img/logo_minedu.png"
    logo_arib = Path(settings.BASE_DIR) / "static/img/logo_arib.png"

    if logo_minedu.exists():
        c.drawImage(ImageReader(str(logo_minedu)), mx, y - 14 * mm, 28 * mm, 13 * mm)

    if logo_arib.exists():
        c.drawImage(ImageReader(str(logo_arib)), w - mx - 28 * mm, y - 14 * mm, 28 * mm, 13 * mm)

    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(w / 2, y - 5 * mm,
                        "INSTITUTO DE EDUCACIÓN SUPERIOR TECNOLÓGICO PÚBLICO")
    c.drawCentredString(w / 2, y - 9 * mm,
                        "“Alianza Renovada Ichuña Bélgica”")

    c.setFont("Helvetica", 8.5)
    c.drawCentredString(w / 2, y - 13 * mm,
                        "Resolución Ministerial N° 0353-2004-ED")
    c.drawCentredString(w / 2, y - 17 * mm,
                        "Provincia General Sánchez Cerro – Distrito de Ichuña")

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, y - 25 * mm, "FICHA DE POSTULANTE")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(w / 2, y - 31 * mm,
                        f"PROCESO DE ADMISIÓN IESTP ARIB – {anio}")

    return y - 40 * mm


# -------------------------------------------------
# PDF principal
# -------------------------------------------------
def generar_ficha_postulante_pdf(inscripcion):
    postulante = inscripcion.postulante

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    mx = 15 * mm

    y = dibujar_encabezado(c, width, height, inscripcion.convocatoria.anio)

    # =====================================================
    # N° INSCRIPCIÓN + CÓDIGO
    # =====================================================
    chip_h = 8 * mm
    gap = 4 * mm
    ancho_principal = width - 2 * mx - 30 * mm  # casi todo el ancho

    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(colors.HexColor("#1E3A8A"))

    c.roundRect(mx, y - chip_h, ancho_principal, chip_h, 2 * mm, stroke=1, fill=0)
    c.drawString(mx + 4 * mm, y - 5 * mm,
                 f"N° Inscripción: {inscripcion.numero_inscripcion}")

    y_code = y - chip_h - gap - chip_h
    c.roundRect(mx, y_code, ancho_principal, chip_h, 2 * mm, stroke=1, fill=0)
    c.drawString(mx + 4 * mm, y_code + 3 * mm,
                 f"Código: {inscripcion.codigo_postulante}")

    # =====================================================
    # FOTO PEQUEÑA (RECTANGULAR MUY BAJA)
    # =====================================================
    foto_w = 26 * mm
    foto_h = 24 * mm  # ✅ MUCHO MÁS BAJA
    foto_x = width - mx - foto_w
    foto_y = y - chip_h

    c.roundRect(
        foto_x,
        foto_y - foto_h + chip_h,
        foto_w,
        foto_h,
        2 * mm,
        stroke=1,
        fill=0
    )

    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(foto_x + foto_w / 2, foto_y - 4 * mm, "Foto")





    # =====================================================
    # PARTE DEL POSTULANTE (OCUPA TODO EL ANCHO)
    # =====================================================
    y_tabla_top = y_code - 12 * mm

    filas = [
        ("Apellidos y nombres", f"{postulante.apellido_paterno} {postulante.apellido_materno}, {postulante.nombres}"),
        ("Documento", f"{postulante.tipo_documento} - {postulante.numero_documento}"),
        ("Sexo", postulante.get_sexo_display()),
        ("Celular", postulante.celular),
        ("Correo electrónico", postulante.correo_electronico),
        ("Idioma materno", postulante.get_idioma_materno_display()),
        ("Fecha de nacimiento", postulante.fecha_nacimiento.strftime("%d/%m/%Y")),
        ("Lugar de nacimiento",
         f"{postulante.lugar_nacimiento}, {postulante.distrito_nacimiento}, "
         f"{postulante.provincia_nacimiento}, {postulante.departamento_nacimiento}, "
         f"{postulante.pais_nacimiento}"),
        ("Institución de procedencia", postulante.institucion_procedencia),
        ("Primera opción", inscripcion.primera_opcion_programa.nombre),
        ("Segunda opción",
         inscripcion.segunda_opcion_programa.nombre if inscripcion.segunda_opcion_programa else "No registró"),
        ("Modalidad", inscripcion.modalidad.nombre),
        ("Código de voucher", inscripcion.codigo_voucher_pago),
    ]

    data = [[p(k, True), p(v)] for k, v in filas]

    tabla = Table(
        data,
        colWidths=[42 * mm, ancho_principal - 42 * mm]
    )

    tabla.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    _, th = tabla.wrap(ancho_principal - 20 * mm, height)
    alto_borde = th + 20 * mm

#c.roundRect(mx, y_tabla_top - alto_borde, ancho_principal, alto_borde, 3 * mm, stroke=1, fill=0)

    c.roundRect(
        mx,
        y_tabla_top - alto_borde,
        width - 30 * mm,
        alto_borde,
        3 * mm,
        stroke=1,
        fill=0
    )

    c.setFont("Helvetica-Bold", 10.5)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.drawString(mx + 6 * mm, y_tabla_top - 8 * mm, "Parte del postulante")

    tabla.drawOn(c, mx + 10 * mm, y_tabla_top - 14 * mm - th)

    y = y_tabla_top - alto_borde - 14 * mm

    # =====================================================
    # DECLARACIÓN JURADA (SUBE)
    # =====================================================
    texto = (
        "Declaro bajo juramento que la información consignada en esta ficha de inscripción "
        "es verdadera, que los documentos adjuntados corresponden a mi persona y que acepto "
        "las disposiciones del proceso de admisión."
    )

    par = Paragraph(
        limpiar(texto),
        ParagraphStyle(
            "decl",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
        ),
    )

    _, ph = par.wrap(width - 42 * mm, 80 * mm)
    alto_decl = ph + 18 * mm

    c.roundRect(mx, y - alto_decl, width - 30 * mm,
                alto_decl, 3 * mm, stroke=1, fill=0)

    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(mx + 6 * mm, y - 7 * mm, "Declaración jurada")
    par.drawOn(c, mx + 6 * mm, y - 13 * mm - ph)

    y = y - alto_decl - 10 * mm

    # =====================================================
    # FECHA + FIRMA (AHORA VISIBLE)
    # =====================================================
    fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M")

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawString(mx, y, f"Ichuña, {fecha_hora}")

    c.line(width - mx - 50 * mm, y - 6 * mm, width - mx, y - 6 * mm)
    c.setFont("Helvetica", 8)
    c.drawCentredString(width - mx - 25 * mm, y - 11 * mm, "Firma del postulante")

    # =====================================================
    # PIE DE DOCUMENTO
    # =====================================================
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawCentredString(
        width / 2,
        y - 16 * mm,
        "Documento generado automáticamente por el Sistema de Admisión Institucional."
    )

    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf