from django.shortcuts import render
from main.models import User, UserDevice, Video
from main.serializers import UserSerializers, UserDeviceSerializer
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from django.contrib.auth import login, logout, authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView, ListCreateAPIView, UpdateAPIView, DestroyAPIView
from .tokens import *
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404, Http404
import httpagentparser
import hashlib
from rest_framework import status
import requests
import json
import requests


@api_view(['GET'])
def get_video(request):
    url = "https://dev.vdocipher.com/api/videos/a06c8ec5549e42e2a9cf9e76006d61d1"

    headers = {
        'Authorization': "Apisecret oPAn8FitJWIAAXcP0ZKaa1pWDHahJBIgTOc9v3KYz7M2SlLswoxFhJUbAXSaDDKm",
        'Content-Type': "application/json",
        'Accept': "application/json"
    }

    response = requests.request("GET", url, headers=headers)

    return Response(response.text)

@api_view(['POST'])
def api_video(request):
    # Fetch all valid video_ids from the database
    valid_video_ids = [video.video_id for video in Video.objects.all()]

    if not valid_video_ids:
        return Response({"error": "No valid video IDs found in the database"}, status=status.HTTP_404_NOT_FOUND)

    # Initialize a list to collect the results
    results = []

    # Loop through each valid video_id
    for video_id in valid_video_ids:
        url = f"https://dev.vdocipher.com/api/videos/{video_id}/otp"

        # Prepare the payload and headers
        payload = json.dumps({"whitelisthref": "getfit.uz"})
        headers = {
            'Authorization': "Apisecret OiQICe19GCEiAXzHj3QWsRfMlyucRiVOTqi1geoVDvZUZk6O333HRX2W3JKDv6Ed",
            'Content-Type': "application/json",
            'Accept': "application/json"
        }

        try:
            # Send the POST request to get the OTP
            response = requests.request('POST', url, data=payload, headers=headers)

            # Handle the response
            if response.status_code == 200:
                result = response.json()
                result['video_id'] = video_id  # Add video_id to the result
                results.append(result)
            else:
                results.append({"video_id": video_id, "error": response.text})

        except requests.exceptions.ProxyError as e:
            results.append({"video_id": video_id, "error": "ProxyError occurred", "details": str(e)})
        except Exception as e:
            results.append({"video_id": video_id, "error": "An error occurred", "details": str(e)})

    # Return the combined results as JSON response
    return Response(results, status=status.HTTP_200_OK)




def get_device_id(request):
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    device_string = f"{user_agent}_{ip_address}"
    device_id = hashlib.md5(device_string.encode('utf-8')).hexdigest()
    return device_id


def get_device_name(user_agent):
    parsed_data = httpagentparser.detect(user_agent)
    os_info = parsed_data.get('os', {})
    browser_info = parsed_data.get('browser', {})
    device_name = os_info.get('name', 'Unknown OS')
    device_version = os_info.get('version', '')
    browser_name = browser_info.get('name', 'Unknown Browser')
    browser_version = browser_info.get('version', '')
    return f"{device_name} {device_version} - {browser_name} {browser_version}"


@api_view(['POST'])
def signin_view(request):
    phone_number = request.data.get('phone_number')
    password = request.data.get('password')

    try:
        usr = authenticate(username=phone_number, password=password)
        if usr is not None:
            device_count = UserDevice.objects.filter(user=usr).count()

            if device_count < 3:
                login(request, usr)

                device_id = get_device_id(request)
                device_name = get_device_name(request.META['HTTP_USER_AGENT'])

                user_device, created = UserDevice.objects.get_or_create(
                    user=usr,
                    device_id=device_id,
                    defaults={'device_name': device_name}
                )

                if device_count > 3:
                    oldest_device = UserDevice.objects.filter(user=usr).order_by('last_login').first()
                    oldest_device.delete()

                tokens = get_tokens_for_user(usr)
                status_code = 200
                data = {
                    'status': status_code,
                    'phone_number': phone_number,
                    'token': tokens,
                    'device': UserDeviceSerializer(user_device).data,
                }
            else:
                status_code = 403
                message = "The number of devices is sufficient"
                data = {
                    'status': status_code,
                    'message': message,
                }
        else:
            status_code = 403
            message = "Invalid Password or Phone Number!"
            data = {
                'status': status_code,
                'message': message,
            }
    except User.DoesNotExist:
        status_code = 404
        message = 'This User is not defined!'
        data = {
            'status': status_code,
            'message': message,
        }
    except Exception as err:
        return Response({'error': str(err)}, status=500)
    return Response(data, status=status_code)


@api_view(['POST'])
def signup_view(request):
    # Ma'lumotlarni olish
    phone_number = request.data.get('phone_number')
    first_name = request.data.get('first_name')
    password = request.data.get('password')

    # Majburiy maydonlar to'ldirilganligini tekshirish
    if not phone_number or not password:
        return Response({"error": "Phone number and password are required."}, status=400)

    try:
        # Telefon raqamini username sifatida ishlatish
        new_user = User.objects.create_user(
            first_name=first_name,
            username=phone_number,  # Telefon raqamini username sifatida belgilash
            phone_number=phone_number,
            password=password
        )
        # Serializatsiya qilish
        ser = UserSerializers(new_user)
        # Javob qaytarish
        return Response(ser.data, status=201)

    except Exception as e:
        # Xatolik holatida javob qaytarish
        return Response({"error": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    device_id = get_device_id(request)
    device_id = UserDevice.objects.filter(device_id=device_id)
    device_id.delete()
    logout(request)
    return Response({'data':'sucses'})


class GetUser(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializers


class UpdateUser(UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializers


class DeleteUser(DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializers


def get_device_name(user_agent):
    parsed_data = httpagentparser.detect(user_agent)
    os_info = parsed_data.get('os', {})
    browser_info = parsed_data.get('browser', {})
    device_name = os_info.get('name', 'Unknown OS')
    device_version = os_info.get('version', '')
    browser_name = browser_info.get('name', 'Unknown Browser')
    browser_version = browser_info.get('version', '')
    return f"{device_name} {device_version} - {browser_name} {browser_version}"


class UserDeviceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        devices = UserDevice.objects.filter(user=request.user)
        serializer = UserDeviceSerializer(devices, many=True)
        return Response(serializer.data)

    def post(self, request):
        device_id = request.data.get('device_id')
        device_name = get_device_name(request.META['HTTP_USER_AGENT'])

        user_device, created = UserDevice.objects.get_or_create(
            user=request.user,
            device_id=device_id,
            defaults={'device_name': device_name}
        )

        if not created:
            return Response({"message": "Device already exists."}, status=400)

        # Qurilma sonini tekshirish va eski qurilmani o'chirish
        device_count = UserDevice.objects.filter(user=request.user).count()
        if device_count > 3:
            oldest_device = UserDevice.objects.filter(user=request.user).order_by('last_login').first()
            oldest_device.delete()

        serializer = UserDeviceSerializer(user_device)
        return Response(serializer.data, status=201)


@api_view(['DELETE'])
def delete_device_view(request, device_id):
    try:
        # Qurilmani ID bo'yicha olish
        device = UserDevice.objects.get(device_id=device_id)
        device.delete()
        return Response({"message": "Device deleted successfully."}, status=200)
    except UserDevice.DoesNotExist:
        raise Http404("No UserDevice matches the given query.")
    except Exception as err:
        return Response({"error": str(err)}, status=500)