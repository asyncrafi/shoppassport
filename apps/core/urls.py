from django.urls import path, include
from .views import *



urlpatterns = [

    path("guide/", APIGuideView.as_view(), name="api-guide;"),
    path('create-test-users/', create_test_users, name='create_test_users'),

    path('terms-and-conditions/', TermsAndConditionsView.as_view(), name='terms-and-conditions'),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy-policy'),
    path('about-us/', AboutUsView.as_view(), name='about-us'),

    path('settings/', AppSettingsView.as_view(), name='settings'),
    path('settings/<str:setting_type>/', update_setting, name='update-setting'),

]

