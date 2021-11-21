from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework import status
from .TopSecret import *
from .models import *
from .utils import *
import time

'''
Level 4 admins must be created manually 

Admins must be created by an admin with a higher clearance level
'''

class CreateAdmin(APIView):

    def post(self, request, format=None):
        level = request.data['level']
        username = request.data['username']
        email = request.data['email']

        if not '@vapur.io' in email:
            return Response({'Error': 'Must use Vapur Email'}, status=status.HTTP_403_FORBIDDEN)

        key = generate_token()

        user = User.objects.filter(username=username)
        user = user[0]

        admin = Admin(user=user, key=key, email=email, level=level)
        admin.save()

        key = key + '69420' + str(level)
        password = encrypt_text(key, the_root_of_evil)

        return Response({'Password': password}, status=status.HTTP_200_OK)


class Login(APIView):

    def post(self, request, format=None):
        
        email = request.data['email']
        password = request.data['password']

        if not '@vapur.io' in email:
            return Response({'Error': 'Not Vapur Email'}, status=status.HTTP_403_FORBIDDEN)

        valid, admin = is_valid(password)

        if valid:
            return set_cookie(admin.key, 'aid')
        else:
            return Response({'Error': 'Invalid Password'}, status=status.HTTP_403_FORBIDDEN)


class Verify(APIView):

    def post(self, request, format=None):

        if request.admin == None:
            return Response({'Error': 'Invalid Credentials'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'Sucecess': 'Verified'}, status=status.HTTP_200_OK)
