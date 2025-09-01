from django.urls import path
from . import views

app_name = 'account'
urlpatterns=[
    path('login', views.UserLogin.as_view(), name='user_login'),
    path('otplogin', views.OtpLoginView.as_view(), name='user_otp_login'),
    path('otp', views.CheckOtpView.as_view(), name='check_otp'),
    path('lohout', views.user_logout, name='user_logout')
]

