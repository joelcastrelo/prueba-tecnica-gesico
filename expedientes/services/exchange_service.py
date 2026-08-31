import logging
from decimal import Decimal, InvalidOperation

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
            f"Moneda no soportada: {base_currency}/{quote_currency}"
        )

    url = f"{FRANKFURTER_BASE_URL}/rate/{base_currency}/{quote_currency}"

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.Timeout as exc:
        logger.error("Timeout consultando Frankfurter (%s/%s)", base_currency, quote_currency)
        raise ExchangeTimeoutError(
            "El servicio externo de tipos de cambio no respondió a tiempo."
        ) from exc
    except requests.RequestException as exc:
        logger.error(
            "Error consultando Frankfurter (%s/%s): %s", base_currency, quote_currency, exc
        )
        raise ExchangeProviderError(
            "No se ha podido consultar el servicio externo de tipos de cambio."
        ) from exc

    try:
        data = response.json()
        rate = Decimal(str(data["rate"]))
    except (KeyError, ValueError, TypeError, InvalidOperation) as exc:
        logger.error("Respuesta inválida de Frankfurter: %s", response.text[:200])
        raise ExchangeProviderError(
            "El servicio externo devolvió datos no válidos."
        ) from exc

    if not rate.is_finite() or rate <= 0:
        logger.error("Tasa de cambio no válida recibida de Frankfurter: %s", rate)
        raise ExchangeProviderError(
            "El servicio externo devolvió una tasa de cambio no válida."
        )

    return rate


def convert_amount(amount: Decimal, base_currency: str, quote_currency: str) -> Decimal:
    if base_currency == quote_currency:
        return amount

    rate = get_rate(base_currency, quote_currency)
    converted = (amount * rate).quantize(Decimal("0.01"))
    logger.info("Conversión realizada: %s -> %s", base_currency, quote_currency)
    return converted
