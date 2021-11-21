from rest_framework.response import Response
from rest_framework import status
from .models import *

class AdminMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        admin_request = ('control' in request.path and not 'login' in request.path) or 'game' in request.path
        
        if admin_request:
            if not 'aid' in request.COOKIES:
                return Response({"Error": "No Admin Credentials"}, status=status.HTTP_403_FORBIDDEN)
            else:
                
                valid, admin = self.valid_cookie(request.COOKIES['aid'])
                if not valid: return Response({"Error": "Invalid Admin Credentials"}, status=status.HTTP_403_FORBIDDEN)
            
            request.admin = admin        
        else:
            request.admin = None
        
        response = self.get_response(request)
        return response

    def valid_cookie(self, cookie):
        admin = Admin.objects.filter(key=cookie)

        if not admin.exists():
            return False, None
        else:
            return True, admin[0]
