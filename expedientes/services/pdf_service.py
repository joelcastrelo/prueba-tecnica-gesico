import logging

from django.template.loader import render_to_string
from weasyprint import HTML

logger = logging.getLogger(__name__)


class PDFGenerationError(Exception):
    """Raised when an expediente PDF cannot be generated."""


def generate_expediente_pdf(expediente) -> bytes:
    try:
        html_content = render_to_string(
            "expedientes/expediente_pdf.html", {"expediente": expediente}
        )
        pdf_bytes = HTML(string=html_content).write_pdf()
    except Exception as exc:
        # Amplio a propósito: aquí es el límite del servicio de PDF, y
        # cualquier fallo interno de WeasyPrint o de la plantilla debe
        # traducirse a un error de dominio controlado, no propagarse como 500.
        logger.exception("Error generando PDF para expediente %s", expediente.reference)
        raise PDFGenerationError("No se ha podido generar el PDF.") from exc

    logger.info("PDF generado para expediente %s", expediente.reference)
    return pdf_bytes
