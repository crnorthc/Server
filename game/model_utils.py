from pycoingecko import CoinGeckoAPI
from .trees.coin_map import map
from django.apps import apps
from user.wallets import *
from .TopSecret import *
import requests
import time

def current_time():
    return time.time() - (60 * 60 * 5)

def get_quotes(id):
    cg = CoinGeckoAPI()
    quote = cg.get_coin_by_id(id, tickers=False, localization="false", market_data=True, community_data=False, developer_data=False, sparkline=False)
    return quote['market_data']['current_price']

def base_conversions():
    currencies = {
        'bitcoin': 0,
        'ethereum': 0,
        'binancecoin': 0
    }

    for currency in currencies:
        quotes = get_quotes(currency)
        currencies[currency] = quotes['usd']

    return currencies

def no_usd_quote(quotes):
    for quote in quotes:
        try:
            convert_with = get_quotes(quote)
            if 'usd' in convert_with:
                return quotes[quote] * convert_with['usd']
        except:
            pass

def usd_quote(id):
    quotes = get_quotes(id)
    if 'usd' in quotes:
        return quotes['usd']
    else:
        return no_usd_quote(quotes)
  

def poly_request_params(game):
    start = game.start_time() - 86400
    end = current_time() - 86400

    length = end - start

    _from = time.localtime(start)
    _to = time.localtime()

    _from = '{y}-{m}-{d}'.format(y=_from[0], m=_from[1], d=_from[2])
    _to = '{y}-{m}-{d}'.format(y=_to[0], m=_to[1], d=_to[2])

    span = 'minute'
    if length > 3000000:
        span = 'month'

    return _from, _to, span

def poly_data(id, game):
    ticker = map[id]['ticker']
    start, end, span = poly_request_params(game)

    url = 'https://api.polygon.io/v2/aggs/ticker/{}/range/1/{}/{}/{}?&limit=50000&apiKey={}'.format(ticker, span, start, end, POLY_KEY)
    r = requests.get(url)
    r = r.json()
    
    while True:
        if r['status'] == 'ERROR':
            time.sleep(60)            
            r = requests.get(url)
            r = r.json()
        else:
            break 

    for x in r['results']:
        x['t'] = x['t'] + 86400000
    
    return r['results']


'''
def make_refunds(game, wagers):
    players = game.players()

    for player in players:
        wager = Wager.objects.filter(player_id=player.id)
        wager = wager[0]

        if wager.frozen:
            user = User.objects.filter(id=player.user_id)
            user = user[0]
            unfreeze_funds(user, wager.amount)'''
