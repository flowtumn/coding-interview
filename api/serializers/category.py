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