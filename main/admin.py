from django.contrib import admin
from .models import User, UserDevice, Video


admin.site.register(User)
admin.site.register(UserDevice)
admin.site.register(Video)
