from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from expedientes.models import Currency, Expediente, ExpedienteStatus


def make_expediente(**overrides):
    defaults = {
        "debtor_name": "Juan Pérez García",
        "tax_id": "12345678Z",
        "debt_amount": Decimal("1250.00"),
        "currency": Currency.EUR,
        "status": ExpedienteStatus.OPEN,
        "court": "Juzgado de Primera Instancia n.º 3 de A Coruña",
    }
    defaults.update(overrides)
    return Expediente.objects.create(**defaults)


class ExpedienteCrudTests(APITestCase):
    def test_create_expediente(self):
        url = reverse("expediente-list")
        payload = {
            "debtor_name": "María López Sánchez",
            "tax_id": "87654321X",
            "debt_amount": "500.00",
            "currency": Currency.EUR,
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["reference"].startswith("EXP-"))

    def test_create_expediente_rejects_non_positive_amount(self):
        url = reverse("expediente-list")
        payload = {
            "debtor_name": "María López Sánchez",
            "tax_id": "87654321X",
            "debt_amount": "0.00",
            "currency": Currency.EUR,
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("debt_amount", response.data)

    def test_list_expedientes(self):
        make_expediente()
        make_expediente(tax_id="11223344B")

        response = self.client.get(reverse("expediente-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_retrieve_expediente(self):
        expediente = make_expediente()

        response = self.client.get(reverse("expediente-detail", args=[expediente.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["reference"], expediente.reference)

    def test_retrieve_missing_expediente_returns_404(self):
        response = self.client.get(reverse("expediente-detail", args=[999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_expediente(self):
        expediente = make_expediente()

        response = self.client.patch(
            reverse("expediente-detail", args=[expediente.pk]),
            {"status": ExpedienteStatus.CLOSED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expediente.refresh_from_db()
        self.assertEqual(expediente.status, ExpedienteStatus.CLOSED)

    def test_delete_expediente(self):
        expediente = make_expediente()

        response = self.client.delete(reverse("expediente-detail", args=[expediente.pk]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Expediente.objects.filter(pk=expediente.pk).exists())


class ExpedienteConvertTests(APITestCase):
    @patch("expedientes.services.exchange_service.requests.get")
    def test_convert_amount_success(self, mock_get):
        mock_get.return_value.json.return_value = {"rate": 1.08}
        mock_get.return_value.raise_for_status.return_value = None
        expediente = make_expediente(debt_amount=Decimal("100.00"), currency=Currency.EUR)

        url = reverse("expediente-convertir", args=[expediente.pk])
        response = self.client.get(url, {"currency": "USD"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["converted_amount"], Decimal("108.00"))

    @patch("expedientes.services.exchange_service.requests.get")
    def test_convert_amount_provider_timeout_returns_504(self, mock_get):
        import requests

        mock_get.side_effect = requests.Timeout
        expediente = make_expediente(debt_amount=Decimal("100.00"), currency=Currency.EUR)

        url = reverse("expediente-convertir", args=[expediente.pk])
        response = self.client.get(url, {"currency": "USD"})

        self.assertEqual(response.status_code, status.HTTP_504_GATEWAY_TIMEOUT)
