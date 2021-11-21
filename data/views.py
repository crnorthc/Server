from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework import status
from .cryptoList import cryptos
from .models import *
from utils import *
import datetime



class Get(APIView):
    # Params
    #   - code <string>: game's code
    # Description
    #   - deletes game and unfreezes funds
    def get(self, request, symbol, span):    
        symbol = Symbol.objects.filter(symbol=symbol)

        # Will need to be updated when stocks are added
        if not symbol.exists():
            symbol = new_symbol(symbol)

            Response({'Success': symbol.get_data(span)}, status=status.HTTP_200_OK)

        symbol = symbol[0]

        data = symbol.get_data()
        update_data(data, span, symbol)
            
        return Response({'Success': 'Game Deleted'}, status=status.HTTP_200_OK)

