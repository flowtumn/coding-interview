import uuid
from django.test import TestCase
from rest_framework.exceptions import ErrorDetail
from api.models import Category
from api.models import Category, Company
from api.serializers import CategoriesSerializer


COMPANY_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
CATEGORY_PARENT_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
CATEGORY_CHILD1_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
CATEGORY_CHILD2_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")


class CategoriesSerializerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Company.objects.create(id=COMPANY_ID, name="Test Company")
        Category.objects.create(id=CATEGORY_PARENT_ID, name="Test Category1", company_id=COMPANY_ID)
        # parent_id -> child_id1
        Category.objects.create(
            id=CATEGORY_CHILD1_ID,
            name="Test Category2",
            company_id=COMPANY_ID,
            parent_category_id=CATEGORY_PARENT_ID,
        )
        # parent_id -> child_id1 -> child_id2
        Category.objects.create(
            id=CATEGORY_CHILD2_ID,
            name="Test Category3",
            company_id=COMPANY_ID,
            parent_category_id=CATEGORY_CHILD1_ID,
        )
    
    def test_init_without_company_id(self):
        """company_idがないとエラーになるか"""
        with self.assertRaises(RuntimeError) as context:
            CategoriesSerializer()

        self.assertEqual(
            str(context.exception),
            "CategoriesSerializer must be initialized with 'company_id' in context.",
        )

    def test_validate(self):
        """有効なデータでエラーにならないか"""
        for name, data in [
            ("name only", {"name": "New Category"}),
            ("name, parent_category_id both", {"name": "New Category", "parent_category_id": str(CATEGORY_PARENT_ID)}),
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

    def test_validate_be_own_parent(self):
        """親IDが同じ、または親を子配下に移動時のバリデーションを確認するテスト"""
        ## 成功ケース
        for name, parent_id, parent_category_id in [
            # ターゲット 子1。親にする相手: 今の親
            ("child1 to parent", CATEGORY_CHILD1_ID, CATEGORY_PARENT_ID),
            # ターゲット 子2。親にする相手: 今の親、子1の親
            ("child2 to parent", CATEGORY_CHILD2_ID, CATEGORY_CHILD1_ID),
            ("child2 is root parent", CATEGORY_CHILD2_ID, CATEGORY_PARENT_ID),
        ]:
            with self.subTest(name=name):
                category = Category.objects.get(id=parent_id)
                serializer = CategoriesSerializer(
                    instance=category, 
                    data={"parent_category_id": str(parent_category_id)},
                    partial=True,
                    context={"company_id": COMPANY_ID},
                )
        
                self.assertTrue(serializer.is_valid())

        ## 失敗ケース
        for name, parent_id, parent_category_id in [
            # ターゲット: 親。親にする相手 自身、子1、子2
            ("parent is own parent", CATEGORY_PARENT_ID, CATEGORY_PARENT_ID),
            ("parent is child1", CATEGORY_PARENT_ID, CATEGORY_CHILD1_ID),
            ("parent is child2", CATEGORY_PARENT_ID, CATEGORY_CHILD2_ID),
            # ターゲット: 子1。親にする相手 自身、子2
            ("child1 is own parent", CATEGORY_CHILD1_ID, CATEGORY_CHILD1_ID),
            ("child1 is child2", CATEGORY_CHILD1_ID, CATEGORY_CHILD2_ID),
            # ターゲット: 子2。親にする相手 自身
            ("child2 is own parent", CATEGORY_CHILD2_ID, CATEGORY_CHILD2_ID),
        ]:
            with self.subTest(name=name):
                category = Category.objects.get(id=parent_id)
                serializer = CategoriesSerializer(
                    instance=category, 
                    data={"parent_category_id": str(parent_category_id)},
                    partial=True,
                    context={"company_id": COMPANY_ID},
                )
        
                self.assertFalse(serializer.is_valid())
                self.assertEqual(
                    serializer.errors,
                    {
                        "parent_category_id": [ErrorDetail(string='A category cannot be its own parent or ancestor.', code='invalid')],
                    },
                )
