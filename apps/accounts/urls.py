from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts.views import *
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
    path("profile/update/", ProfileUpdateView.as_view(), name="profile-update"),
    path(
        "profile/verify-email-change/",
        VerifyEmailChangeView.as_view(),
        name="verify-email-change",
    ),
    path("social-auth/", SocialAuthView.as_view(), name="social-auth"),

    path("profile/", UserProfileGenericView.as_view(), name="user-profile"),
]

urlpatterns += [

    # User Management
    path('admin/users/', AllUsersView.as_view(), name='all-users'),
    path('admin/users/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('admin/users/stats/', UserStatsView.as_view(), name='user-stats'),
    
    # User Actions
    path('admin/users/block/', BlockUserView.as_view(), name='block-user'),
    path('admin/users/unblock/', UnblockUserView.as_view(), name='unblock-user'),
    path("admin/restore/", AccountRestoreView.as_view(), name="account-restore"),

]