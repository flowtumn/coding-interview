from django.contrib import admin
from api.models import Company

# 企業登録は管理画面から実施する
admin.site.register(Company)
