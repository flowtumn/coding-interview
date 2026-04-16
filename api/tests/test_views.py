import dataclasses
import uuid
from api.models import Category, Company
from api.views.category import get_company, parse_must_uuid, CategoryView, InvalidCompanyID, InvalidCategoryID
from django.forms.models import model_to_dict
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.test import APITestCase


@dataclasses.dataclass
class CategoryData:
    category_id: uuid.UUID
    company_id: uuid.UUID
    name: str
    parent_category_id: uuid.UUID | None = None


@dataclasses.dataclass
class CompanyData:
    company_id: uuid.UUID
    name: str
    categories: list[CategoryData] = dataclasses.field(default_factory=list)


COMPANY_1_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
COMPANY_2_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
COMPANY_3_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
NOT_FOUND_COMPANY_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")

COMPANY_2_CATEGORY_1_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")
COMPANY_3_CATEGORY_1_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
COMPANY_3_CATEGORY_1_1_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
COMPANY_3_CATEGORY_2_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")


class CategoryViewUtilsTests(TestCase):
    """CategoryViewのAPI以外のユニットテスト"""

    def test_parse_must_uuid_success(self):
        """parse_must_uuidのテスト"""
        for name, v, expected in [
            ("valid uuid", "11111111-1111-1111-1111-111111111111", uuid.UUID("11111111-1111-1111-1111-111111111111")),
        ]:
            with self.subTest(msg=name):
                self.assertEqual(
                    expected,
                    parse_must_uuid(value=v, exception=InvalidCompanyID),
                )

    # def test_parse_must_uuid_failures(self):
    #     """parse_must_uuidの失敗ケースのテスト"""
    #     for name, v, raise_exception in [
    #         ("invalid uuid format", "invalid-uuid", InvalidCompanyID),
    #         ("empty string", "", InvalidCategoryID),
    #     ]:
    #         with self.subTest(msg=name):
    #             try:
    #                 parse_must_uuid(value=v, exception=raise_exception)
    #             except type(raise_exception) as e:
    #                 pass
    
    def test_get_company_success(self):
        """get_companyのテスト"""
        company = Company.objects.create(id=COMPANY_1_ID, name="Test Company 1")

        self.assertEqual(
            company,
            get_company(company_id=COMPANY_1_ID),
        )

    # def test_get_company_not_found(self):
    #     """get_companyの会社が見つからないケースのテスト"""
    #     with self.assertRaises(InvalidCompanyID) as cm:
    #         get_company(company_id=NOT_FOUND_COMPANY_ID)
    #     self.assertNotEqual(str(cm.exception), str(InvalidCompanyID))


    def test_convert_to_response(self):
        """CategoryView.convert_to_responseのテスト"""
        for name, categories, expected in [
            (
                "no category",
                [],
                [],
            ),
            (
                "one category without parent",
                [
                    {
                        "id": COMPANY_2_CATEGORY_1_ID,
                        "name": "Category 1",
                        "parent_category_id": None,
                    },
                ],
                [
                    {
                        "id": COMPANY_2_CATEGORY_1_ID,
                        "name": "Category 1",
                        "parent_category_id": None,
                        "children": [],
                    },
                ],
            ),
            (
                "multiple categories with hierarchy",
                [
                    {
                        "id": COMPANY_3_CATEGORY_1_ID,
                        "name": "Category 1",
                        "parent_category_id": None,
                    },
                    {
                        "id": COMPANY_3_CATEGORY_1_1_ID,
                        "name": "Category 1-1",
                        "parent_category_id": COMPANY_3_CATEGORY_1_ID,
                    },
                    {
                        "id": COMPANY_3_CATEGORY_2_ID,
                        "name": "Category 2",
                        "parent_category_id": None,
                    },
                    {
                        "id": COMPANY_2_CATEGORY_1_ID,
                        "name": "Category 2",
                        "parent_category_id": COMPANY_3_CATEGORY_1_1_ID,
                    },
                ],
                [
                    {
                        "id": COMPANY_3_CATEGORY_1_ID,
                        "name": "Category 1",
                        "parent_category_id": None,
                        "children": [
                            {
                                "id": COMPANY_3_CATEGORY_1_1_ID,
                                "name": "Category 1-1",
                                "parent_category_id": COMPANY_3_CATEGORY_1_ID,
                                "children": [
                                    {
                                        "id": COMPANY_2_CATEGORY_1_ID,
                                        "name": "Category 2",
                                        "parent_category_id": COMPANY_3_CATEGORY_1_1_ID,
                                        "children": [],
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "id": COMPANY_3_CATEGORY_2_ID,
                        "name": "Category 2",
                        "parent_category_id": None,
                        "children": [],
                    },
                ],
            ),
            (
                "category with parent_category_id that does not exist",
                [
                    {
                        "id": COMPANY_3_CATEGORY_1_ID,
                        "name": "Category 1",
                        "parent_category_id": None,
                    },
                    {
                        "id": COMPANY_3_CATEGORY_1_1_ID,
                        "name": "Category 1-1",
                        "parent_category_id": COMPANY_3_CATEGORY_1_ID,
                    },
                    {
                        "id": COMPANY_3_CATEGORY_2_ID,
                        "name": "Category 2",
                        "parent_category_id": COMPANY_2_CATEGORY_1_ID, # 存在しない親カテゴリID
                    },
                ],
                [
                    {
                        "id": COMPANY_3_CATEGORY_1_ID,
                        "name": "Category 1",
                        "parent_category_id": None,
                        "children": [
                            {
                                "id": COMPANY_3_CATEGORY_1_1_ID,
                                "name": "Category 1-1",
                                "parent_category_id": COMPANY_3_CATEGORY_1_ID,
                                "children": [],
                            },
                        ],
                    },
                    # 親が存在しないが、ツリーのルートに置かれる
                    {
                        "id": COMPANY_3_CATEGORY_2_ID,
                        "name": "Category 2",
                        "parent_category_id": COMPANY_2_CATEGORY_1_ID,
                        "children": [],
                    },
                ],
            ),
        ]:
            with self.subTest(msg=name):
                self.assertEqual(
                    expected,
                    CategoryView.convert_to_response(categories=categories),
                )


class CategoryViewAPITests(APITestCase):
    """CategoryViewのAPIのテスト"""

    TEST_COMPANIES = [
        CompanyData(company_id=COMPANY_1_ID, name="Test Company 1"),
        CompanyData(
            company_id=COMPANY_2_ID,
            name="Test Company 2",
            categories=[
                CategoryData(
                    category_id=COMPANY_2_CATEGORY_1_ID,
                    company_id=COMPANY_2_ID,
                    name="Category 1",
                ),
            ],
        ),
        CompanyData(
            company_id=COMPANY_3_ID,
            name="Test Company 3",
            categories=[
                CategoryData(
                    category_id=COMPANY_3_CATEGORY_1_ID,
                    company_id=COMPANY_3_ID,
                    name="Category 1",
                ),
                CategoryData(
                    category_id=COMPANY_3_CATEGORY_1_1_ID,
                    company_id=COMPANY_3_ID,
                    name="Category 1-1",
                    parent_category_id=COMPANY_3_CATEGORY_1_ID,
                ),
                CategoryData(
                    category_id=COMPANY_3_CATEGORY_2_ID,
                    company_id=COMPANY_3_ID,
                    name="Category 2",
                ),
            ]
        )
    ]
    TEST_START_TIME = timezone.now()

    @classmethod
    def setUpTestData(cls):
        """テスト開始前にテスト用のデータを作成する"""
        for company in cls.TEST_COMPANIES:
            Company.objects.create(id=company.company_id, name=company.name)
            for category in company.categories:
                Category.objects.create(
                    id=category.category_id,
                    company_id=category.company_id,
                    name=category.name,
                    parent_category_id=category.parent_category_id,
                )

    def assert_datetime_within_range(self, at: str) -> None:
        """日時文字列がテスト開始から5秒以内であることを確認します"""
        dt = parse_datetime(at)
        self.assertIsNotNone(dt)
        self.assertTrue(self.TEST_START_TIME <= dt <= self.TEST_START_TIME + timezone.timedelta(seconds=5))
        
    def _exclude_timestamp_with_test(self, categories: list[dict]) -> list[dict]:
        """カテゴリのリストから作成日時、更新日時を取り除いて返します。
        取り除く前に、、テスト開始から5秒以内に作成された日時であることを確認します。
        """
        for category in categories:
            self.assert_datetime_within_range(at=category.pop("created_at"))
            self.assert_datetime_within_range(at=category.pop("updated_at"))
            category["children"] = self._exclude_timestamp_with_test(category["children"])
        return categories

    def test_get_category_success(self):
        """カテゴリIDを指定して取得するテスト"""
        for name, company_id, category_id, expected in [
            (
                "company 2 with one category",
                COMPANY_2_ID,
                COMPANY_2_CATEGORY_1_ID,
                {
                    "id": str(COMPANY_2_CATEGORY_1_ID),
                    "name": "Category 1",
                    "parent_category_id": None,
                    "children": [],
                    # 作成時刻、更新時刻も変えるが、テストの都合上、値は取り除いて比較する
                    # "created_at": ANY,
                    # "updated_at": ANY,
                },
            ),
            (
                "company 3 with multiple categories and hierarchy",
                COMPANY_3_ID,
                COMPANY_3_CATEGORY_1_ID,
                {
                    "id": str(COMPANY_3_CATEGORY_1_ID),
                    "name": "Category 1",
                    "parent_category_id": None,
                    "children": [
                        {
                            "id": str(COMPANY_3_CATEGORY_1_1_ID),
                            "name": "Category 1-1",
                            "parent_category_id": str(COMPANY_3_CATEGORY_1_ID),
                            "children": [],
                        },
                    ],
                },
            ),
        ]:
            with self.subTest(msg=name):
                r = self.client.get(
                    reverse(
                        "category-detail",
                        kwargs={
                            "company_id": company_id,
                            "category_id": category_id,
                        },
                    ),
                )
                self.assertEqual(r.status_code, 200)

                actual_data = self._exclude_timestamp_with_test(
                    categories=[r.json()],
                )

                self.assertEqual(len(actual_data), 1)
                self.assertEqual(
                    actual_data[0],
                    expected,
                )

    def test_get_category_failures(self):
        """カテゴリIDを指定して取得する際の失敗ケースのテスト"""
        for name, status_code, company_id, category_id in [
            ("invalid company_id", 400, "invalid", COMPANY_2_CATEGORY_1_ID),
            ("not found company_id", 404, NOT_FOUND_COMPANY_ID, COMPANY_2_CATEGORY_1_ID),
            ("invalid category_id", 400, COMPANY_2_ID, "invalid"),
            ("not found category_id", 404, COMPANY_2_ID, COMPANY_3_CATEGORY_1_1_ID),
        ]:
            with self.subTest(msg=name, status_code=status_code):
                r = self.client.get(
                    reverse(
                        "category-detail",
                        kwargs={
                            "company_id": company_id,
                            "category_id": category_id,
                        },
                    ),
                )

                self.assertEqual(status_code, r.status_code)

    def test_list_success(self):
        """カテゴリのリストを取得するテスト"""
        for name, company_id, expected in [
            (
                "company 1 with no category",
                COMPANY_1_ID,
                [],
            ),
            (
                "company 2 with one category",
                COMPANY_2_ID,
                [
                    {
                        "id": str(COMPANY_2_CATEGORY_1_ID),
                        "name": "Category 1",
                        "parent_category_id": None,
                        "children": [],
                        # 作成時刻、更新時刻も変えるが、テストの都合上、値は取り除いて比較する
                        # "created_at": ANY,
                        # "updated_at": ANY,
                    },
                ],
            ),
            (
                "company 3 with multiple categories and hierarchy",
                COMPANY_3_ID,
                [
                    {
                        "id": str(COMPANY_3_CATEGORY_1_ID),
                        "name": "Category 1",
                        "parent_category_id": None,
                        "children": [
                            {
                                "id": str(COMPANY_3_CATEGORY_1_1_ID),
                                "name": "Category 1-1",
                                "parent_category_id": str(COMPANY_3_CATEGORY_1_ID),
                                "children": [],
                            },
                        ],
                    },
                    {
                        "id": str(COMPANY_3_CATEGORY_2_ID),
                        "name": "Category 2",
                        "parent_category_id": None,
                        "children": [],
                    },
                ],
            ),
        ]:
            with self.subTest(msg=name):
                r = self.client.get(reverse("categories", kwargs={"company_id": company_id}))
                self.assertEqual(r.status_code, 200)

                actual_data = r.json()
                actual_data["categories"] = self._exclude_timestamp_with_test(categories=actual_data["categories"])

                self.assertEqual(
                    actual_data,
                    {
                        "categories": expected,
                    },
                )

    def test_list_failures(self):
        """カテゴリ一覧を取得する際の失敗ケースのテスト"""
        for name, status_code, company_id in [
            ("invalid company_id", 400, "invalid"),
            ("not found company_id", 404, NOT_FOUND_COMPANY_ID),
        ]:
            with self.subTest(msg=name):
                r = self.client.get(reverse("categories", kwargs={"company_id": company_id}))
                self.assertEqual(status_code, r.status_code)

    def test_create_success(self):
        """カテゴリを作成するテスト"""
        for name, company_id in [
            ("company 1", COMPANY_1_ID),
            ("company 2", COMPANY_2_ID),
        ]:
            with self.subTest(msg=name):
                # 企業間で同じカテゴリ名を作成できることを確認するため、カテゴリ名称は固定にする
                r = self.client.post(
                    reverse("categories", kwargs={"company_id": company_id}),
                    data={
                        "name": "category1",
                    },
                    format='json',
                )

                self.assertEqual(r.status_code, 201)

                # id, created_at, updated_at は動的に生成されるため取り除く
                actual_data = r.json()
                category_id = actual_data.pop("id")

                # 直近の時間かをテストする
                self.assert_datetime_within_range(at=actual_data.pop("created_at"))
                self.assert_datetime_within_range(at=actual_data.pop("updated_at"))

                self.assertEqual(
                    actual_data,
                    {
                        "name": "category1",
                        "parent_category_id": None,
                    },
                )

                # 作成されたカテゴリがDBに存在することを確認
                self.assertTrue(
                    Category.objects.filter(
                        id=category_id,
                        company_id=company_id,
                        name="category1",
                        parent_category_id=None,
                    ).exists(),
                )

                # 再度同じリクエストを投げるとエラーになる
                r = self.client.post(
                    reverse("categories", kwargs={"company_id": company_id}),
                    data={
                        "name": "category1",
                    },
                    format='json',
                )
                self.assertEqual(r.status_code, 409)

    def test_create_failures(self):
        """カテゴリ作成時の失敗ケースのテスト"""
        for name, status_code, company_id, parent_category_id in [
            ("invalid company_id", 400, "invalid", None),
            ("not found company_id", 404, NOT_FOUND_COMPANY_ID, None),
            ("invalid parent_category_id", 400, COMPANY_1_ID, "invalid-category-id"),
            ("invalid parent_category_id with not found category", 400, COMPANY_3_ID, COMPANY_1_ID),
        ]:
            with self.subTest(msg=name):
                r = self.client.post(
                    reverse("categories", kwargs={"company_id": company_id}),
                    data={
                        "name": "category1",
                        "parent_category_id": parent_category_id,
                    },
                    format='json',
                )
                self.assertEqual(status_code, r.status_code)

    def test_update(self):
        """カテゴリを更新するテスト"""
        for name, company_id, category_id, body in [
            (
                "company 2 category 1 update name",
                COMPANY_2_ID,
                COMPANY_2_CATEGORY_1_ID,
                {
                    "name": "updated company 2 category 1 name",
                },
            ),
            # 親を COMPANY_3_CATEGORY_2_ID に変更
            (
                "company 3 category 1-1 update parent_category_id to null",
                COMPANY_3_ID,
                COMPANY_3_CATEGORY_1_1_ID,
                {
                    "parent_category_id": COMPANY_3_CATEGORY_2_ID,
                },
            ),
            (
                "company 3 category 1-1 update name and parent_category_id",
                COMPANY_3_ID,
                COMPANY_3_CATEGORY_1_1_ID,
                {
                    "name": "updated category 1-1 name",
                    "parent_category_id": None,
                },
            ),
        ]:
            with self.subTest(msg=name):
                r = self.client.patch(
                    reverse(
                        "category-detail",
                        kwargs={
                            "company_id": company_id,
                            "category_id": category_id,
                        },
                    ),
                    data=body,
                    format='json',
                )
                self.assertEqual(r.status_code, 200)

                # DBの値も更新されていることを確認する
                category = model_to_dict(
                    Category.objects.get(
                        id=category_id,
                        company_id=company_id,
                    ),
                )

                self.assertEqual(
                    {
                        "company": company_id,
                        "name": body.get("name", category["name"]),
                        "parent_category": body.get("parent_category_id", category["parent_category"]),
                    },
                    model_to_dict(
                        Category.objects.get(
                            id=category_id,
                            company_id=company_id,
                        ),
                    ),
                )

    def test_update_failures(self):
        """カテゴリ更新時の失敗ケースのテスト"""
        for name, status_code, company_id, category_id, body in [
            (
                "invalid company_id",
                400,
                "invalid",
                COMPANY_3_CATEGORY_1_1_ID,
                {},
            ),
            (
                "not found company_id",
                404,
                NOT_FOUND_COMPANY_ID,
                COMPANY_3_CATEGORY_1_1_ID,
                {},
            ),
            (
                "invalid category_id",
                400,
                COMPANY_3_ID,
                "invalid",
                {},
            ),
            (
                "not found category_id",
                404,
                COMPANY_3_ID,
                NOT_FOUND_COMPANY_ID,
                {},
            ),
            # 親を自分自身に変更
            (
                "company 3 category 1-1 update parent_category_id to itself",
                400,
                COMPANY_3_ID,
                COMPANY_3_CATEGORY_1_1_ID,
                {
                    "parent_category_id": COMPANY_3_CATEGORY_1_1_ID,
                },
            ),
            # 存在しない親カテゴリIDを指定
            (
                "invalid parent_category_id",
                400,
                COMPANY_3_ID,
                COMPANY_3_CATEGORY_1_1_ID,
                {
                    "parent_category_id": NOT_FOUND_COMPANY_ID,
                },
            ),
        ]:
            with self.subTest(msg=name):
                r = self.client.patch(
                    reverse(
                        "category-detail",
                        kwargs={
                            "company_id": company_id,
                            "category_id": category_id,
                        },
                    ),
                    data=body,
                    format='json',
                )
                self.assertEqual(status_code, r.status_code)


    def test_destroy_success(self):
        """カテゴリを削除するテスト"""
        for name, company_id, category_id in [
            ("company 2 category 1", COMPANY_2_ID, COMPANY_2_CATEGORY_1_ID),
            ("company 3 category 1-1", COMPANY_3_ID, COMPANY_3_CATEGORY_1_1_ID),
        ]:
            with self.subTest(msg=name):
                r = self.client.delete(
                    reverse(
                        "category-detail",
                        kwargs={
                            "company_id": company_id,
                            "category_id": category_id,
                        },
                    ),
                )
                self.assertEqual(r.status_code, 204)

                # もう一度同じリクエストを投げるとエラーになることを確認する
                r = self.client.delete(
                    reverse(
                        "category-detail",
                        kwargs={
                            "company_id": company_id,
                            "category_id": category_id,
                        },
                    ),
                )
                self.assertEqual(r.status_code, 404)

                # DBからも削除されていることを確認する
                self.assertFalse(
                    Category.objects.filter(
                        id=category_id,
                        company_id=company_id,
                    ).exists(),
                )

    def test_destroy_failures(self):
        """カテゴリ削除時の失敗ケースのテスト"""
        for name, status_code, company_id, category_id in [
            ("not found category_id", 404, COMPANY_1_ID, COMPANY_2_ID),
            ("category with children", 400, COMPANY_3_ID, COMPANY_3_CATEGORY_1_ID),
        ]:
            with self.subTest(msg=name, status_code=status_code):
                r = self.client.delete(
                    reverse(
                        "category-detail",
                        kwargs={
                            "company_id": company_id,
                            "category_id": category_id,
                        },
                    ),
                )
                self.assertEqual(r.status_code, status_code)