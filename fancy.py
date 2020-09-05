#!/usr/bin/env python
import curses
from main import BlaseIt, Team, Bet
from collections import deque
from time import sleep

import struct

class BetStore:
    Bets = {}

    @staticmethod
    def add_bet(bet):
        Bets[bet.game_id] = bet

    @staticmethod
    def bet_for_game_id(gid):
        return Bets[gid]

class Ticker:

    def tick(self):
        self.screen.addstr(1, 1, "".join(self.events)[0:self.width])
        self.events.rotate(-1)

    def __init__(self, new_events, scr):
        # oneliner to turn array of dictionaries, strip out events,
        #  and prep them for rotation
        self.events = deque("     ".join([x['msg'] for x in new_events]))
        _, x = scr.getmaxyx()
        self.width = x - 2
        self.screen = scr

class ActiveGameDisplay:

    # 2 x 31 chars

    def tick(self):
        i = self.top
        for t in Team.from_game(self.game):
            self.screen.addstr(i, self.left, t.emoji)
            self.screen.addstr(i, self.left + 2, t.name)
            self.screen.addstr(i, self.left + 29, str(t.score))
            i = i + 1

    def __init__(self, new_game, scr, y, x):
        self.screen = scr
        self.game = new_game
        self.top = y
        self.left = x

class TomorrowGameDisplay:

    # 2 x 31 chars

    def tick(self):
        i = self.top
        for t in Team.from_game(self.game):
            self.screen.addstr(i, self.left, t.emoji)
            self.screen.addstr(i, self.left + 2, t.name)
            self.screen.addstr(i, self.left + 27, str(int(t.odds * 100)) + "%")
            i = i + 1

    def __init__(self, new_game, scr, y, x):
        self.screen = scr
        self.game = new_game
        self.top = y
        self.left = x


def main(stdscr):
    stdscr.clear()
    stdscr.border()
    curses.curs_set(0)

    b = BlaseIt()
    t = Ticker(b.get_events(), stdscr)

    # TODO: figure out right way to size these
    stdscr.addstr(3, 15, "TODAY")
    stdscr.addstr(3, curses.COLS - 20, "TOMORROW")
    for e in b.fake_event_stream():
        # TODO: template these out
        top = 4
        for g in e['value']['games']['schedule']:
            gd = ActiveGameDisplay(g, stdscr, top, 2)
            gd.tick()
            # slide down
            top = top + 4

        top = 4
        for g in e['value']['games']['tomorrowSchedule']:
            gd = TomorrowGameDisplay(g, stdscr, top, curses.COLS - 32)
            gd.tick()
            # slide down
            top = top + 4

        break

    while True:
        t.tick()
        stdscr.refresh()
        sleep(0.5)

if __name__ == '__main__':
    curses.wrapper(main)
