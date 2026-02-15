from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from .models import AppSettings
from django.shortcuts import get_object_or_404
from apps.core.utils.mixins import BaseResponseMixin
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from django.views.generic import TemplateView
from .serializers import AppSettingsSerializer

class APIGuideView(TemplateView):
    template_name = "guide/api-guide.html"


class TermsAndConditionsView(generics.RetrieveAPIView):
    serializer_class = AppSettingsSerializer

    def get(self, request, *args, **kwargs):
        """Get current Terms and Conditions"""
        try:
            terms = AppSettings.objects.filter(
                setting_type="terms_conditions"
            ).first()

            if not terms:
                return Response(
                    {
                        "success": False,
                        "message": "Terms and Conditions not found",
                        "data": None
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = self.get_serializer(terms)

            return Response(
                {
                    "success": True,
                    "message": "Terms and Conditions retrieved successfully",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"An error occurred: {str(e)}",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PrivacyPolicyView(generics.RetrieveAPIView):
    serializer_class = AppSettingsSerializer

    def get(self, request, *args, **kwargs):
        """Get current Privacy Policy"""
        try:
            privacy = AppSettings.objects.filter(
                setting_type="privacy_policy"
            ).first()

            if not privacy:
                return Response(
                    {
                        "success": False,
                        "message": "Privacy Policy not found",
                        "data": None
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = self.get_serializer(privacy)

            return Response(
                {
                    "success": True,
                    "message": "Privacy Policy retrieved successfully",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"An error occurred: {str(e)}",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AboutUsView(generics.RetrieveAPIView):
    serializer_class = AppSettingsSerializer

    def get(self, request, *args, **kwargs):
        """Get current About Us"""
        try:
            about_us = AppSettings.objects.filter(
                setting_type="about_us"
            ).first()

            if not about_us:
                return Response(
                    {
                        "success": False,
                        "message": "About Us not found",
                        "data": None
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = self.get_serializer(about_us)

            return Response(
                {
                    "success": True,
                    "message": "About Us retrieved successfully",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"An error occurred: {str(e)}",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class AppSettingsView(generics.ListAPIView):
    queryset = AppSettings.objects.all()
    serializer_class = AppSettingsSerializer


@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_setting(request, setting_type):
    """Update privacy policy, terms, about us"""
    content = request.data.get('content', '')

    setting, created = AppSettings.objects.get_or_create(
        setting_type=setting_type,
        defaults={'content': content}
    )

    if not created:
        setting.content = content
        setting.save()

    serializer = AppSettingsSerializer(setting)
    return Response(serializer.data)




def privacy_policy(request):
    setting = get_object_or_404(AppSettings, setting_type='privacy_policy')
    return render(request, 'app_settings/setting_detail.html', {
        'setting': setting,
        'title': 'Privacy Policy'
    })

def terms_conditions(request):
    setting = get_object_or_404(AppSettings, setting_type='terms_conditions')
    return render(request, 'app_settings/setting_detail.html', {
        'setting': setting,
        'title': 'Terms & Conditions'
    })

def about_us(request):
    setting = get_object_or_404(AppSettings, setting_type='about_us')
    return render(request, 'app_settings/setting_detail.html', {
        'setting': setting,
        'title': 'About Us'
    })









from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])  
def create_test_users(request):
    """
    Create or retrieve test users for all user types.
    POST body can be empty or contain custom emails/passwords.
    """
    
    # Default test users configuration
    default_users = {
        'superadmin': {
            'email': 'superadmin@test.com',
            'password': 'Admin@123',
            'is_superuser': True,
            'is_staff': True,
        },
        'event_admin': {
            'email': 'eventadmin@test.com',
            'password': 'Event@123',
            'event_admin': True,
        },
        'shop_admin': {
            'email': 'shopadmin@test.com',
            'password': 'Shop@123',
            'shop_admin': True,
        },
        'shopper': {
            'email': 'shopper@test.com',
            'password': 'Shopper@123',
            'shopper': True,
        }
    }
    
    users_config = request.data.get('users', default_users)
    
    created_users = []
    existing_users = []
    
    try:
        with transaction.atomic():
            for user_type, user_data in users_config.items():
                email = user_data.get('email')
                password = user_data.get('password', 'DefaultPass@123')
                
                # Try to get existing user
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'is_active': True,
                        'is_deleted': False,
                    }
                )
                
                if created:
                    user.set_password(password)
                    
                    if user_data.get('is_superuser'):
                        user.is_superuser = True
                        user.is_staff = True
                    if user_data.get('event_admin'):
                        user.event_admin = True
                    if user_data.get('shop_admin'):
                        user.shop_admin = True
                    if user_data.get('shopper'):
                        user.shopper = True
                    
                    user.save()
                    
                    created_users.append({
                        'type': user_type,
                        'email': email,
                        'password': password,
                        'id': user.id,
                        'status': 'created'
                    })
                else:
            
                    if user.is_deleted:
                        user.restore()
                    
                    existing_users.append({
                        'type': user_type,
                        'email': email,
                        'password': password,  
                        'id': user.id,
                        'status': 'already_exists'
                    })
        
        return Response({
            'success': True,
            'message': f'Created {len(created_users)} new users, found {len(existing_users)} existing users',
            'created': created_users,
            'existing': existing_users,
            'total_users': len(created_users) + len(existing_users)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)