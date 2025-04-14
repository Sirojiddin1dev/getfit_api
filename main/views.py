from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth import login, authenticate, logout
from main.serializers import *
from django.utils import timezone
import hashlib
import httpagentparser
from rest_framework_simplejwt.tokens import RefreshToken
import requests
import json
from .permissions import IsStaff
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from main.models import Video, Book, News
from main.serializers import VideoSerializer, BookSerializer, NewsSerializer
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


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

@swagger_auto_schema(
    method='post',
    operation_description="Foydalanuvchini ro'yxatdan o'tkazadi.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['phone_number', 'password', 'device_id'],
        properties={
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, example='+998901234567'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, example='parol123'),
            'device_id': openapi.Schema(type=openapi.TYPE_STRING, example='abcd1234'),
            'device_name': openapi.Schema(type=openapi.TYPE_STRING, example='Redmi Note 11'),
        },
    ),
    responses={
        201: openapi.Response('Ro‘yxatdan o‘tish muvaffaqiyatli', examples={'application/json': {
            'message': 'Foydalanuvchi muvaffaqiyatli ro‘yxatdan o‘tdi. Siz hozircha blokdasiz.',
            'access': 'jwt-access-token',
            'refresh': 'jwt-refresh-token'
        }}),
        400: 'Xatolik'
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def signup_api(request):
    phone_number = request.data.get('phone_number')
    password = request.data.get('password')
    device_id = request.data.get('device_id')
    device_name = request.data.get('device_name') or "unknown"

    if not phone_number or not password or not device_id:
        return Response({"error": "Telefon raqami, parol va qurilma ID talab qilinadi."}, status=status.HTTP_400_BAD_REQUEST)

    phone_validator = RegexValidator(
        regex=r'^\+998\d{9}$',
        message='Telefon raqami +998XXXXXXXXX formatida bo‘lishi kerak.'
    )

    try:
        phone_validator(phone_number)

        user = User(username=phone_number, phone_number=phone_number, status='Block')
        user.set_password(password)
        user.save()

        UserDevice.objects.create(user=user, device_id=device_id, device_name=device_name)

        login(request, user)
        tokens = get_tokens_for_user(user)

        return Response({
            'message': 'Foydalanuvchi muvaffaqiyatli ro‘yxatdan o‘tdi. Siz hozircha blokdasiz.',
            'access': tokens['access'],
            'refresh': tokens['refresh']
        }, status=status.HTTP_201_CREATED)

    except ValidationError:
        return Response({'error': 'Telefon raqamni +998XXXXXXXXX formatida kiriting'}, status=status.HTTP_400_BAD_REQUEST)
    except IntegrityError:
        return Response({'error': 'Bu telefon raqami allaqachon roʻyxatdan oʻtgan.'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_description="Foydalanuvchini tizimga kiritadi.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['phone_number', 'password', 'device_id'],
        properties={
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, example='+998901234567'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, example='parol123'),
            'device_id': openapi.Schema(type=openapi.TYPE_STRING, example='abcd1234'),
            'device_name': openapi.Schema(type=openapi.TYPE_STRING, example='Redmi Note 11'),
        },
    ),
    responses={
        200: openapi.Response('Muvaffaqiyatli login', examples={'application/json': {
            'message': 'Muvaffaqiyatli tizimga kirildi.',
            'access': 'jwt-access-token',
            'refresh': 'jwt-refresh-token'
        }}),
        400: 'Login xatosi',
        403: 'Foydalanuvchi bloklangan'
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    phone_number = request.data.get('phone_number')
    password = request.data.get('password')
    device_id = request.data.get('device_id')
    device_name = request.data.get('device_name') or "unknown"

    if not phone_number or not password or not device_id:
        return Response({"error": "Telefon raqami, parol va qurilma ID talab qilinadi."}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=phone_number, password=password)

    if user is not None:
        if user.status != 'Active':
            return Response({'error': "Siz bloklangansiz. Juda ko'p qurilmalardan tizimga kirishga uringansiz yoki hali darslikni sotib olmagansiz"},
                            status=status.HTTP_403_FORBIDDEN)

        if not user.is_superuser:
            device = UserDevice.objects.filter(user=user, device_id=device_id).first()

            if device:
                device.last_login = timezone.now()
                device.save()
            else:
                devices = UserDevice.objects.filter(user=user)
                if devices.count() >= 5:
                    user.status = 'Block'
                    user.save()
                    devices.delete()
                    return Response({'error': "Siz bloklangansiz. Juda ko'p moslamalarda tizimga kirishga harakat qildingiz."},
                                    status=status.HTTP_403_FORBIDDEN)

                UserDevice.objects.create(user=user, device_id=device_id, device_name=device_name)

        login(request, user)

        tokens = get_tokens_for_user(user)

        return Response({
            'message': "Muvaffaqiyatli tizimga kirildi.",
            'access': tokens['access'],
            'refresh': tokens['refresh'],
        }, status=status.HTTP_200_OK)

    return Response({'error': "Telefon raqami yoki parol noto'g'ri kiritilgan."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    logout(request)
    return Response({'message': "Muvaffaqiyatli chiqildi."}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def video_list_api(request):
    user = request.user

    # Avtomatik status tekshirish
    if user.course_expire_date and user.course_expire_date < timezone.now():
        if user.status != 'Block':
            user.status = 'Block'
            user.save()

    # Bloklangan bo‘lsa, kirish taqiqlanadi
    if user.status == 'Block':
        return Response({'error': 'Foydalanuvchi bloklangan.'}, status=status.HTTP_403_FORBIDDEN)

    all_videos = Video.objects.all()
    modules = {}

    for video in all_videos:
        if video.category not in modules:
            modules[video.category] = {
                'name': video.category,
                'videos': []
            }

        url = f"https://dev.vdocipher.com/api/videos/{video.video_id}/otp"
        payload = json.dumps({"whitelisthref": "vdocipher.com"})
        headers = {
            'Authorization': "Apisecret oCxi0FTzAXOZxDPMddQcFZ3NQ3NpsIrtByd2fbghtwvdgwAcNsl0u3DhjN2VK3Al",
            'Content-Type': "application/json",
            'Accept': "application/json"
        }

        try:
            response = requests.post(url, data=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                modules[video.category]['videos'].append({
                    'video_id': video.video_id,
                    'video_name': video.video_name,
                    'otp': result['otp'],
                    'playbackInfo': result['playbackInfo']
                })
        except Exception as e:
            print(f"Error fetching OTP for video {video.video_id}: {e}")

    return Response({'modules': list(modules.values())}, status=status.HTTP_200_OK)




def staff_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# --- Video CRUD ---
@swagger_auto_schema(method='get', responses={200: VideoSerializer(many=True)})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@staff_required
def video_list(request):
    videos = Video.objects.all()
    serializer = VideoSerializer(videos, many=True)
    return Response(serializer.data)


@swagger_auto_schema(method='post', request_body=VideoSerializer, responses={201: VideoSerializer})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@staff_required
def video_create(request):
    serializer = VideoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='get', responses={200: VideoSerializer})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@staff_required
def video_detail(request, pk):
    video = get_object_or_404(Video, pk=pk)
    serializer = VideoSerializer(video)
    return Response(serializer.data)


@swagger_auto_schema(method='put', request_body=VideoSerializer, responses={200: VideoSerializer})
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@staff_required
def video_update(request, pk):
    video = get_object_or_404(Video, pk=pk)
    serializer = VideoSerializer(video, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='delete', responses={204: 'No Content'})
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@staff_required
def video_delete(request, pk):
    video = get_object_or_404(Video, pk=pk)
    video.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# --- Book CRUD ---
@swagger_auto_schema(method='get', responses={200: BookSerializer(many=True)})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @staff_required
def book_list(request):
    books = Book.objects.all()
    serializer = BookSerializer(books, many=True)
    return Response(serializer.data)


@swagger_auto_schema(method='post', request_body=BookSerializer, responses={201: BookSerializer})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@staff_required
def book_create(request):
    serializer = BookSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='get', responses={200: BookSerializer})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @staff_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    serializer = BookSerializer(book)
    return Response(serializer.data)


@swagger_auto_schema(method='put', request_body=BookSerializer, responses={200: BookSerializer})
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@staff_required
def book_update(request, pk):
    book = get_object_or_404(Book, pk=pk)
    serializer = BookSerializer(book, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='delete', responses={204: 'No Content'})
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@staff_required
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# --- News CRUD ---
@swagger_auto_schema(method='get', responses={200: NewsSerializer(many=True)})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @staff_required
def news_list(request):
    news = News.objects.all()
    serializer = NewsSerializer(news, many=True)
    return Response(serializer.data)


@swagger_auto_schema(method='post', request_body=NewsSerializer, responses={201: NewsSerializer})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@staff_required
def news_create(request):
    serializer = NewsSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='get', responses={200: NewsSerializer})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
# @staff_required
def news_detail(request, pk):
    news = get_object_or_404(News, pk=pk)
    serializer = NewsSerializer(news)
    return Response(serializer.data)


@swagger_auto_schema(method='put', request_body=NewsSerializer, responses={200: NewsSerializer})
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@staff_required
def news_update(request, pk):
    news = get_object_or_404(News, pk=pk)
    serializer = NewsSerializer(news, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='delete', responses={204: 'No Content'})
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@staff_required
def news_delete(request, pk):
    news = get_object_or_404(News, pk=pk)
    news.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(method='put', request_body=UserUpdateSerializer, responses={200: UserUpdateSerializer})
@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsStaff])
def update_user_status_course_month(request, pk):
    user = get_object_or_404(User, pk=pk)
    serializer = UserUpdateSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        course_month = serializer.validated_data.get('course_month', None)

        # Agar course_month kiritilgan bo‘lsa, statusni Active va expire date qo‘shamiz
        if course_month is not None:
            now = timezone.now()
            months_map = {
                0: 1,
                1: 3,
                2: 6,
                3: 12
            }
            months = months_map.get(course_month, 0)
            expire_date = now + timedelta(days=30 * months)
            user.course_expire_date = expire_date
            user.status = 'Active'

        serializer.save()
        return Response(UserUpdateSerializer(user).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
