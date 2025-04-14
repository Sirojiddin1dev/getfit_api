from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('signup/', views.signup_api, name='signup_api'),
    path('login/', views.login_api, name='login_api'),
    path('logout/', views.logout_api, name='logout_api'),
    path('videos/', views.video_list_api, name='video_list_api'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('admin/videos/', views.video_list),
    path('admin/videos/create/', views.video_create),
    path('admin/videos/<int:pk>/', views.video_detail),
    path('admin/videos/<int:pk>/update/', views.video_update),
    path('admin/videos/<int:pk>/delete/', views.video_delete),
    path('admin/books/', views.book_list),
    path('admin/books/create/', views.book_create),
    path('admin/books/<int:pk>/', views.book_detail),
    path('admin/books/<int:pk>/update/', views.book_update),
    path('admin/books/<int:pk>/delete/', views.book_delete),
    path('admin/news/', views.news_list),
    path('admin/news/create/', views.news_create),
    path('admin/news/<int:pk>/', views.news_detail),
    path('admin/news/<int:pk>/update/', views.news_update),
    path('admin/news/<int:pk>/delete/', views.news_delete),
]
