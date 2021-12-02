from pycoingecko import CoinGeckoAPI
from .TopSecret import *
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
  

