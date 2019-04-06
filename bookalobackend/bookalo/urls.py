from django.contrib import admin
from django.urls import path, include
from bookalo import views
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    path(r'api/login', views.Login),
    path(r'api/generic_product_view', views.GenericProductView),
    path(r'api/get_user_profile', views.GetUserProfile),
    path(r'api/search_product', views.SearchProduct),
    path(r'api/filter_product', views.FilterProduct),
    path(r'api/get_user_products', views.GetUserProducts),
    path(r'api/create_product', views.CreateProduct),
    path(r'api/create_report', views.CreateReport),
    path(r'api/prueba', views.prueba),
]
