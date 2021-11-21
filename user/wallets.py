from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins
from .TopSecret import mnemonic
from decimal import Decimal
from .models import *

def create_wallet(user):    
    address = get_address(user.id)
    wallet = Wallet(address=address, balance=0)            
    wallet.save()

def get_address(id):
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()

    coin = Bip44Coins.BINANCE_SMART_CHAIN

    root = Bip44.FromSeed(seed_bytes, coin)
    account = root.Purpose().Coin().Account(id)

    return account.PublicKey().ToAddress()

def get_balance(id):
    address = get_address(id)
    wallet = Wallet.objects.filter(address=address)

    if wallet.exists():
        wallet = wallet[0]
        return wallet.balance
    else: 
        return 0

def frozen_balance(id):
    address = get_address(id)
    wallet = Wallet.objects.filter(address=address)
    wallet = wallet[0]

    frozen = Frozen.objects.filter(wallet=wallet)

    return frozen[0].amount

def user_to_wallet(user):
    address = get_address(user.id)
    wallet = Wallet.objects.filter(address=address)

    if wallet.exists():
        return wallet[0]

def enough_funds(id, bet):
    balance = get_balance(id)

    return float(balance) >= float(bet)

def freeze_funds(user, amount):
    wallet = user_to_wallet(user)
    wallet.balance -= amount
    frozen = Frozen.objects.filter(wallet=wallet)

    if frozen.exists():
        frozen = frozen[0]
        frozen.amount += amount
    else:
        frozen = Frozen(wallet=wallet, amount=amount)

    wallet.save()
    frozen.save()

def unfreeze_funds(user, amount):
    wallet = user_to_wallet(user)
    wallet.balance += amount
    frozen = Frozen.objects.filter(wallet=wallet)

    if frozen.exists():
        frozen = frozen[0]
        frozen.amount -= amount
    else:
        frozen = Frozen(wallet=wallet, amount=amount)

    wallet.save()
    frozen.save()

def remove_funds(user, amount):
    wallet = user_to_wallet(user)
    frozen = Frozen.objects.filter(wallet=wallet)
    frozen = frozen[0]
    frozen.amount -= Decimal(amount)

    frozen.save()

def add_funds(user, amount):
    print('paying: ' + user.username + ' ' + str(amount))
    wallet = user_to_wallet(user)
    wallet.balance += Decimal(amount)

    wallet.save()

def pay_house(amount):
    wallet = Wallet.objects.filter(address='house')
    wallet = wallet[0]
    print('paying: house ' + str(amount))
    wallet.balance = Decimal(amount)

    wallet.save()