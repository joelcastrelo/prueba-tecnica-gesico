import logging

from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Expediente
from .serializers import ExpedienteSerializer
from .services import exchange_service, pdf_service
from .services.exchange_service import (
    ExchangeProviderError,
    ExchangeTimeoutError,
    InvalidCurrencyError,
)

logger = logging.getLogger(__name__)


class ExpedienteViewSet(viewsets.ModelViewSet):
    queryset = Expediente.objects.all()
    serializer_class = ExpedienteSerializer

    def perform_create(self, serializer):
        expediente = serializer.save()
        logger.info("Expediente creado: %s", expediente.reference)

    @action(detail=True, methods=["get"])
    def convertir(self, request, pk=None):
        expediente = self.get_object()
        target_currency = request.query_params.get("currency", "").upper()

        if not target_currency:
            return Response(
                {"detail": "El parámetro 'currency' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            converted_amount = exchange_service.convert_amount(
                expediente.debt_amount, expediente.currency, target_currency
            )
        except InvalidCurrencyError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ExchangeTimeoutError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except ExchangeProviderError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(
            {
                "reference": expediente.reference,
                "original_amount": str(expediente.debt_amount),
                "original_currency": expediente.currency,
                "converted_amount": str(converted_amount),
                "converted_currency": target_currency,
            }
        )

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        expediente = self.get_object()
        pdf_bytes = pdf_service.generate_expediente_pdf(expediente)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="expediente_{expediente.reference}.pdf"'
        )
        return response
