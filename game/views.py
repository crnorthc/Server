from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .cryptoList import cryptos
from django.apps import apps
from user.wallets import *
from .coinmarket import *
from .models import *
from .utils import *
import datetime

Profile = apps.get_model('user', 'Profile')

DURATION_TO_SEC = {
    'Week': 7 * 24 * 60 * 60,
    'Day': 24 * 60 * 60,
    'Hour': 60 * 60
}

STOCK_DURATION_TO_SEC = {
    'Week': 60 * 60 * 102.5,
    'Day': 60 * 60 * 6.5
}


class Create(APIView):
    # Params
    #   - game <dict>: dict of game params
    # Description
    #   - creates a new game, admin only access
    def post(self, request, format=None):    
        if request.admin == None:
            return Response({"Error", "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        game = request.data['game']
        type = game['type']
        name = game['name'] 
        league = game['league'] 
        duration = game['duration'] 
        start = game['date']['start'] 
        split = game['split']
        bet = game['bet']

        if duration == 'Quarter':
            start, end = financial_quarter_start_end(start)  
        else:         
            start = date_to_timestamp(start) 
            if duration == "Custom":
                end = date_to_timestamp(game['date']['end'])
            else:
                if league == "Stocks":
                    end = start + STOCK_DURATION_TO_SEC[duration]
                else:
                    end = start + DURATION_TO_SEC[duration]        


        new_game = Game(
            name=name, 
            type = type,
            league=league,  
            split=split, 
            bet=bet, 
            code=get_code(), 
            creator=request.admin
        )        
        new_game.save()

        duration = Duration(type=duration, game=new_game, start=start, end=end)
        duration.save()

        return Response({'Success': 'Game Created'}, status=status.HTTP_200_OK)


class Delete(APIView):
    # Params
    #   - code <string>: game's code
    # Description
    #   - deletes game and unfreezes funds
    def post(self, request, format=None):    
        if request.admin == None:
            return Response({"Error", "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        code = request.data['code']

        game = Game.objects.filter(code=code)
        game = game[0]

        if game.live:
            make_refunds(game)

        game.delete()
        
        return Response({'Success': 'Game Deleted'}, status=status.HTTP_200_OK)


class GoLive(APIView):
    # Params
    #   - code <string>: game's code
    # Description
    #   - deletes game and unfreezes funds
    def post(self, request, format=None):    
        if request.admin == None:
            return Response({"Error", "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        code = request.data['code']

        game = Game.objects.filter(code=code)
        game = game[0]

        game.live = True

        game.save()
        
        return Response({'Success': game.get_info()}, status=status.HTTP_200_OK)


class GetAll(APIView):
    # Params
    #   - game <dict>: dict of game params
    # Description
    #   - creates a new game, admin only access
    def post(self, request, format=None):    
        games = {}

        if request.admin == None:
            Games = Game.objects.filter(live=True, ended=False)
        else:
            Games = Game.objects.all()
            #Games = Game.objects.filter(ended=False)

        for game in Games:
            info = game.get_basic_info()
            games[info['code']] = info

        return Response({'Success': games}, status=status.HTTP_200_OK)


class MyGames(APIView):
    # Params
    #   - NONE
    # Description
    #   - gets a user's games (future, present, past)
    def get(self, request):    
        games = {}

        players = Player.objects.filter(user_id=request.user.id)

        for player in players:
            info = player.game.get_basic_info()
            games[info['code']] = info

        return Response({'Success': games}, status=status.HTTP_200_OK)


class GetGame(APIView):
    # Params
    #   - game <dict>: dict of game params
    # Description
    #   - creates a new game, admin only access
    def get(self, request, code):    
        game = Game.objects.filter(code=code)
        if not game.exists():
            return Response({"Error", "Invalid Code"}, status=status.HTTP_404_NOT_FOUND)

        game = game[0]

        if game.starting:
            return Response({'One Sec': 'Game Starting'}, status=status.HTTP_200_OK)

        player = get_player(request.user, game)
        
        return Response({'Game': game.get_info(), "Player": player}, status=status.HTTP_200_OK)


class Join(APIView):
    
    def post(self, request, format=None):
        code = request.data['code']
        bet = request.data['bet']
        game = Game.objects.filter(code=code)
        game = game[0]

        if game.starting or game.started:
            return Response({'Error': 'Too Late'}, status=status.HTTP_403_FORBIDDEN)

        if game.is_tier():
            tier = bet 
            bet = tier_bet(game.bet, tier)

        if enough_funds(request.user.id, bet):
            freeze_funds(request.user, bet)

            player = Player(user=request.user, game=game)
            wager = Wager(amount=bet, frozen=True, player=player)       

            if game.is_tier():
                wager.tier = tier
            
            player.save()
            wager.save()

            return Response({'Success': player.get_info()}, status=status.HTTP_200_OK)
        else:
            return Response({'Error': 'Insuficient Funds'}, status=status.HTTP_403_FORBIDDEN)


class EditLineup(APIView):

    def post(self, request, format=None):
        code = request.data['code']
        allocation = request.data['allocation']
        id = request.data['id']
        game = code_to_game(code)
        player = user_to_player(request.user, game)

        if current_time() - game.start_time() > 10:
            return Response({'Error': 'Too Late'}, status=status.HTTP_403_FORBIDDEN)

        lineup = Lineup.objects.filter(player_id=player.id, map_id=id)

        if lineup.exists():
            lineup = lineup[0]
            dif = allocation - lineup.allocation
            lineup.allocation = allocation 
            if player.cash - dif < 0:
                return Response({'Error': 'Not Enough Funds'}, status=status.HTTP_200_OK)
        else:
            if allocation > player.cash:
                return Response({'Error': 'Not Enough Funds'}, status=status.HTTP_200_OK)

            dif = allocation
            lineup = Lineup(player=player, allocation=allocation, map_id=id)

        player.cash -= dif
        player.save()

        if allocation == 0:
            lineup.delete()
        else:
            lineup.save()

        return Response({'Success': player.get_info()}, status.HTTP_200_OK)


class SearchCrypto(APIView):

    def post(self, request, format=None):
        search = request.data['search'].lower()    
        results = search_trees(search)

        return Response({'Success': results}, status=status.HTTP_200_OK)


class EditWager(APIView):

    def post(self, request, format=None):
        wager = request.data['wager'] 
        code = request.data['code']       
        game = Game.objects.filter(code=code)
        game = game[0]

        player = user_to_player(request.user, game)

        Wager = player.wager()
        
        if game.is_tier():
            amount = tier_bet(game.bet, wager)
            if enough_funds(request.user.id, amount):
                unfreeze_funds(request.user.id, Wager.amount)
                freeze_funds(request.user.id, amount)
                Wager.amount = amount
                Wager.tier = wager
            else:
                return Response({'Error': 'Insuficient Funds'}, status=status.HTTP_403_FORBIDDEN)
        else:
            if enough_funds(request.user.id, wager):
                if wager == 0:
                    unfreeze_funds(request.user.id, wager)
                else:
                    freeze_funds(request.user.id, wager)
                Wager.amount = wager
            else:
                return Response({'Error': 'Insuficient Funds'}, status=status.HTTP_403_FORBIDDEN)

        Wager.save()        

        return Response({'Success': player.get_info()}, status=status.HTTP_200_OK)


class Compare(APIView):

    def post(self, request, format=None):
        code = request.data['code']      
        username = request.data['username'] 
        game = Game.objects.filter(code=code)
        game = game[0]

        user = username_to_user(username)

        player = user_to_player(user, game)

        portfolio = {username: player.portfolio()}
        
        return Response(portfolio, status=status.HTTP_200_OK)