"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import re_path
from django.contrib import admin
from collector import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    #reference : https://docs.djangoproject.com/en/3.0/ref/urls/
    # url(regex, view, kwargs=None, name=None)¶
    # This function is an alias to django.urls.re_path(). It’s likely to be deprecated in a future release.
    #url() -> re_path()

    # url(r'^collector/', views.collector),
    # url(r'^state/', views.state),
    # url(r'^init/', views.init),
    # url(r'^command/', views.command),
    # url(r'^graph/', views.graph),
    # url(r'^$', views.main),
    # url(r'error/', views.error),

    re_path(r'^collector/', views.collector),
    re_path(r'^state/', views.state),
    re_path(r'^init/', views.init),
    re_path(r'^command/', views.command),
    re_path(r'^graph/', views.graph),
    re_path(r'^$', views.main),
    re_path(r'error/', views.error),
    re_path(r'^admin/', admin.site.urls)
] + static(settings.STATIC_URL, document_ROOT=settings.STATIC_URL)
