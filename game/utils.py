from django.contrib.auth.models import User
from .trees.symbol_tree import symbols
from pycoingecko import CoinGeckoAPI
from .trees.name_tree import names
from .trees.coin_map import map
from user.wallets import *
from .TopSecret import *
from .cryptoList import *
from .models import *
import requests
import datetime
import string
import random
import time

FINANCIAL_QUARTERS = {
    'Q1': {
        'start': {
            'month': 1,
            'day': 1,
            'hour': 9,
            'minute': 30
        }, 
        'end': {
            'month': 3,
            'day': 31,
            'hour': 16,
            'minute': 30 
        }
    },
    'Q2': {
        'start': {
            'month': 4,
            'day': 1,
            'hour': 9,
            'minute': 30
        },
        'end': {
            'month': 6,
            'day': 30,
            'hour': 16,
            'minute': 30
        }
    },
    'Q3': {
        'start': {
            'month': 7,
            'day': 1,
            'hour': 9,
            'minute': 30
        },
        'end': {
            'month': 9,
            'day': 30,
            'hour': 16,
            'minute': 30
        }
    },
    'Q4': {
        'start': {
            'month': 10,
            'day': 1,
            'hour': 9,
            'minute': 30
        },
        'end': {
            'month': 12,
            'day': 31,
            'hour': 16,
            'minute': 30
        }
    }
}

def current_time():
    return time.time() - (60 * 60 * 5)

def get_code():
    choices = string.ascii_uppercase + string.digits
    choices = choices.replace('l', '')
    choices = choices.replace('I', '')

    while True:
        code = ''.join(random.choice(choices) for i in range(8))
        queryset = Game.objects.filter(code=code)

        if not queryset.exists():
            return code    

def date_to_timestamp(date):
    year = int(date['year'])
    month = int(date['month'])

    if 'day' in date:
        day = int(date['day'])
    else:
        day = 0

    if 'hour' in date:
        hour = int(date['hour'])
    else:
        hour = 0

    if 'minute' in date:
        minute = int(date['minute'])
    else:
        minute = 0

    return int(datetime.datetime(year, month, day, hour, minute).timestamp())

def financial_quarter_start_end(quarter):
    current_time = time.localtime()
    year = current_time[0]

    start = FINANCIAL_QUARTERS[quarter]['start']
    start['year'] = year

    end = FINANCIAL_QUARTERS[quarter]['end']
    end['year'] = year

    return date_to_timestamp(start), date_to_timestamp(end)

def get_symbol_data(symbol, start_time, end_time):
    r = requests.get('https://finnhub.io/api/v1/stock/candle?symbol=' + symbol +
                     '&resolution=5&from=' + start_time + '&to=' + end_time + '&token=' + FINNHUB_API_KEY)

    return r.json()

def code_to_game(code):
    game = Game.objects.filter(code=code)

    return game[0]

def user_to_player(user, game):
    player = Player.objects.filter(user_id=user.id, game_id=game.id)

    return player[0]

def username_to_user(username):
    user = User.objects.filter(username=username)
    return user[0]

def make_refunds(game):
    players = game.players()

    for player in players:
        wager = Wager.objects.filter(player_id=player.id)
        wager = wager[0]

        if wager.frozen:
            user = User.objects.filter(id=player.user_id)
            user = user[0]
            unfreeze_funds(user, wager.amount)

def get_player(user, game):
    player = Player.objects.filter(user_id=user.id, game_id=game.id)

    if player.exists():
        temp = player[0].get_info()
        temp['participant'] = True
        return temp
    else:
        return {
            'participant': False,
            'balance': get_balance(user.id)
        }

    
def search_trees(val):
    results = []
    symbol_spot = symbols
    name_spot = names
    
    def add_to_results():
        if 'results' in symbol_spot:
            results.extend(symbol_spot['results'])

        if 'match' in symbol_spot:
            results.extend(symbol_spot['match'])

        if 'results' in name_spot:
            results.extend(name_spot['results'])

        if 'match' in name_spot:
            results.extend(name_spot['match'])
    
    for x in val:    
        add_to_results()
        if x in name_spot:
            name_spot = name_spot[x]

        if x in symbol_spot:
            symbol_spot = symbol_spot[x]
    add_to_results()

    ids = []
    unique = []

    results = sorted(results, key=lambda d: d['match'], reverse=True)

    for result in results:
        if not result['id'] in ids:
            temp = map[result['id']]
            temp['match'] = result['match']
            unique.append(temp)
            ids.append(result['id'])
    

    return sorted(unique, key=lambda d: (d['match']), reverse=True)

def tier_bet(bet, tier):
    if tier == 'diamond':
        return bet * 4
    if tier == 'gold':
        return bet * 3
    if tier == 'silver':
        return bet * 2
    if tier == 'bronze':
        return bet
    if tier == 'ghost':
        return 0

def format_time(time):
    return '{year}-{month}-{day}'.format(year=time[0], month=time[1], day=time[2] - 1)

def get_quotes(id):
    cg = CoinGeckoAPI()
    quote = cg.get_coin_by_id(id, tickers=False, localization="false", market_data=True, community_data=False, developer_data=False, sparkline=False)
    return quote['market_data']

def base_conversions():
    currencies = {
        'btc',
        'eth',
        'bnb'
    }

    for currency in currencies:
        currencies[currency] = get_quotes(currency)
    
    return currencies

def no_usd_quote(quotes):
    for quote in quotes:
        convert_with = get_quotes(quote)
        if 'usd' in convert_with:
            return quotes[quote] * convert_with['usd']

def usd_quote(id):
    quotes = get_quotes(id)
    try:
        return quotes['usd']
    except KeyError:
        return no_usd_quote(quotes)
    
def normalize_poirtfolios(data):
    longest = None
    length = 0
    for x in data:
        if len(data[x]) > length:
            length = len(data[x])
            longest = data[x]

    normalized = [{'date': d['date']} for d in longest]

    for t in range(length):
        for y in data:
            try:
                normalized[t][y] = data[y][t]['close']
            except IndexError:
                normalized[t][y] = data[y][-1]['close']

    return normalized

def player_context(player):
    if player.game.started:
        return {
            'rank': player.get_rank(),
            'take': player.take()
        }
    else:
        return {
            'take': player.take(),
            'allocation': '{:.1f}'.format((1 - (player.cash / 100000)) * 100)
        }
