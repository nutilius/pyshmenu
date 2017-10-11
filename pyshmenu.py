#!/usr/bin/env python
import sys
import argparse
import curses 


class Menu:

    win = None
    entries = None
    normal = None
    marked = None


    def __init__(self, entries):
        # Init window
        self.entries = entries
        self.win = curses.newwin(len(entries), stdscr.getmaxyx()[1])
        
        # init attributes
        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
            self.normal = curses.color_pair(1)
            self.marked = curses.color_pair(2)
        else:
            self.normal = curses.A_NORMAL #color_pair(curses.A_NORMAL)
            self.marked = curses.A_REVERSE #color_pair(curses.A_UNDERLINE)

        # Fulfill window
        col = 0
        for entry in entries:
            self.win.addstr(col, 0, entry, self.marked if col == 0 else self.normal)
            col += 1
        self.win.move(0, 0)
        self.win.refresh()


    def cursor_v(self, dir):
        (my, mx) = self.win.getmaxyx()
        (cy, cx) = self.win.getyx()
        
        self.win.addstr(cy, 0, self.entries[cy], self.normal)         
        cy = cy + dir 
        if cy < 0 :
            cy = my - 1
        elif cy >= my:
            cy = 0
        self.win.addstr(cy, 0, self.entries[cy], self.marked)         
        self.win.move(cy, cx)
        self.win.refresh()

        return



    def loop(self):
        position = None

        self.win.keypad(1)
        while True:
            char = self.win.getch()
            if char == ord('q') or char == ord('Q'):
                break
            elif char == 27:
                break
            elif char == curses.KEY_UP:
               self.cursor_v(-1)
            elif char == curses.KEY_DOWN:
               self.cursor_v(+1)
            elif char == 10: #curses.KEY_ENTER
               position = self.win.getyx()[0]
               break
        self.win.keypad(0)
        return position


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Simple mneu using python and curses')
    parser.add_argument('-f', '--file')
    parser.add_argument('-t', '--type', choices=['index', 'value'], default='index')
    parser.add_argument('positional', nargs='*')

    args = parser.parse_args()

    entries = []
    # Evaluating menu values

    if args.file:
        # Read from file
        menufile = open(args.file)
        for line in menufile:
            entries.append(line[:-1])
        menufile.close()
    elif len(args.positional) > 0:
        # READ from command line    
        for line in args.positional:
            entries.append(line)
    else:
        # Try to read from stdin
        for line in sys.stdin:
            print(line)
            if len(line[:-1]) > 0:
                entries.append(line[:-1])
            else:
                break


    if len(entries) > 0:
        stdscr = curses.initscr()
        curses.start_color()
        curses.noecho()
        curses.cbreak()
        
        m = Menu(entries)
        position = m.loop()


        curses.nocbreak()
        curses.echo()

        curses.endwin()

        if args.type == 'index':
            print(position)
        elif args.type == 'value':
            if position: 
                print(entries[position])
    else:
        sys.exit(1)

