import uuid
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from api.models import Category, Company
from api.serializers import CategoriesSerializer


InvalidCompanyID = ValidationError("Invalid company_id")
InvalidCategoryID = ValidationError("Invalid category_id")
InvalidParentCategoryID = ValidationError("Invalid parent_category_id")


def parse_must_uuid(value: str, exception: Exception) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise exception


class CategoryView(APIView):
    @staticmethod
    def convert_to_response(categories: list[dict]) -> list[dict]:
        """Categoryのリストを、親子関係を表すツリー構造に変換します。"""
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

    def initial(self, request: Request,*args, **kwargs):
        super().initial(request, *args, **kwargs)
        
        company_id = parse_must_uuid(
            value=kwargs.get('company_id'),
            exception=InvalidCompanyID,
        )
        self.company = get_object_or_404(
            Company,
            id=company_id,
        )

    def get(self, request: Request, category_id: str | None = None, **kwargs) -> Response:
        """Categoryの一覧、もしくは特定のCategory(子を込み)を取得します。"""
        if category_id:
            _category_id = parse_must_uuid(
                value=category_id,
                exception=InvalidCategoryID,
            )

            serializer = CategoriesSerializer(
                Category.objects.filter(
                    Q(id=_category_id) | Q(parent_category_id=_category_id),
                    company_id=self.company.id,
                ),
                many=True,
                context={
                    "company_id": self.company.id,
                },
            )

            if not serializer.data:
                raise Http404("Category not found.")

            data = self.convert_to_response(categories=serializer.data)

            # category_idが指定されているので、配列の大きさは必ず1件
            # 1件で無いときは、内部の処理に問題があるため 500 エラーを返すのは意図しています
            assert len(data) == 1

            return Response(
                status=200,
                data=data[0]
            )
        else:
            # SQLの発行は一回に留めるため全件取得。
            serializer = CategoriesSerializer(
                Category.objects.filter(company_id=self.company.id),
                many=True,
                context={
                    "company_id": self.company.id,
                },
            )

            return Response(
                status=200,
                data={
                    "categories": self.convert_to_response(categories=serializer.data),
                },
            )
        
    def post(self, request: Request, **kwargs) -> Response:
        """Categoryの作成を行います。
        Requestパラメーター例:

        {
          "name": "カテゴリ名",
          "parent_category_id": "親カテゴリID (null可)"
        }
        """

        serializer = CategoriesSerializer(
            data=request.data,
            context={
                "company_id": self.company.id,
            },
        )
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                serializer.save(company=self.company)
            return Response(
                serializer.data,
                status=201,
            )
        except IntegrityError:
            return Response(status=409)

    def patch(self, request: Request, category_id: str, **kwargs) -> Response:
        """Categoryの更新を行います。
        値が null の場合は、フィールドをnullに更新します。
        プロパティが存在しないときは、そのフィールドは更新されません。
        Requestパラメーター例:

        {
          "name": "カテゴリ名",
          "parent_category_id": "親カテゴリID"
        }
        """

        category = get_object_or_404(
            Category,
            id=parse_must_uuid(
                value=category_id,
                exception=InvalidCategoryID,
            ),
            company_id=self.company.id,
        )

        serializer = CategoriesSerializer(
            category,
            data=request.data,
            partial=True, # 部分更新を許可
            context={
                "company_id": self.company.id,
            },
        )

        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                serializer.save()
            
            return Response(serializer.data, status=200)
        except IntegrityError:
            return Response(status=409)

    def delete(
        self,
        request: Request,
        category_id: str,
        **kwargs,
    ) -> Response:
        """Categoryの削除を行います。子どもがいるカテゴリは削除できません。"""
        category = get_object_or_404(
            Category,
            id=parse_must_uuid(
                value=category_id,
                exception=InvalidCategoryID,
            ),
            company_id=self.company.id,
        )

        # 子どもがいるカテゴリは削除できない
        if Category.objects.filter(parent_category_id=category.id).exists():
            return Response(status=400, data={"detail": "Cannot delete category with children."})

        with transaction.atomic():
            category.delete()

        return Response(status=204)
