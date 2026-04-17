from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.views.category import CategoryView

router = DefaultRouter()

urlpatterns = [path("", include(router.urls))]

urlpatterns = [
    path("", include(router.urls)),
    # GET, POST
    path("company/<str:company_id>/categories/", CategoryView.as_view(), name="categories"),
    # GET, PATCH, DELETE
    path("company/<str:company_id>/categories/<str:category_id>/", CategoryView.as_view(), name="category-detail"),
]