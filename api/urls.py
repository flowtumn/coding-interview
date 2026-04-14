from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views.category import CategoryView

router = DefaultRouter()

urlpatterns = [path("", include(router.urls))]

from django.http import HttpResponse

urlpatterns = [
    path("", include(router.urls)),
    path("company/<str:company_id>/categories/", CategoryView.as_view(), name="category-tree"),
]