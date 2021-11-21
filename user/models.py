from django.contrib.auth.models import User
from game.trees.coin_map import map
from django.db import models

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

DEFAULT_TIERS = {
    'ghost': 0,
    'bronze': 0,
    'silver': 0,
    'gold': 0,
    'diamond': 0
}

class Stats(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    total_games = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)
    games_lost = models.IntegerField(default=0)
    total_bets = models.DecimalField(max_digits=17, decimal_places=8, null=True)
    amount_won = models.DecimalField(max_digits=17, decimal_places=8, null=True)
    amount_lost = models.DecimalField(max_digits=17, decimal_places=8, null=True)
    tiers = models.JSONField(default=DEFAULT_TIERS)
    favorites = models.JSONField(default=dict)

    class Meta:
        db_table = 'Stats'

    def top_4(self):
        favorites = []

        for favorite in self.favorites['crypto']:
            info = map[int(favorite)]
            favorites.append({'name': info['name'],'symbol': info['symbol'],'allocation': self.favorites['crypto'][favorite]})

        return sorted(favorites, key=lambda d: d['allocation'], reverse=True)

    def info(self):
        return {
            'total_games': self.total_games,
            'games_won': self.games_won,
            'games_lost': self.games_lost,
            'total_bets': self.total_bets,
            'amount_won': self.amount_won,
            'amount_lost': self.amount_lost,
            'favorites': self.top_4(),
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
