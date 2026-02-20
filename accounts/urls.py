from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'
urlpatterns = [
    path('registrace/', views.register, name='register'),
    path('prihlaseni/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('odhlaseni/', auth_views.LogoutView.as_view(), name='logout'),
    path('profil/', views.profile, name='profile'),
]
