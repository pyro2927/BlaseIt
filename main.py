#!/usr/bin/env python
import json
import requests

GLOBAL_COOKIES={'connect.sid': 'PUT_YOUR_COOKIE_HERE'}
BET_AMOUNT=20
ALWAYS_BET_ON=['Sunbeams', 'Moist Talkers', 'Firefighters']

class WhichTeam:
    # returns the team ID to bet on for a given game object
    @staticmethod
    def compute_bet(game):
        # Check to see if our favorites are playing, in order
        for t in ALWAYS_BET_ON:
            if t in game['awayTeamNickname']:
                return game['awayTeam']
            if t in game['homeTeamNickname']:
                return game['homeTeam']
        # No favorites, algo shit
        if game['awayOdds'] > 0.50:
            return game['awayTeam']
        else:
            return game['homeTeam']

class BlaseIt:

    def __init__(self):
        # first get our monies
        me = self.user_info()
        self.monies = me['coins']
        self.user_id = me['id']
        # then active bets
        self.bets = [x['gameId'] for x in self.get_active_bets()]
        # then start streaming and betting
        print("Starting with " + str(self.monies) + " coins")
        print("Connecting to event stream...")
        self.connect_to_event_stream()
        # TODO: handle requests.exceptions.ChunkedEncodingError

    def get(self, url):
        r = requests.get('https://www.blaseball.com/' + url, cookies=GLOBAL_COOKIES)
        return r.json()

    def post(self, url, payload={}):
        r = requests.post('https://www.blaseball.com/' + url, cookies=GLOBAL_COOKIES, json=payload)
        return r.json()

    def user_info(self):
        return self.get('api/getUser')

    def get_active_bets(self):
        return self.get('api/getActiveBets')

    def get_user_notifications(self):
        return self.get('api/getUserNotifications')

    def beg(self):
        return self.post('api/logBeg')

    def place_bet(self, amount, team, game):
        payload = {}
        payload['amount'] = amount
        payload['entityId'] = team
        payload['gameId'] = game
        payload['type'] = 'winner'
        payload['userId'] = self.user_id
        return self.post('api/bet', payload)

    def bet_on(self, games):
        for g in games:
            if g['id'] in self.bets:
                print("Already bet on game, skipping")
            elif self.monies <= 0:
                print("Out of money, begging")
                b = self.beg()
                print(b['message'])
                self.monies = self.monies + b['amount']
            else:
                print("Placing bet....")
                # TODO: add logic for calculating games
                amount = min(self.monies, BET_AMOUNT)
                team = WhichTeam.compute_bet(g)
                d = place_bet(amount, team, g['id'])

                # If bet worked, update and place
                if d['message'] == "Bet placed":
                    self.monies = self.monies - amount
                    self.bets.append(g['id'])

                print(d['message'])

    def connect_to_event_stream(self):
        r = requests.get('https://www.blaseball.com/events/streamData', cookies=GLOBAL_COOKIES, stream=True)
        for line in r.iter_lines():
            # filter out keep-alive new lines
            if line:
                decoded_line = line.decode('utf-8')
                data = json.loads(decoded_line.replace("data: ", ""))
                upcoming_games = data['value']['games']['tomorrowSchedule']
                self.bet_on(upcoming_games)

if __name__=='__main__':
    BlaseIt()