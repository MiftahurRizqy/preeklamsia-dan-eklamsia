from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('tentang-kami/', views.about_view, name='about'),
]