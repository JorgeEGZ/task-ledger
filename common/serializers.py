"""
Base serializers and common serializer utilities.
"""

from rest_framework import serializers


class BaseSerializer(serializers.ModelSerializer):
    """
    Base serializer with common functionality.
    """

    def get_fields(self):
        """
        Add common read-only fields to all serializers.
        """
        fields = super().get_fields()

        # Add audit fields as read-only if the model has them
        if 'created_at' in fields:
            fields['created_at'].read_only = True
        if 'updated_at' in fields:
            fields['updated_at'].read_only = True

        return fields


class EmptySerializer(serializers.Serializer):
    """
    Empty serializer for actions that don't require input data.
    """
    pass
