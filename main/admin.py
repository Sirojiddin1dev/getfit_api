from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserDevice, Video, Book, News


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {
            'fields': ('phone_number', 'status', 'course_month')
        }),
    )
    list_display = ('username', 'phone_number', 'status', 'course_month', 'is_staff')
    list_filter = ('status', 'course_month', 'is_staff', 'is_superuser')
    search_fields = ('username', 'phone_number')
    ordering = ('-date_joined',)
    readonly_fields = ('last_login', 'date_joined')


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_name', 'device_id', 'last_login')
    search_fields = ('user__username', 'device_name', 'device_id')
    list_filter = ('last_login',)
    ordering = ('-last_login',)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('video_name', 'category')
    search_fields = ('video_name',)
    list_filter = ('category',)
    ordering = ('video_name',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)