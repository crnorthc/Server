from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from rest_framework import status
from .TopSecret import *
from .wallets import *
from .models import *
import datetime
import time
import binascii
import smtplib
import random
import ssl
import os

carriers_email = [
    '@txt.att.net',
    '@smsmyboostmobile.com',
    '@sms.cricketwireless.net',
    '@messaging.sprintpcs.com',
    '@tmomail.net',
    '@email.uscc.net',
    '@vtext.com',
    '@vmobl.com'
]

SECONDS_IN_YEAR = 60 * 60 * 24 * 365

'''
    Authentication Helpers
'''

def valid_user(request):
    birthday = request.data['birthday']
    username = request.data['username']
    phone = request.data['phone']    

    if under_18(birthday):
        return False, 'Underage'

    usernames = User.objects.filter(username=username)    
    phones = Profile.objects.filter(phone=phone)

    if usernames.exists():
        return False, "Username Taken"

    if phones.exists():
        return False, "Phone Taken"

    if 'email' in request.data:    
        email = request.data['email']
        emails = User.objects.filter(email=email)

        if emails.exists():
            return False, "Email Taken"

    return True, "Valid User"

def generate_token():
    # Params
    #   - None
    # Description
    #   - randomly generates the token used for uid (user id) in the IDToken model

    token = binascii.hexlify(os.urandom(20)).decode()
    tokens = IDToken.objects.filter(key=token)

    while tokens.exists():
        token = binascii.hexlify(os.urandom(20)).decode()
        tokens = IDToken.objects.filter(key=token)

    return token

def get_verfication_code(recover=False):
    # Params
    #   - recover <boolean>: whether or not the code is for account recovery
    # Description
    #   - randomly generates the code used for phone verification, starts with a 6 if for recovery

    while True:
        if recover:
            code = '6'
            add =  ''.join(["{}".format(random.randint(0, 9)) for _ in range(0, 5)])
            code = code + add
        else:
            code = str(random.choice([1, 2, 3, 4, 5, 7, 8, 9]))
            add =  ''.join(["{}".format(random.randint(0, 9)) for _ in range(0, 5)])
            code = code + add

        profile = Profile.objects.filter(verification_code=code)

        if not profile.exists() and code != '000000':
            return code

def under_18(birthday):
    current_date = time.time()
    birthday = datetime.datetime(birthday['year'], birthday['month'], birthday['day']).timestamp()

    return (current_date - birthday) / SECONDS_IN_YEAR < 18

def login(user):
    # Params
    #   - user <user object>: user to be logged in
    # Description
    #   - sets the cookie, which is sent for all future requests, signifying authentication
    token = Token.objects.filter(user_id=user.id)

    data = {"user": load_user(user)} 

    profile = user_to_profile(user)

    idtoken = IDToken.objects.filter(user_id=user.id)
    idtoken = idtoken[0]

    return set_cookie([('loggedIn', token[0].key), ('uid', idtoken.key)], data, profile.remember)

'''
    General Helpers
'''

def load_user(user):
    # Params
    #   - user <user object>: user to be logged in
    # Description
    #   - returns a user's information
    profile = Profile.objects.filter(user_id=user.id)
    profile = profile[0]
    stats = Stats.objects.filter(profile_id=profile.id)
    stats = stats[0]

    return {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username,
        'phone': profile.phone,
        'balance': get_balance(user.id),
        'frozen': frozen_balance(user.id),
        'stats': stats.info()
    }

def set_cookie(cookies, data=None, remember=False):
    # Params
    #   - cookies <list: <tuple>>: [(key_name, value)]
    #   - name <string>: the name of the cookie
    #   - data <dict>: response data
    #   - now <bool>: True to delete the cookie
    # Description
    #   - returns a response object containing a cookie
    response = Response(data, status=status.HTTP_200_OK)
    for cookie in cookies:
        if remember:
            age = 365 * 24 * 60 * 60
            expires = datetime.strftime(
                datetime.utcnow() + timedelta(seconds=age),
                "%a, %d %b %Y %H:%M:%S GMT",
            )
            response.set_cookie(key=cookie[0], value=cookie[1], expires=expires, samesite="None", secure=True)
        else:
            response.set_cookie(key=cookie[0], value=cookie[1], samesite="None", secure=True)

    response["Access-Control-Allow-Credentials"]=True

    return response

def send_verification_code(phone, code):
    # Params
    #   - phone <string>: users phone number
    #   - code <string>: six digit verification code 
    # Description
    #   - send the verfication code to a user's phone 
    message = MIMEText(code)
    message['Subject'] = 'Your Verification Code is'


    for email in carriers_email:
        send_to = phone + email
        message['To'] = send_to
        try:
            send_email(message, send_to)
            break
        except smtplib.SMTPRecipientsRefused:
            continue

def send_email(message, email):
    # Params
    #   - message <string>: message of the email
    #   - email <string>: email of the recipient
    # Description
    #   - send an email containg 'message' to 'email'
    sender_email = "vapurofficial@gmail.com"
    message['From'] = sender_email
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, email_password)
        server.sendmail(
            sender_email, email, message.as_string()
        )

def phone_to_profile(phone):
    # Params
    #   - phone <string>: 10 digit phone number
    # Description
    #   - returns the profile object pertaining to the phone number
    profile = Profile.objects.filter(phone=phone)
    return profile[0]

def profile_to_user(profile):
    # Params
    #   - profile <profile object>: profile of needed user
    # Description
    #   - returns the user object pertaining to the profile object
    user = User.objects.filter(id=profile.user_id)
    return user[0]

def user_to_profile(user):
    # Params
    #   - user <user object>: user of needed profile
    # Description
    #   - returns the profile object pertaining to the user object
    profile = Profile.objects.filter(user_id=user.id)
    return profile[0]


'''
    Profile Helpers
'''
TIER_PRIZE = {
    'bronze': .25,
    'silver': .5,
    'gold': .75,
    'diamond': 1
}

TIERED_SPLITS = {
    'Top Player': 1,
    'Top 3 Players': 3,
    'Top 5 Players': 5,
    'Top 10 Players': 10
}

def get_game_winnings(game, tier):
    players = game.players()
    total = 0

    for player in players:
        total += player.wager().amount

    return '{:.2f}'.format((float(total) / float(TIERED_SPLITS[game.split]) * TIER_PRIZE[tier]) * .97)