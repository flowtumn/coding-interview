import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
from api.models import Category, Company
from api.serializers import CategoriesSerializer


InvalidCompanyID = ValidationError("Invalid company_id")
InvalidParentCategoryID = ValidationError("Invalid parent_category_id")


def parse_must_uuid(name: str, v: str, exception: Exception) -> uuid.UUID:
    try:
        return uuid.UUID(v)
    except ValueError:
        raise exception


def get_company(
    company_id: uuid.UUID,
    exception: Exception = InvalidCompanyID,
) -> Company:
    try:
        return Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        raise exception


def get_category(
    category_id: uuid.UUID,
    company_id: uuid.UUID,
    exception: Exception,
) -> Category:
    try:
        return Category.objects.get(id=category_id, company_id=company_id)
    except Category.DoesNotExist:
        raise exception


class CategoryView(APIView):
    @staticmethod
    def convert_to_response(categories: list[dict]) -> list[dict]:
        category_map = {
            str(category["id"]): {
                **category,
                "children": [],
            }
            for category in categories
        }

        tree = []
        for category in categories:
            parent_id = category["parent_category_id"]
            current = category_map[str(category["id"])]

            # 親なし
            if parent_id is None:
                tree.append(current)
                continue
        
            parent = category_map.get(str(parent_id))
            if parent:
                parent["children"].append(current)
            else:
                # 親が設定されているが、見つからなかった。異常なデータだが、とりあえずツリーのルートに置いておく。
                tree.append(current)

        return tree

    def get(self, request: Request, company_id: str, *args, **kwargs) -> Response:
        company = get_company(
            company_id=parse_must_uuid(
                name="company_id",
                v=company_id,
                exception=InvalidCompanyID,
            ),
        )

        serializer = CategoriesSerializer(
            Category.objects.filter(company_id=company.id),
            many=True,
        )

        return Response(
            status=200,
            data={
                "categories": self.convert_to_response(categories=serializer.data),
            },
        )

    def post(self, request: Request, company_id: str, *args, **kwargs) -> Response:
        company = get_company(
            company_id=parse_must_uuid(
                name="company_id",
                v=company_id,
                exception=InvalidCompanyID,
            ),
        )

        parent_category_id: uuid.UUID | None = parse_must_uuid(
            name="parent_category_id",
            v=request.data.get("parent_category_id"),
            exception=InvalidParentCategoryID,
        ) if request.data.get("parent_category_id") else None
        if parent_category_id:
            # parent_category_idの存在確認
            get_category(
                category_id=parent_category_id,
                company_id=company.id,
                exception=InvalidParentCategoryID,
            )

        new_category_id = uuid.uuid4()
        Category.objects.create(
            id=new_category_id,
            company_id=company.id,
            name=request.data.get("name"),
            parent_category_id=parent_category_id,
        )

        return Response(
            status=201,
            data={
                "id": str(new_category_id),
                "name": request.data.get("name"),
                "parent_category_id": parent_category_id,
            },
        )

    def put(self, request: Request, *args, **kwargs) -> Response:
        return Response("This is the category tree view.")

    def delete(self, request: Request, *args, **kwargs) -> Response:
        return Response("This is the category tree view.")