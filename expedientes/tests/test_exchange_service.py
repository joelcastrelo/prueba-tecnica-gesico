from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase

from expedientes.services import exchange_service
from expedientes.services.exchange_service import (
    ExchangeProviderError,
    InvalidCurrencyError,
)


class ExchangeServiceTests(SimpleTestCase):
    def test_convert_amount_same_currency_skips_http_call(self):
        result = exchange_service.convert_amount(Decimal("100.00"), "EUR", "EUR")

        self.assertEqual(result, Decimal("100.00"))

    def test_get_rate_rejects_unsupported_currency(self):
        with self.assertRaises(InvalidCurrencyError):
            exchange_service.get_rate("EUR", "JPY")

    @patch("expedientes.services.exchange_service.requests.get")
    def test_convert_amount_uses_provider_rate(self, mock_get):
        mock_get.return_value.json.return_value = {"rate": 0.9}
        mock_get.return_value.raise_for_status.return_value = None

        result = exchange_service.convert_amount(Decimal("200.00"), "EUR", "GBP")

        self.assertEqual(result, Decimal("180.00"))

    @patch("expedientes.services.exchange_service.requests.get")
    def test_get_rate_raises_on_malformed_response(self, mock_get):
        mock_get.return_value.json.return_value = {"unexpected": "shape"}
        mock_get.return_value.raise_for_status.return_value = None

        with self.assertRaises(ExchangeProviderError):
            exchange_service.get_rate("EUR", "USD")

    @patch("expedientes.services.exchange_service.requests.get")
    def test_get_rate_raises_on_non_numeric_rate(self, mock_get):
        mock_get.return_value.json.return_value = {"rate": "ERROR"}
        mock_get.return_value.raise_for_status.return_value = None

        with self.assertRaises(ExchangeProviderError):
            exchange_service.get_rate("EUR", "USD")

    @patch("expedientes.services.exchange_service.requests.get")
    def test_get_rate_raises_on_non_positive_rate(self, mock_get):
        mock_get.return_value.json.return_value = {"rate": -1}
        mock_get.return_value.raise_for_status.return_value = None

        with self.assertRaises(ExchangeProviderError):
            exchange_service.get_rate("EUR", "USD")
