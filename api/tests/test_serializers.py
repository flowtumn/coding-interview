from django.test import TestCase
from api.models import Category
from api.serializers import CategoriesSerializer
import uuid
from api.models import Category, Company


COMPANY_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
CATEGORY_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")

class CategoriesSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Company.objects.create(id=COMPANY_ID, name="Test Company")
        Category.objects.create(id=CATEGORY_ID, name="Test Category", company_id=COMPANY_ID)

    def test_validate_cannot_be_own_parent(self):
        """自身を親に指定するとエラーになるか"""
        category = Category.objects.create(
            id=uuid.uuid4(),
            name="Self Parent Test",
            company_id=COMPANY_ID
        )
        
        # PATCHを想定し、instanceを渡し、自分自身のIDをparent_category_idに設定
        serializer = CategoriesSerializer(
            instance=category, 
            data={"parent_category_id": str(category.id)},
            context={"company_id": COMPANY_ID},
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 1)
        self.assertEqual(
            serializer.errors["parent_category_id"][0], 
            "A category cannot be its own parent."
        )
