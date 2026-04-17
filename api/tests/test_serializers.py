import uuid
from django.test import TestCase
from rest_framework.exceptions import ErrorDetail
from api.models import Category
from api.models import Category, Company
from api.serializers import CategoriesSerializer


COMPANY_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
CATEGORY_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


class CategoriesSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Company.objects.create(id=COMPANY_ID, name="Test Company")
        Category.objects.create(id=CATEGORY_ID, name="Test Category", company_id=COMPANY_ID)

    def test_validate(self):
        """有効なデータでエラーにならないか"""
        for name, data in [
            ("name only", {"name": "New Category"}),
            ("name, parent_category_id both", {"name": "New Category", "parent_category_id": str(CATEGORY_ID)}),
        ]:
            with self.subTest(name=name):
                serializer = CategoriesSerializer(
                    data=data,
                    context={"company_id": COMPANY_ID},
                )
                self.assertTrue(serializer.is_valid(), msg=serializer.errors)

    def test_validate_failures(self):
        """無効なデータでエラーになるか"""
        for name, data, expected_error in [
            (
                "empty name",
                {"name": ""},
                {"name": [ErrorDetail(string='This field may not be blank.', code='blank')]},
            ),
            (
                "invalid parent_category_id",
                {
                    "name": "hoge",
                    "parent_category_id": "invalid-uuid",
                },
                {
                    "parent_category_id": [ErrorDetail(string='Must be a valid UUID.', code='invalid')],
                },
            ),
        ]:
            with self.subTest(name=name):
                serializer = CategoriesSerializer(
                    data=data,
                    context={"company_id": COMPANY_ID},
                )
                self.assertFalse(serializer.is_valid())
                self.assertEqual(serializer.errors, expected_error)

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
            partial=True,
            context={"company_id": COMPANY_ID},
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "parent_category_id": [ErrorDetail(string='A category cannot be its own parent.', code='invalid')],
            },
        )
