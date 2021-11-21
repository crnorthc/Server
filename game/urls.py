from django.urls import path
from .views import *
from .admin import *

urlpatterns = [
    path('create', Create.as_view()),
    path('delete', Delete.as_view()),
    path('get-all', GetAll.as_view()),
    path('get/<str:code>/', GetGame.as_view()),
    path('live', GoLive.as_view()),
    path('join', Join.as_view()),
    path('search-crypto', SearchCrypto.as_view()),
    path('edit-lineup', EditLineup.as_view()),
    path('edit-wager', EditWager.as_view()),
    path('my', MyGames.as_view()),
    path('compare', Compare.as_view())
]