import logging

from django.template.loader import render_to_string
from weasyprint import HTML

logger = logging.getLogger(__name__)


def generate_expediente_pdf(expediente) -> bytes:
    html_content = render_to_string(
        "expedientes/expediente_pdf.html", {"expediente": expediente}
    )
    pdf_bytes = HTML(string=html_content).write_pdf()
    logger.info("PDF generado para expediente %s", expediente.reference)
    return pdf_bytes
