from django.urls import path
from .views import *

urlpatterns = [
    path('create', CreateUser.as_view()),
    path('send_text', SendText.as_view()),
    path('confirm', ConfirmCode.as_view()),
    path('find', FindUser.as_view()),
    path('login', Login.as_view()),
    path('load', LoadUser.as_view()),
    path('recover-phone', RecoverPhone.as_view()),
    path('change-password', ChangePassword.as_view()),
    path('recent-game', MostRecentGame.as_view()),
    path('wallet', WalletInfo.as_view()),
    path('stats', Stats.as_view()),
]