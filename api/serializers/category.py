from typing import Any
import uuid
from rest_framework import serializers
from api.models import Category


class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'id', 
            'name', 
            'parent_category_id', 
            'created_at', 
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]
    
    id = serializers.UUIDField(format='hex_verbose', read_only=True)
    name = serializers.CharField(required=True, max_length=255)
    parent_category_id = serializers.UUIDField(
        required=False,
        allow_null=True, 
        format='hex_verbose', 
    )

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        # PATCH操作時、自身を親カテゴリに設定できないようにする
        if self.instance and data.get('parent_category_id') == self.instance.id:
            raise serializers.ValidationError(
                {"parent_category_id": "A category cannot be its own parent."}
            )
        return data
    
    def validate_parent_category_id(self, value: uuid.UUID | None) -> uuid.UUID | None:
        if value:
            company_id = self.context.get('company_id')
            if not Category.objects.filter(id=value, company_id=company_id).exists():
                raise serializers.ValidationError("Specified parent category does not exist within the company.")
        return value