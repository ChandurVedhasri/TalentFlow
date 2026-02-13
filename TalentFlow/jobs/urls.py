from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_job, name='create_job'),
    path('matches/', views.student_matches, name='matches'),
]
