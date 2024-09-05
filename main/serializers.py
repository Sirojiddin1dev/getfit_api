from rest_framework import serializers
from .models import *


class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class VideoSerializers(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = '__all__'


class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = ['device_id', 'device_name', 'last_login']
