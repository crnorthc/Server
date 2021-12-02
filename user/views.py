from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework import status
from django.db.models import Q
from django.apps import apps
from .wallets import *
from .settings import *
from .models import *
from .utils import *
import time

PlayerHistory = apps.get_model('game', 'PlayerHistory')
Player = apps.get_model('game', 'Player')


'''
    Authentication
'''
'''
    Create User -> Set IDToken -> Verify Phone -> Create Token (logged_in) -> Login -> Set Token (logged_in)
'''

class CreateUser(APIView):
    # Params
    #   - first_name <string>: user's first name
    #   - last_name <string>: user's last name
    #   - username <string>: user's username
    #   - password <string>: user's password
    #   - phone <string>: user's 10 digit phone number
    #   - email <string>: user's email (optional)
    #   - birthday <dict>: user's birthday {'year', 'month', 'day'}
    # Description
    #   - creates user object, IDToken object, and Profile object
    #   - return a Response with uid cookie

    permission_classes = [AllowAny]

    def post(self, request, format=None):
        first_name = request.data['first_name']
        last_name = request.data['last_name']
        username = request.data['username']
        password = request.data['password']
        phone = request.data['phone']
        birthday = request.data['birthday']
        birthday = datetime.date(birthday['year'], birthday['month'], birthday['day'])

        valid, msg = valid_user(request)

        if not valid:
            return Response({'Error': msg}, status=status.HTTP_403_FORBIDDEN)
    
        key = generate_token()

        user = User.objects.create_user(
            username=username, password=password, first_name=first_name, last_name=last_name)

        if PHONE_VERIFICATION:
            verification_code = get_verfication_code()
        else:
            verification_code = '000000'
            token = Token.objects.create(user=user)
            token.save()

        token = IDToken(key=key, user=user)
        profile = Profile(user=user, phone=phone, birthday=birthday, verification_code=verification_code)

        if 'email' in request.data:
            user.email = request.data['email']

        user.save()
        token.save()
        profile.save()


        return set_cookie([('uid', key)])


class FindUser(APIView):
    # Params
    #   - uid <string>: user's uid cookie value
    # Description
    #   - looks for the user correspoinding to the uid cookie
    #   - returns the phone number of that user
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        key = request.data['uid']
        token = IDToken.objects.filter(key=key)

        if token.exists():
            token = token[0]
            user = User.objects.filter(id=token.user_id)
            user = user[0]
            profile = Profile.objects.filter(user_id=user.id)
            profile = profile[0]

            return Response({'Phone': profile.phone}, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


class SendText(APIView):
    # Params
    #   - phone <string>: user's 10 digit phone number
    # Description
    #   - send the text to the phone number cointaing the verification code

    permission_classes = [AllowAny]

    def post(self, request, format=None):
        phone = request.data['phone']
        profile = phone_to_profile(phone)
        send_verification_code(phone, profile.verification_code)

        return Response(status=status.HTTP_200_OK)


class ConfirmCode(APIView):
    # Params
    #   - code <string>: user's 6 digit verification code
    #   - phone <string>: user's 10 digit phone number
    # Description
    #   - check to see if the verification ocde matches
    #   - creates an AuthToken object for the user, which is used to signify that a user is logged in

    permission_classes = [AllowAny]

    def post(self, request, format=None):
        phone = request.data['phone']
        code = request.data['code']
        profile = phone_to_profile(phone)
        
        if code == profile.verification_code:
            profile.verification_code = '000000'
            profile.save()
            if not code[0] == '6':
                user = profile_to_user(profile)
                token = Token.objects.create(user=user)
                token.save()
        else:
            return Response({'Error': "Incorrect Code"}, status=status.HTTP_403_FORBIDDEN)

        return Response(status=status.HTTP_200_OK)


class Login(APIView):
    # Params
    #   - username <string>: user's username
    #   - password <string>: user's password
    # Description
    #   - validates user's information
    #   - returns loggedin cookie if authentication is granted

    permission_classes = [AllowAny]

    def post(self, request, format=None):
        username = request.data['username']
        password = request.data['password']
        remember = request.data['remember']
        user = User.objects.filter(username=username)

        if not user.exists():
            return Response({'Error': 'Invalid Username'}, status=status.HTTP_403_FORBIDDEN)

        user = user[0]
        profile = Profile.objects.filter(user_id=user.id)
        profile = profile[0]

        if not profile.verification_code == '000000' or profile.verification_code[0] == '6':
            return Response({'Error': 'Verification Required'}, status=status.HTTP_403_FORBIDDEN)

        if user.check_password(password):

            if not profile.verification_code == '000000':
                return Response({'Error': 'Verification Required'}, status=status.HTTP_403_FORBIDDEN)
            else:
                profile.remember = remember

                if not profile.verification_code == '000000':
                    profile.verification_code = '000000'
                    
                profile.save()
                return login(user)
                
        else:
            return Response({'Error': 'Invalid Password'}, status=status.HTTP_403_FORBIDDEN)


class RecoverPhone(APIView):
    # Params
    #   - phone <string>: user's 10 digit phone number
    # Description
    #   - sends code to recover account
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        phone = request.data['phone']
        profile = Profile.objects.filter(phone=phone)

        if not profile.exists():
            return Response({'Error': 'Invalid Phone'}, status=status.HTTP_403_FORBIDDEN)

        profile = profile[0]
        
        verification_code = get_verfication_code(True)

        profile.verification_code = verification_code
        profile.save()

        send_verification_code(phone, profile.verification_code)

        return Response(status=status.HTTP_200_OK)


class ChangePassword(APIView):
    # Params
    #   - password <string>: user's new password
    #   - phone <string>: user's 10 digit phone number
    # Description
    #   - changes a user's password
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        phone = request.data['phone']
        password = request.data['password']
        profile = Profile.objects.filter(phone=phone)

        if not profile.exists():
            return Response({'Error': 'Invalid Phone'}, status=status.HTTP_403_FORBIDDEN)

        profile = profile[0]
        
        user = profile_to_user(profile)
        user.set_password(password)
        user.save()

        return Response(status=status.HTTP_200_OK)


'''
    Profile
'''
# DB Needs some work to make this cleaner
class MostRecentGame(APIView):

    def get(self, request):
        players = PlayerHistory.objects.filter(user=request.user)
        newest_game = None
        newest_time = 0
        newest_player = None

        for player in players:
            if player.game.start_time() > newest_time:
                newest_time = player.game.start_time()
                newest_game = player.game
                newest_player = player

        return Response({'player_history': newest_player.info(), 'game_history': newest_game.get_basic_info()}, status=status.HTTP_200_OK)


class WalletInfo(APIView):

    def get(self, request):
        players = Player.objects.filter(user=request.user)

        current_games = []
        
        for player in players:
            details = {
                'name': player.game.name,
                'bet': player.wager().amount,
            }

            if player.game.is_tier():
                prize = get_game_winnings(player.game, player.wager().tier)
            else:
                if player.game.split == 'Top 10%':
                    prize = player.wager().amount * 8
                else:
                    prize = player.wager().amount * 2

            details['prize'] = prize

            current_games.append(details)

        return Response({'wallet': current_games}, status=status.HTTP_200_OK)


class Stats(APIView):

    def get(self, request):
        players = PlayerHistory.objects.filter(user=request.user)
        best_game = None
        best_score = 0
        best_player = None
        worst_game = None
        worst_score = None
        worst_player = None
        

        for player in players:
            if player.score > best_score:
                best_score = player.score
                best_game = player.game.get_basic_info()
                best_player = player.info()

            if worst_score == None:
                worst_score = player.score
                worst_game = player.game.get_basic_info()
                worst_player = player.info()
            else:
                if player.score < worst_score:
                    worst_score = player.score
                    worst_game = player.game.get_basic_info()
                    worst_player = player.info()

        return Response({'best': {'player': best_player, 'game': best_game}, 'worst': {'player': worst_player, 'game': worst_game}}, status=status.HTTP_200_OK)


class History(APIView):

    def get(self, request):
        players = PlayerHistory.objects.filter(user=request.user)
        history = []

        for player in players:
            history.append({
                'player': player.info(), 
                'game': player.game.get_basic_info()
            })

        return Response({'History': history}, status=status.HTTP_200_OK)

'''
    General
'''
class LoadUser(APIView):

    def get(self, request):
        return Response({'user': load_user(request.user)}, status=status.HTTP_200_OK)


class Watch(APIView):

    def post(self, request, format=None):
        id = request.data['id']
        watchList = Watchlist.objects.filter(user=request.user, map_id=id)

        if watchList.exists():
            watchList[0].delete()
        else:
            watchList = Watchlist(user=request.user, map_id=id)
            watchList.save()

        return Response({'watchlist': get_watchlist(request.user)}, status=status.HTTP_200_OK)
    
    def get(self, request):
        return Response({'watchlist': get_watchlist(request.user)}, status=status.HTTP_200_OK)