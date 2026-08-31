import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


def generate_reference() -> str:
    return f"EXP-{uuid.uuid4().hex[:8].upper()}"


class Currency(models.TextChoices):
    EUR = "EUR", "Euro"
    USD = "USD", "US Dollar"
    GBP = "GBP", "British Pound"


class ExpedienteStatus(models.TextChoices):
    OPEN = "open", "Open"
    IN_PROGRESS = "in_progress", "In progress"
    CLOSED = "closed", "Closed"


class Expediente(models.Model):
    reference = models.CharField(
        max_length=20, default=generate_reference, unique=True, editable=False
    )
    debtor_name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=20)
    debt_amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    currency = models.CharField(
        max_length=3, choices=Currency.choices, default=Currency.EUR
    )
    status = models.CharField(
        max_length=20, choices=ExpedienteStatus.choices, default=ExpedienteStatus.OPEN
    )
    court = models.CharField(max_length=200, blank=True)
    opened_at = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-opened_at"]

    def __str__(self) -> str:
        return f"{self.reference} - {self.debtor_name}"
