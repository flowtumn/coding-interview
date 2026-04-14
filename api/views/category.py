import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from api.models import Category, Company


InvalidCompanyID = ValidationError("Invalid company_id")


def to_uuid(name: str, v: str) -> uuid.UUID:
    try:
        return uuid.UUID(v)
    except ValueError:
        raise InvalidCompanyID

def get_company(
    company_id: uuid.UUID,
    exception: Exception = InvalidCompanyID,
) -> Company:
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        raise exception

    return company

class CategoryView(APIView):
    def get(self, request: Request, company_id: str, *args, **kwargs) -> Response:
        get_company(
            company_id=to_uuid(
                name="company_id",
                v=company_id,
            ),
        )

        category = Category.objects.filter(company_id=company_id)
        return Response(
            status=200,
            data={
                "categories": [
                    {
                        "id": str(c.id),
                        "name": c.name,
                        "parent_category_id": str(c.parent_category_id) if c.parent_category_id else None,
                        "created_at": c.created_at.isoformat(),
                        "updated_at": c.updated_at.isoformat(),
                    }
                    for c in category
                ]
            },
        )

    def post(self, request: Request, company_id: str, *args, **kwargs) -> Response:
        get_company(
            company_id=to_uuid(
                name="company_id",
                v=company_id,
            ),
        )

        new_category_id = uuid.uuid4()
        Category.objects.create(
            id=new_category_id,
            company_id=company_id,
            name=request.data.get("name"),
            parent_category_id=request.data.get("parent_category_id"),
        )

        return Response(
            status=201,
            data={
                "id": str(new_category_id),
                "name": request.data.get("name"),
                "parent_category_id": request.data.get("parent_category_id"),
            },
        )

    def put(self, request: Request, *args, **kwargs) -> Response:
        return Response("This is the category tree view.")

    def delete(self, request: Request, *args, **kwargs) -> Response:
        return Response("This is the category tree view.")