from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from expedientes.models import Currency, Expediente


class ExpedientePdfTests(APITestCase):
    def test_pdf_endpoint_returns_valid_pdf(self):
        expediente = Expediente.objects.create(
            debtor_name="Ana Torres Ruiz",
            tax_id="55667788C",
            debt_amount=Decimal("750.00"),
            currency=Currency.EUR,
        )

        response = self.client.get(reverse("expediente-pdf", args=[expediente.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
