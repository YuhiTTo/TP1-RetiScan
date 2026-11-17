"""Generador de informes PDF de soporte clínico para RetiScan (US-20).

Este módulo no realiza consultas a la base de datos ni a Amazon S3.
"""
from dataclasses import dataclass
from datetime import date, datetime
from html import escape
from io import BytesIO
from math import isfinite

from PIL import Image as PILImage, ImageOps
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as PDFImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


@dataclass(frozen=True)
class ReportPDFData:
    evaluation_id: int
    report_version: int
    establishment_name: str
    evaluation_date: datetime
    eye: str
    patient_name: str
    patient_document: str
    patient_birthdate: date
    patient_sex: str
    doctor_name: str
    rd_result: str
    rd_confidence: float
    glaucoma_result: str
    glaucoma_confidence: float
    suggested_priority: str | None
    medical_observation: str | None


def _safe(value: object) -> str:
    return escape(str(value).strip() if value is not None and str(value).strip() else "No registrado").replace("\n", "<br/>")


def _confidence(value: float) -> str:
    number = float(value)
    if not isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError("La confianza del modelo debe estar entre 0 y 1.")
    return f"{number * 100:.1f} %"


def _age(born: date, on: date) -> int:
    if born > on:
        raise ValueError("La fecha de nacimiento supera la fecha de evaluación.")
    return on.year - born.year - ((on.month, on.day) < (born.month, born.day))


def generate_report_pdf(data: ReportPDFData, retinography_bytes: bytes) -> bytes:
    """Produce PDF bytes con datos clínicos existentes, sin generar diagnósticos."""
    if data.evaluation_id <= 0 or data.report_version <= 0:
        raise ValueError("Identificadores de evaluación o versión inválidos.")
    if data.eye not in ("OD", "OI"):
        raise ValueError("El ojo evaluado debe ser OD u OI.")
    if not retinography_bytes:
        raise ValueError("La retinografía es obligatoria para el reporte.")

    rd_pct = _confidence(data.rd_confidence)
    gl_pct = _confidence(data.glaucoma_confidence)
    age = _age(data.patient_birthdate, data.evaluation_date.date())

    # Reducir tamaño y normalizar imagen para evitar PDF excesivamente pesado.
    with PILImage.open(BytesIO(retinography_bytes)) as original:
        eye_image = ImageOps.exif_transpose(original)
        eye_image.thumbnail((1200, 1200))
        image_buffer = BytesIO()
        eye_image.convert("RGB").save(image_buffer, format="JPEG", quality=87)

    image_buffer.seek(0)
    stream = BytesIO()
    doc = SimpleDocTemplate(
        stream,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=18 * mm,
        title=f"RetiScan - Informe de retinografía {data.evaluation_id}",
        author="RetiScan",
    )
    page_width = A4[0] - 36 * mm
    navy = colors.HexColor("#173A52")
    teal = colors.HexColor("#067F83")
    pale = colors.HexColor("#E9F5F5")
    gray = colors.HexColor("#536674")

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="RSHeader", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=navy, spaceAfter=4))
    styles.add(ParagraphStyle(name="RSTitle", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=navy))
    styles.add(ParagraphStyle(name="RSBody", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=13))
    styles.add(ParagraphStyle(name="RSMuted", parent=styles["Normal"], fontName="Helvetica", fontSize=8, leading=11, textColor=gray))
    styles.add(ParagraphStyle(name="RSSection", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=teal, spaceBefore=11, spaceAfter=5))
    styles.add(ParagraphStyle(name="RSImageCaption", parent=styles["Normal"], alignment=TA_CENTER, fontName="Helvetica", fontSize=8, textColor=gray))

    def p(value, style="RSBody"):
        return Paragraph(_safe(value), styles[style])

    def field(label, value):
        return Paragraph(f"<font color='#536674'>{escape(label)}:</font> {_safe(value)}", styles["RSBody"])

    sections = []
    header = Table([[p(data.establishment_name, "RSHeader"), p("INFORME CLÍNICO DE RETINOGRAFÍA", "RSTitle")]], colWidths=[page_width * .42, page_width * .58])
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 9), ("LINEBELOW", (0, 0), (-1, -1), 1, teal)]))
    sections.extend([header, Spacer(1, 5 * mm)])

    metadata = Table([
        [field("Fecha de evaluación", data.evaluation_date.strftime("%d/%m/%Y")), field("Ojo evaluado", data.eye)],
    ], colWidths=[page_width / 2] * 2)
    metadata.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    sections.append(metadata)

    sections.append(p("DATOS DEL PACIENTE Y RESPONSABLE", "RSSection"))
    info = Table([
        [field("Paciente", data.patient_name), field("Médico responsable", data.doctor_name)],
        [field("DNI", data.patient_document), field("Sexo", data.patient_sex)],
        [field("Edad a la evaluación", f"{age} años"), field("Fecha de nacimiento", data.patient_birthdate.strftime("%d/%m/%Y"))],
    ], colWidths=[page_width / 2] * 2)
    info.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F6F8")), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7), ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
    sections.append(info)

    sections.append(p("RESULTADOS AUTOMATIZADOS DE APOYO CLÍNICO", "RSSection"))
    ai = Table([
        [p("Patología", "RSHeader"), p("Clasificación", "RSHeader"), p("Confianza", "RSHeader")],
        [p("Retinopatía diabética"), p(data.rd_result), p(rd_pct)],
        [p("Glaucoma"), p(data.glaucoma_result), p(gl_pct)],
    ], colWidths=[page_width * .30, page_width * .49, page_width * .21], repeatRows=1)
    ai.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), pale), ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#D7E2E8")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    sections.append(ai)
    sections.extend([Spacer(1, 3 * mm), field("Prioridad sugerida por el sistema", data.suggested_priority)])

    sections.append(p("RETINOGRAFÍA EVALUADA", "RSSection"))
    iw, ih = eye_image.size
    scale = min((page_width * .63) / iw, (63 * mm) / ih)
    retina = PDFImage(image_buffer, width=iw * scale, height=ih * scale)
    retina.hAlign = "CENTER"
    sections.extend([retina, Spacer(1, 2 * mm), p("Imagen de fondo de ojo asociada a esta evaluación.", "RSImageCaption")])

    sections.append(p("OBSERVACIÓN MÉDICA", "RSSection"))
    sections.append(p(data.medical_observation))
    sections.extend([Spacer(1, 6 * mm), p("AVISO IMPORTANTE", "RSSection")])
    sections.append(p("Los resultados automatizados, las probabilidades de confianza y la prioridad sugerida son información de soporte clínico. No constituyen un diagnóstico definitivo ni sustituyen la evaluación, interpretación o criterio del médico oftalmólogo.", "RSMuted"))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D7E2E8"))
        canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(gray)
        canvas.drawString(18 * mm, 10 * mm, "RetiScan | Reporte de apoyo clínico")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Página {doc.page}")
        canvas.restoreState()

    doc.build(sections, onFirstPage=footer, onLaterPages=footer)
    return stream.getvalue()
