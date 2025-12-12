from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    ShopperRegisterView,
    ShopAdminRegisterView,
    EventAdminRegisterView,
    LoginView,
    LogoutView,
    VerifyEmailView,
    ResendOTPView,
    PasswordResetRequestView,
    PasswordResetOTPVerifyView,
    ChangePasswordView,
    PasswordResetConfirmView,
    SocialAuthView,
    AccountSoftDeleteView,
    AccountRestoreView,
    ProfileUpdateView,
    VerifyEmailChangeView,
    ParmanentAccountDeleteView,
    UserProfileGenericView,
)

urlpatterns = [
    # Authentication endpoints
    path("shopper/register/", ShopperRegisterView.as_view(), name="shopper-register"),
    path("shopadmin/register/", ShopAdminRegisterView.as_view(), name="shopadmin-register"),
    path("eventadmin/register/", EventAdminRegisterView.as_view(), name="eventadmin-register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # # Password management
    path(
        "password/reset-request/",
        PasswordResetRequestView.as_view(),
        name="password-reset-request",
    ),
    path(
        "password/reset-verify-otp/",
        PasswordResetOTPVerifyView.as_view(),
        name="password-reset-verify-otp",
    ),
    path(
        "password/reset-confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm-view",
    ),

    path("password/change/", ChangePasswordView.as_view(), name="password-change"),

    path("account/delete/", AccountSoftDeleteView.as_view(), name="account-delete"),
    path("account/parmanent/delete/", ParmanentAccountDeleteView.as_view(), name="parmanent-delete"),
    path("account/restore/", AccountRestoreView.as_view(), name="account-restore"),
    path("profile/update/", ProfileUpdateView.as_view(), name="profile-update"),
    path(
        "profile/verify-email-change/",
        VerifyEmailChangeView.as_view(),
        name="verify-email-change",
    ),
    path("social-auth/", SocialAuthView.as_view(), name="social-auth"),

    path("profile/", UserProfileGenericView.as_view(), name="user-profile"),

]
