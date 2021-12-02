from django.contrib.auth.models import User
from game.trees.coin_map import map
from game.trees.gecko_map import ids
from .model_utils import *
from django.db import models

DEFAULT_TIERS = {
    'ghost': 0,
    'bronze': 0,
    'silver': 0,
    'gold': 0,
    'diamond': 0
}

class IDToken(models.Model):
    # user - user corresponding to the uid token
    # key - used as the uid cookie, which helps determine a user upon initial page enter
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    key = models.CharField(max_length=40, primary_key=True)

    class Meta:
        db_table = 'IDToken'


class Profile(models.Model):
    # user - user corresponding to the uid token
    # phone - the phone number associated with a user
    # verification_code - the code used to verify a phone number ('000000' upon verification)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=10, unique=True)
    remember = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6)
    birthday = models.DateField(null=False)

    class Meta:
        db_table = 'Profile'

    def get_stats(self):
        stats = Stats.objects.filter(profile=self)
        
        if stats.exists():
            return stats[0]
        else:
            stats = Stats(profile=self)
            stats.save()
            return stats

    def get_watchlist(self):
        watchings = Watchlist.objects.filter(user=self.user)
        watchlist = {}
    
        for watching in watchings:
            watchlist[watching.map_id] = map[watching.map_id]
            watchlist[watching.map_id]['price'] = '{:.2f}'.format(usd_quote(ids[watching.map_id]))

        return watchlist


class Stats(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    total_games = models.IntegerField(default=0)
    tiered_games_won = models.IntegerField(default=0)
    mult_games_won = models.IntegerField(default=0)
    tiered_games_lost = models.IntegerField(default=0)
    mult_games_lost = models.IntegerField(default=0)
    tiered_total_bets = models.DecimalField(max_digits=17, decimal_places=8, null=True)
    mult_total_bets = models.DecimalField(max_digits=17, decimal_places=8, null=True)
    tiered_amount_won = models.DecimalField(max_digits=17, decimal_places=8, null=True)
    tiered_amount_lost = models.DecimalField(max_digits=17, decimal_places=8, null=True)
    mult_amount_won = models.DecimalField(max_digits=17, decimal_places=8, null=True)
    mult_amount_lost = models.DecimalField(max_digits=17, decimal_places=8, null=True)
    tiers = models.JSONField(default=DEFAULT_TIERS)
    favorites = models.JSONField(default=dict)

    class Meta:
        db_table = 'Stats'

    def top_10(self):
        favorites = []

        for favorite in self.favorites['crypto']:
            info = map[int(favorite)]
            favorites.append({'logo': info['logo'], 'name': info['name'],'symbol': info['symbol'],'allocation': self.favorites['crypto'][favorite]})

        return sorted(favorites, key=lambda d: d['allocation'], reverse=True)

    def info(self):
        return {
            'total_games': self.total_games,
            'tiered_games_won': self.tiered_games_won,
            'tiered_games_lost': self.tiered_games_lost,
            'mult_games_won': self.mult_games_won,
            'mult_games_lost': self.mult_games_lost,
            'tiered_total_bets': '{:.2f}'.format(self.tiered_total_bets),
            'mult_total_bets': '{:.2f}'.format(self.mult_total_bets),            
            'tiered_amount_won': '{:.2f}'.format(self.tiered_amount_won),
            'tiered_amount_lost': '{:.2f}'.format(self.tiered_amount_lost),
            'mult_amount_won': '{:.2f}'.format(self.mult_amount_won),
            'mult_amount_lost': '{:.2f}'.format(self.mult_amount_lost),
            'favorites': self.top_10(),
            'tiers': self.tiers,
        }


class Wallet(models.Model):
    address = models.CharField(max_length=100, primary_key=True)
    balance = models.DecimalField(default=0, max_digits=28, decimal_places=18)

    class Meta:
        db_table = "Wallets"


class Frozen(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    amount = models.DecimalField(default=0, max_digits=28, decimal_places=18)

    class Meta:
        db_table = 'Frozen'


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    map_id = models.IntegerField(default=0)

    class Meta:
        db_table = 'Watchlist'