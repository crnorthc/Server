from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User
from datetime import datetime as dt
from .trees.coin_map import map
from .trees.gecko_map import ids
from django.db import models
from control.models import *
from user.wallets import *
from .model_utils import *

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

def get_split(game):
    if game.is_tier():
        split = TIERED_SPLITS[game.split]
    else:
        if game.split == 'Top 40%':
            split = round(float(len(game.players)) * .4)
        else:
            split = round(float(len(game.players)) * .1)
    
    return split

def initialize_portfolios(game):
    players = game.players()
    conversions = base_conversions()

    for player in players:
        lineup = Lineup.objects.filter(player_id=player.id)

        if len(lineup) == 0:
            player.remove()
            continue

        for x in lineup:
            id = ids[x.map_id]

            if id in conversions:
                x.amount = float(x.allocation) / conversions[id]
                x.open = float(conversions[id])
            else: 
                quote = usd_quote(id)
                x.amount = float(x.allocation) / float(quote)
                x.open = float(quote)
                conversions[id] = quote

            x.save()

def format_time(time):
    time = dt.fromtimestamp(time)
    
    return {
        'year': time.year,
        'month': time.month,
        'day': time.day,
        'hours': time.hour,
        'minutes': time.minute
    }

def days_since(ts):
    return int((current_time() - float(ts)) / 86400) + 1

def coin_to_usd(data, coin):
    for x in data:
        x[4] *= coin

    return data

def format_portfolio_data(data, start, lineup):
    results = []
    longest = max([len(data[i]) for i in data])

    lineup_dict = {i.map_id: i for i in lineup}
    
    for period in range(longest):
        totals = {'date': 0, 'close': 0}
        count = 0
        for chart in data:
            try:
                if data[chart][period]['t'] / 1000 < start:
                    continue
                totals['date'] = data[chart][period]['t']
                totals['close'] += data[chart][period]['c'] * float(lineup_dict[chart].amount)
                count += 1
            except IndexError:
                totals['close'] += data[chart][-1]['c'] * float(lineup_dict[chart].amount)
                count += 1
        if count == len(data):
            results.append(totals)
    
    return results


def get_rankings(results):
    rankings = {}
    for x in range(len(results)):
        rankings[results['player']] = x + 1
    return rankings

def pay_winners(game, winners, pot):
    payouts = {}
    if game.is_tier():
        take = float(pot) * .03
        prize = ((float(pot) * .97) / float(len(winners)))
        for winner in winners:
            winnings = prize * float(TIER_PRIZE[winner['player'].tier()])
            take += (prize - winnings)
            payouts[winner['player'].id] = take
            add_funds(winner['player'].user, winnings)

        pay_house(take)

    else:
        pay_house(float(pot) * .2)
        
        prize = ((float(pot) * .8) / float(len(winners)))

        for winner in winners:
            add_funds(winner['player'].user, prize)
            payouts[winner['player'].id] = prize

    return payouts

def determine_pot(players):
    total = 0
    for player in players:
        wager = player.wager()
        total += wager.amount
        remove_funds(player.user, wager.amount)

    return total

def determine_winners(game, results):
    split = get_split(game)

    prev_player = {'player': None, 'close': None}
    winners = []

    for result in results:
        if split != 0:
            winners.append(result)
            prev_player = result 
            split -= 1
        else:
            if result['close'] == prev_player['close']:
                winners.append(result)

    return winners

def save_ranks(game, rankings):
    players = game.players()

    for player in players:
        player_history = PlayerHistory.objects.filter(player=player)
        player_history = player_history[0]
        player_history.rank = rankings[player]
        player_history.save()

def get_results(game):
    players = game.players()
    results = []

    for player in players:
        wager = player.wager()
        if wager.tier != 'ghost' and wager.amount != 0:

            lineup = player.get_lineup()
            total = 0
            for x in lineup:
                total += x.close

            results.append({
                'player': player,
                'close': total
            })

    results = sorted(results, key=lambda d: d['close'], reverse=True)

    save_ranks(get_rankings(results))

    return results

def create_history(player, total, lineup):
    wager = player.wager()

    player_history = PlayerHistory(
        user=player.user,
        game=player.game,
        score=total,
        bet=wager.amount,
        tier=wager.tier,
        lineup=lineup,
        portfolio=player.portfolio()   
    )

    player_history.save()

def finalize_scores(players):
    for player in players:
        lineup = player.get_lineup()
        total = 0
        saved_lineup = {}        
        for x in lineup:
            quote = usd_quote(ids[x.map_id])
            x.close = quote * float(x.amount)
            total += quote * float(x.amount)
            saved_lineup[x.map_id] = {'open': round(float(x.open), 2), 'close': round(float(x.close), 2)}
            x.save()
        create_history(player, total, saved_lineup)


class Game(models.Model):
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=15, default='Tiered')
    split = models.CharField(max_length=20)
    bet = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    code = models.CharField(max_length=8)
    league = models.CharField(max_length=40)
    live = models.BooleanField(default=False)    
    starting = models.BooleanField(default=False)
    started = models.BooleanField(default=False)
    ended = models.BooleanField(default=False)
    pot = models.IntegerField(default=0)
    creator = models.ForeignKey(Admin, on_delete=models.CASCADE)

    def get_basic_info(self):
        duration = Duration.objects.filter(game_id=self.id)
        duration = duration [0]
        return {
            'name': self.name,
            'type': self.type,
            'code': self.code,
            'league': self.league,
            'duration': duration.type,
            'start': format_time(duration.start),
            'end': format_time(duration.end),
            'players': len(self.players()),
            'split': self.split,
            'bet': self.bet,
            'started': self.started,
            'pot': self.pot
        }

    def get_info(self):
        duration = Duration.objects.filter(game_id=self.id)
        duration = duration [0]
        temp = {
            'name': self.name,
            'type': self.type,
            'code': self.code,
            'league': self.league,
            'duration': duration.type,
            'start': format_time(duration.start),
            'end': format_time(duration.end),
            'players': len(self.players()),
            'split': self.split,
            'bet': self.bet,
            'live': self.live,
            'started': self.started,
            'pot': self.pot
        }
        if self.started:
            players = self.players()
            players = [{'player': x.user.username, 'worth': x.get_worth()} for x in players]
            players = sorted(players, key=lambda d: d['worth'], reverse=True)
            temp['players_list'] = [{'player': x['player'], 'worth': '{:.2f}'.format(x['worth'])} for x in players]

        return temp

    def bet_type(self):
        if self.bet.multiplier == None:
            return 'tiered'
        else:
            return 'multiplier'

    def players(self):
        return Player.objects.filter(game_id=self.id)

    def is_tier(self):
        return self.type == 'tiered'

    def get_duration(self):
        duration = Duration.objects.filter(game_id=self.id)
        return duration[0]

    def start_time(self):
        duration = self.get_duration()
        return duration.start

    def end_time(self):
        duration = self.get_duration()
        return duration.end

    def start(self):
        self.starting = True
        print('starting game')
        self.save()
        
        initialize_portfolios(self)

        self.starting = False
        self.started = True

        self.save()

    def end(self):
        self.ended = True
        self.save()
        finalize_scores(self.players())
        results = get_results(self)
        winners = determine_winners(self, results)
        total = determine_pot(self.players())
        payouts = pay_winners(self, winners, total)

        return payouts


class Duration(models.Model):
    type = models.CharField(max_length=10, default='Day')
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    start = models.IntegerField(default=0)
    end = models.IntegerField(default=0)


class Player(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    cash = models.DecimalField(max_digits=25, decimal_places=4, default=100000)
    lineup_done = models.BooleanField(default=False)


    def get_info(self):
        wager = Wager.objects.filter(player_id=self.id)
        info = {
            'code': self.game.code,
            'cash': self.cash,
            'lineup_done': self.lineup_done,
            'lineup': self.get_lineup_info(),
            'balance': get_balance(self.user_id)
        }

        if wager.exists():
            wager = wager[0]
            info.update({'wager': wager.get_info()})
        
        if self.game.started:
            info['portfolio'] = self.portfolio()

        return info

    def get_lineup(self):
        lineup = Lineup.objects.filter(player_id=self.id)
        return lineup

    def get_lineup_info(self):
        lineup = Lineup.objects.filter(player_id=self.id)
        
        if lineup.exists():
            return sorted([x.get_info() for x in lineup], key=lambda d: d['allocation'], reverse=True)
        else:
            return []

    def wager(self):
        wager = Wager.objects.filter(player_id=self.id)
        return wager[0]

    def remove(self):
        wager = self.wager()
        unfreeze_funds(self.user.id, wager.amount)
        self.delete()

    def portfolio(self):
        lineup = Lineup.objects.filter(player_id=self.id)
        data = {}

        for x in lineup:
            res = poly_data(x.map_id, self.game)
            data[x.map_id] = res

        return format_portfolio_data(data, self.game.start_time(), lineup)

    def get_worth(self):
        lineup = self.get_lineup_info()
        worth = 0

        for x in lineup:
            quote = usd_quote(ids[x['id']])
            worth += (quote * float(x['amount']))
        
        return worth

    def tier(self):
        wager = self.wager()
        return wager.tier

    def get_rank(self):
        players = self.game.players()

        rankings = []
        for player in players:
            rankings.append({'player': player, 'score': player.get_worth()})
        
        rankings = sorted(rankings, key= lambda d: d['score'], reverse=True)

        for i in range(len(rankings)):
            if rankings[i]['player'] == self:
                return {'rank': i + 1, 'score': rankings[i]['score']}

    def take(self):
        if self.game.is_tier():
            return '{:.2f}'.format((self.game.pot / TIERED_SPLITS[self.game.split]) * TIER_PRIZE[self.tier()] * .97)
        else:
            if self.game.split == 'Top 10%':
                return '{:.2f}'.format(self.wager().amount * 8)
            else:
                return '{:.2f}'.format(self.wager().amount * 2)

class Wager(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    selected = models.BooleanField(default=True)
    frozen = models.BooleanField(default=False)
    placed = models.BooleanField(default=False)
    tier = models.CharField(max_length=8, null=True)

    def get_info(self):
        return {
            'tier': self.tier,
            'frozen': self.frozen,
            'placed': self.placed,
            'selected': self.selected,
            'amount': self.amount
            }

    def get_player(self):
        player = Player.objects.filter(id = self.player)

        return player[0]


class Lineup(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    map_id = models.IntegerField(default=0)
    amount = models.DecimalField(max_digits=25, decimal_places=10, null=True)
    allocation = models.DecimalField(max_digits=10, decimal_places=2)
    open = models.DecimalField(max_digits=25, decimal_places=10, null=True)
    close = models.DecimalField(max_digits=25, decimal_places=10, null=True)


    def get_info(self):
        info = map[self.map_id]
        info.update({
            'amount': self.amount,
            'allocation': self.allocation,
            'price': self.open
        })

        if self.open != None:
            info.update(self.get_current_value())    
        
        return info

    def get_current_value(self):
        current_value =  usd_quote(ids[self.map_id]) * float(self.amount)
        d_change = (current_value - float(self.open * self.amount))

        if d_change < 0:
            d_change = (float(self.open * self.amount) - current_value)

        p_change = ((d_change * 100) / float(self.open * self.amount * 100))

        return {
            'current_value': '{:.2f}'.format(current_value),
            'd_change': '{:.2f}'.format(d_change),
            'p_change': '{:.2f}'.format(p_change)
        }


class PlayerHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=25, decimal_places=10, null=True)
    ranking = models.IntegerField(default=0)
    bet = models.DecimalField(max_digits=6, decimal_places=2)
    won = models.DecimalField(max_digits=10, decimal_places=5, null=True)
    tier = models.CharField(max_length=8, null=True)
    lineup = models.JSONField(default=dict)
    portfolio = ArrayField(
        models.JSONField(default=dict)
    )

    def info(self):
        history = {
            'score': '{:.2f}'.format(self.score),
            'type': self.game.type,
            'ranking': self.ranking,
            'bet': self.bet,
            'won': '{:.2f}'.format(self.won),
            'lineup': []
        }

        for x in self.lineup:
            symbol_info = map[int(x)]
            history['lineup'].append({
                'name': symbol_info['name'],
                'symbol': symbol_info['symbol'],
                'logo': symbol_info['logo'],
                'allocation': self.lineup[x]
            })
        
        return history