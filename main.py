#!/usr/bin/env python
import json
import requests
from collections import deque

GLOBAL_COOKIES={'connect.sid': 'PUT_YOUR_COOKIE_HERE'}
BET_AMOUNT=20
ALWAYS_BET_ON=['Sunbeams', 'Moist Talkers', 'Firefighters']

class Team:

    def __init__(self, new_name, new_id, new_odds):
        self.name = new_name
        self.id = new_id
        self.odds = new_odds

    @staticmethod
    def from_game(g):
        away = Team(g['awayTeamNickname'], g['awayTeam'], g['awayOdds'])
        home = Team(g['homeTeamNickname'], g['homeTeam'], g['homeOdds'])
        return [away, home]

class WhichTeam:
    # returns the team to bet on for a given game object
    @staticmethod
    def compute_bet(teams):
        # Check to see if our favorites are playing, in order
        for t in ALWAYS_BET_ON:
            for t2 in teams:
                if t == t2.name:
                    return t2
        # No favorites, return team with highest odds
        teams.sort(key=lambda x:x.odds, reverse=True)
        return teams[0]

class BlaseIt:

    def __init__(self):
        self.events = deque(self.get_events())
        # initial user info load
        me = self.user_info()
        self.monies = me['coins']
        self.user_id = me['id']
        # then active bets
        self.bets = [x['gameId'] for x in self.get_active_bets()]
        # check notifications
        self.get_and_show_notifications()
        # then start streaming and betting
        print("Starting with " + str(self.monies) + " coins")
        print("Connecting to event stream...")
        self.connect_to_event_stream()
        # TODO: handle requests.exceptions.ChunkedEncodingError

    def get_and_show_notifications(self):
        notifications = self.get_user_notifications()['notes']
        for n in notifications:
            print(n['message'])

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

    def get_events(self):
        return self.get('database/globalEvents')

    def get_user_rewards(self):
        return self.get('api/getUserRewards')

    def get_user_notifications(self):
        return self.get('api/getUserNotifications')

    def clear_user_notifications(self):
        return self.post('api/clearUserNotifications')

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
                # TODO: have better debug logging
                # print("Already bet on game, skipping")
                continue
            elif self.monies <= 0:
                print("Out of money, begging")
                b = self.beg()
                print(b['message'])
                if b['message'].startswith("You find"):
                    self.monies = self.monies + b['amount']
                else:
                    print("Error occurred begging for money")
            # as long as we have monies, bet
            if self.monies > 0:
                # TODO: add logic for calculating games
                amount = min(self.monies, BET_AMOUNT)
                teams = Team.from_game(g)
                winner = WhichTeam.compute_bet(teams)
                print("Placing {} bet on {}....".format(str(amount), winner.name))

                d = self.place_bet(amount, winner.id, g['id'])
                # If bet worked, update and place
                if d['message'] == "Bet placed":
                    self.monies = self.monies - amount
                    self.bets.append(g['id'])
                else:
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
                # print random message after each iteration for fun
                self.events.rotate(1)
                print(self.events[0]['msg'])

if __name__=='__main__':
    BlaseIt()