from django.urls import path
from . import views

urlpatterns = [
    path('', views.input_data, name='input_data'), 
    path('hasil/', views.predict_risk, name='predict_result'),
]