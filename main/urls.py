from django.urls import path
from .views import *

urlpatterns = [
    path('get-user/', GetUser.as_view()),
    path('update-user/', UpdateUser.as_view()),
    path('delete-user/', DeleteUser.as_view()),

    path('signin/', signin_view),
    path('signup/', signup_view),
    path('logout/', logout_view),

    path('devices/', UserDeviceListView.as_view(), name='device-list'),
    path('devices/<str:device_id>/', delete_device_view),
    path('video/', api_video),
    path('get/', get_video),
]
