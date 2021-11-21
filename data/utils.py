from .cryptoList import cryptos
from .models import *
import requests
import time

SECONDS_IN_WEEK = 60 * 60 * 24 * 7

TIME_SPANS = {
    'H': {'span': 'minute', 'multiplier': 1, 'show': 1},
    'D': {'span': 'minute', 'multiplier': 15, 'show': 2},
    'W': {'span': 'hour', 'multiplier': 1, 'show': 8},
    'M': {'span': 'day', 'multiplier': 1},
    'Y': {'span': 'week', 'multiplier': 1},
    'All': {'span': 'week', 'multiplier': 2}
}

def new_symbol(symbol):
    for crypto in cryptos:
        if crypto['symbol'].lower() == symbol.lower():
            name = crypto['name']
            image = crypto['image']
            break
    
    data = populate_data(symbol)
    new_symbol = Symbol(symbol=symbol, name=name, image=image, data=data)
    new_symbol.save()
    return new_symbol

def update_data(data, span, symbol):
    c_time = time.time()

    if c_time - data.last_update(span) > 60:
        update_span(data, span, symbol)


def update_span(data, span, symbol):
    pass

def format_time(time):
    return '{year}-{month}-{day}'.format(year=time[0], month=time[1], day=time[2])

def current_time():
    current_time = time.localtime()
    return format_time(current_time)

def date_weeks_ago(weeks):
    last_week = time.time() - (SECONDS_IN_WEEK * weeks)
    return format_time(last_week)

def from_date(span):
    if span == 'H' or span == 'D' or span == 'W':
        return date_weeks_ago(TIME_SPANS[span]['show'])
    else:
        return '2011-08-01'

def initialize_data():
    c_time = round(time.time())
    return Data(
        h_last_updated=c_time,
        d_last_updated=c_time,
        w_last_updated=c_time,
        m_last_updated=c_time,
        y_last_updated=c_time,
        a_last_updated=c_time,
    )

def update_data(span, data, Data):
    if span == 'H':
        Data.hour = data
    if span == 'D':
        Data.day = data
    if span == 'W':
        Data.week = data
    if span == 'M':
        Data.month = data
    if span == 'Y':
        Data.year = data
    if span == 'A':
        Data.all = data

    return Data

def format_results(results):
    temp = []
    for x in results:
        temp.append({
            'c': x['c'],
            'o': x['o'],
            'h': x['h'],
            'l': x['l'],
            'v': x['v']
        })

    return temp

def populate_data(symbol):
    to = current_time()

    for span in TIME_SPANS:
        data = initialize_data()
        _from = from_date(span)
        span = TIME_SPANS[span]['span']
        mult = TIME_SPANS[span]['multiplier']
        url = "https://api.polygon.io/v2/aggs/ticker/X:" + symbol + "USD/range/" + mult + "/" + span + "/" + _from + "/" + to + "?&apiKey=b4XCWhIAVjd82VOpYwXKjL5S3j9epMy6"        

        r = requests.get(url)

        results = r.json()
        temp = format_results(results['results'])
        data = update_data(span, temp, data)
            
    data.save()
    return data