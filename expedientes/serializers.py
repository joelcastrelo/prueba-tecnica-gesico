from rest_framework import serializers

from .models import Expediente


class ExpedienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expediente
        fields = [
            "id",
            "reference",
            "debtor_name",
            "tax_id",
            "debt_amount",
            "currency",
            "status",
            "court",
            "opened_at",
            "notes",
        ]
        read_only_fields = ["id", "reference", "opened_at"]
