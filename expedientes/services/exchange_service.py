import logging
from decimal import Decimal

import requests

logger = logging.getLogger(__name__)

FRANKFURTER_BASE_URL = "https://api.frankfurter.dev/v2"
REQUEST_TIMEOUT_SECONDS = 5

SUPPORTED_CURRENCIES = {"EUR", "USD", "GBP"}


class ExchangeServiceError(Exception):
    """Base exception for exchange rate service failures."""


class InvalidCurrencyError(ExchangeServiceError):
    """Raised when the requested currency is not supported."""


class ExchangeTimeoutError(ExchangeServiceError):
    """Raised when the external provider does not respond in time."""


class ExchangeProviderError(ExchangeServiceError):
    """Raised when the external provider returns an error or invalid data."""


def get_rate(base_currency: str, quote_currency: str) -> Decimal:
    if base_currency not in SUPPORTED_CURRENCIES or quote_currency not in SUPPORTED_CURRENCIES:
        raise InvalidCurrencyError(
            f"Unsupported currency pair: {base_currency}/{quote_currency}"
        )

    url = f"{FRANKFURTER_BASE_URL}/rate/{base_currency}/{quote_currency}"

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.Timeout as exc:
        logger.error("Timeout consultando Frankfurter (%s/%s)", base_currency, quote_currency)
        raise ExchangeTimeoutError("Exchange rate provider timed out") from exc
    except requests.RequestException as exc:
        logger.error(
            "Error consultando Frankfurter (%s/%s): %s", base_currency, quote_currency, exc
        )
        raise ExchangeProviderError("Exchange rate provider returned an error") from exc

    try:
        data = response.json()
        rate = Decimal(str(data["rate"]))
    except (KeyError, ValueError, TypeError) as exc:
        logger.error("Respuesta inválida de Frankfurter: %s", response.text[:200])
        raise ExchangeProviderError("Exchange rate provider returned invalid data") from exc

    return rate


def convert_amount(amount: Decimal, base_currency: str, quote_currency: str) -> Decimal:
    if base_currency == quote_currency:
        return amount

    rate = get_rate(base_currency, quote_currency)
    converted = (amount * rate).quantize(Decimal("0.01"))
    logger.info(
        "Conversión %s %s -> %s: %s", amount, base_currency, quote_currency, converted
    )
    return converted
