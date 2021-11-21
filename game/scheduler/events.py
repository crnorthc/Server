from django.apps import apps
from ..models import *
import time 

Profile = apps.get_model('user', 'Profile')
Stats = apps.get_model('user', 'Stats')


def delete_players(game):
    players = game.players()
    for player in players:
        player.delete()

def save_stats(game, payouts):
    players = game.players()

    for player in players:
        profile = Profile.objects.filter(user=player.user)
        profile = profile[0]
        wager = player.wager()

        lineup = player.get_lineup()
        for x in lineup:
            if x.map_id in stats.favorites['crypto']:
                stats.favorites['crypto'][x.map_id] += x.allocation
            else:
                stats.favorites['crypto'][x.map_id] = x.allocation

        stats = profile.get_stats()
        stats.total_games += 1
        stats.total_bets += wager.amount

        if player.id in payouts:
            stats.games_won += 1
            stats.amount_won += payouts[player.id]
        else:
            stats.games_lost += 1
            stats.amount_lost += wager.amount

        if game.is_tier():
            stats.tiers[wager.tier] += 1

        stats.save()

def watch_games():
    games = Game.objects.filter(live=True, ended=False)
    current_time = time.time()
    for game in games:
        if current_time > game.start_time() + 10 and not game.started:
            game.start()          

        if current_time > game.end_time():
            payouts = game.end()
            save_stats(game, payouts)
            delete_players(game)