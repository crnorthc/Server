from rest_framework.response import Response
from cryptography.fernet import Fernet
from rest_framework import status
from .TopSecret import *
from .models import *
from .views import *
import binascii
import os

password= "gAAAAABhhaAPJPQZ5nE94T8C0skhXKwNRsD2wt27qrm7k8GLi7z_pxF1iZckgz7rx7wIm80LzYdUgIVbGwA-zge0NsQJBrNQIr8Bb9KAIefGuwE5V67x5itH7L5MSI4-y5bMyUkHVv_M"

def is_valid(password):
    token = decrypt_text(password, the_root_of_evil)
    token = token[:-6]

    admin = Admin.objects.filter(key=token)

    if not admin.exists():
        return False, None
    else:
        return True, admin[0]

def generate_token():
    # Params
    #   - None
    # Description
    #   - randomly generates the token used for uid (user id) in the IDToken model

    token = binascii.hexlify(os.urandom(20)).decode()
    tokens = Admin.objects.filter(key=token)

    while tokens.exists():
        token = binascii.hexlify(os.urandom(20)).decode()
        tokens = Admin.objects.filter(key=token)

    return token


def encrypt_text(plain_text, key):
    f = Fernet(key)
    encrypted_text = f.encrypt(bytes(plain_text, "UTF-8"))
    return encrypted_text.decode()


def decrypt_text(encrypted_text, key):
    f = Fernet(key)
    return f.decrypt(bytes(encrypted_text,"UTF-8")).decode()

def set_cookie(key, name, data=None, remember=False):
    # Params
    #   - key <string>: the value of the cookie
    #   - name <string>: the name of the cookie
    #   - data <dict>: response data
    #   - now <bool>: True to delete the cookie
    # Description
    #   - returns a response object containing a cookie
    response = Response(data, status=status.HTTP_200_OK)
    response.set_cookie(key=name, value=key, samesite="None", secure=True)
    response["Access-Control-Allow-Credentials"]=True

    return response