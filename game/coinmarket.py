from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json


def make_request(url, params):
    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': '3d0de223-7f52-4c71-8b75-2bc995abf66e',
    }

    session = Session()
    session.headers.update(headers)

    response = session.get(url, params=params)
    data = json.loads(response.text)

    return data['data']
    

