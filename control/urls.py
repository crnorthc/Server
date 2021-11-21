from django.urls import path
from .views import *

urlpatterns = [
    path('create', CreateAdmin.as_view()),
    path('login', Login.as_view()),
    path('verify', Verify.as_view()),
]