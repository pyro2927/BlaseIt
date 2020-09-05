#!/usr/bin/env python
import curses
from main import BlaseIt
from collections import deque
from time import sleep

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

def main(stdscr):
    stdscr.clear()
    stdscr.border()
    curses.curs_set(0)

    b = BlaseIt()
    t = Ticker(b.get_events(), stdscr)
    while True:
        t.tick()
        stdscr.refresh()
        sleep(0.5)

if __name__ == '__main__':
    curses.wrapper(main)