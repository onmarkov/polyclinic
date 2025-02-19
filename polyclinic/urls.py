"""polyclinic URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, include
from registry.forms import BootstrapAuthenticationForm
from registry.views import HomeView


urlpatterns = [
    path('session_security/', include('session_security.urls')),
    path('', HomeView.as_view(), name='home'),
    path('registry/', include('registry.urls')),
    path('login/', LoginView.as_view(
        template_name='login.html',
        authentication_form=BootstrapAuthenticationForm, extra_context={'title': 'Вход'}), name='login'),
    path('logout', LogoutView.as_view(next_page='login'), name='logout'),
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('admin/', admin.site.urls),
]
