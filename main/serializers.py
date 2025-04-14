from rest_framework import serializers
from .models import *
from django.contrib.auth import get_user_model

User = get_user_model()
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'phone_number', 'status', 'course_month', 'course_expire_date']

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['status', 'course_month']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'phone_number',
            'status',
            'course_month',
            'is_active',
            'date_joined',
            'last_login',
        ]
        read_only_fields = ['id', 'is_active', 'date_joined', 'last_login']



class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = '__all__'

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = '__all__'

class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = ['device_id', 'device_name', 'last_login']
