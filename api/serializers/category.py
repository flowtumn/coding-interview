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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'company_id' not in self.context:
            raise RuntimeError(
                "CategoriesSerializer must be initialized with 'company_id' in context."
            )

    def validate_parent_category_id(self, value: uuid.UUID | None) -> uuid.UUID | None:
        if not value:
            return value

        company_id = self.context.get('company_id')
        if company_id is None:
            # 内部の問題なので 500 エラーで良い
            raise RuntimeError("Context: company_id is required.")

        # 存在チェック
        current_category = Category.objects.filter(id=value, company_id=company_id).first()
        if not current_category:
            raise serializers.ValidationError("Specified parent category does not exist within the company.")

        if self.instance is not None:
            # PATCH処理の考慮。自分自身は親に出来ず、親が子の配下に移動することもNG
            while current_category is not None:
                if current_category.id == self.instance.id:
                    raise serializers.ValidationError("A category cannot be its own parent or ancestor.")

                # TODO: 都度SQLが飛んでいる。データ数が増えたときは、対応が必要となる。
                current_category = Category.objects.filter(
                    id=current_category.parent_category_id,
                    company_id=company_id,
                ).first()

        return value