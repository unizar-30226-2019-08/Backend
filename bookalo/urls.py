from django.contrib import admin
from django.urls import path, include
from django.conf.urls import re_path
from bookalo import views
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    re_path(r'^$', views.index),
    path(r'api/login', views.Login),
    re_path(r'generic_product_view', views.GenericProductView),
    re_path(r'api/get_user_profile', views.GetUserProfile),
    path(r'api/filter_product', views.FilterProduct),
    path(r'api/get_user_products', views.GetUserProducts),
    path(r'api/create_product', views.CreateProduct),
    path(r'api/create_report', views.CreateReport),
    path(r'api/create_chat', views.CreateChat),
    path(r'api/delete_product', views.DeleteProduct),
    path(r'api/like_product', views.LikeProduct),
    path(r'api/get_chats', views.GetChats),
    path(r'api/send_message', views.SendMessage),
    path(r'api/rate_user', views.SendRating),
    re_path(r'privacypolicy', views.PrivacyPolicy),
    re_path(r'create_product', views.CreateProductRender),
    path(r'api/get_pending_notifications', views.GetPendingNotifications),
    path(r'api/get_ratings', views.GetRatings),
    path(r'api/get_user_info', views.GetUserInfo),
    path(r'api/get_messages', views.GetMessages),
    path(r'api/get_tags', views.GetTagList),
    path(r'api/sell_product', views.SellProduct),
    path(r'api/get_favorites', views.GetLikedProducts),
    re_path(r'api/edit_product_render', views.EditProductRender),
    path(r'api/edit_product', views.EditProduct),
    path(r'api/marcar_vendido', views.Vender_producto),
    re_path(r'logout', views.Logout),
    path(r'api/delete_pending', views.ClearPendingMessages),
    path(r'api/get_info_isbn', views.GetInfoISBN),
    re_path(r'mobile_app', views.MobileRedirect),
]
