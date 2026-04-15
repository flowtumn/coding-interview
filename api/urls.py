from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views.category import CategoryView

router = DefaultRouter()

urlpatterns = [path("", include(router.urls))]

from django.http import HttpResponse

urlpatterns = [
    path("", include(router.urls)),
    # GET, POST
    path("company/<str:company_id>/categories/", CategoryView.as_view(), name="categories"),
    # GET, PUT, DELETE
    path("company/<str:company_id>/categories/<str:category_id>/", CategoryView.as_view(), name="category-detail"),
]