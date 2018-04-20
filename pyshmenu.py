#!/usr/bin/env python
import os
import sys
import argparse
import curses 

stdscr = None

def init():

        stdscr = curses.initscr()
        curses.start_color()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)

        return stdscr

def fini():
    curses.nocbreak()
    curses.echo()
    curses.endwin()

class Menu:
    '''
    Simple Menu class to show menu entries on system where ncurses is available

    '''

    win = None
    entries = None
    normal = None
    marked = None

    posx = 0
    posy = 0
    width  = None
    height = None
    n_data_rows = 0    # max width of data
    n_data_cols = 0    # max height of data
    row_selected = 0
    frame  = 0 


    # *****************************************
    #
    # init 
    #   border:
    #     0 - no border
    #     1 - default border
    #
    # *****************************************
    def __init__(self, stdscr, entries, posx = -1, posy = -1, width=None, height=None, border = 0):

        (maxy, maxx) = stdscr.getmaxyx()
        self.width  = min(width,  maxx) if width  else maxx
        self.height = min(height, maxy) if height else maxy


        if border > 0:
            self.frame = 1

        # calculate max width of data - number of columns
        for entry in entries:
            if len(entry) > self.n_data_cols:
                self.n_data_cols = len(entry)

        # calculate max height - number of rows
        self.n_data_rows = len(entries)

        # init window
        self.entries = entries

        # Hint: in case without border the width must be incremented 
        # by one otherwise addstr generate error in last row
        height = self.n_data_rows + 2 * self.frame 
        width  = self.n_data_cols + 1 + 1 * self.frame 
        self.posx = posx if posx > -1 else (maxx - width)  / 2 
        self.posy = posy if posy > -1 else (maxy - height) / 2

        self.win = curses.newwin(height,
                                 width,
                                 self.posy, 
                                 self.posx)
        if border == 1:
            self.win.border()
        elif border == 2:
            self.win.border('|', '|', '-', '-', '+', '+', '+', '+')
        
        # init attributes
        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
            self.normal = curses.color_pair(1)
            self.marked = curses.color_pair(2)
        else:
            self.normal = curses.A_NORMAL #color_pair(curses.A_NORMAL)
            self.marked = curses.A_REVERSE #color_pair(curses.A_UNDERLINE)

        # select current row (highlitet)
        self.row_selected = self.frame # in the beginning 1st row is selected

        self.update_window()


    # *****************************************
    # Redraw windows:
    #  - redraw current line with marked background
    #  - redraw other lines with normal background
    #  - position cursor in valid place
    #
    # *****************************************
    def update_window(self):

        # Fill the window
        row = self.frame
        col = self.frame

        idx = 0
        while idx < len(self.entries):
            row = idx + self.frame
            self.win.addnstr(row, col, 
                            "%-*s" % (self.n_data_cols, self.entries[idx]), 
                            self.n_data_cols,
                            self.marked if row == self.row_selected else self.normal)
           #self.win.addnstr(row, col, "x", self.n_data_cols, self.normal)
            idx += 1

        self.win.move(self.row_selected, self.frame)

        self.win.refresh()

        return

    # *****************************************
    #
    # Moving cursor in vertical direction
    #   dir:
    #     -1 - up
    #     +1 - down
    #
    # *****************************************
    def cursor_v(self, dir):
        (row, col) = self.win.getyx()
        
        row = row + dir 
        if row < self.frame:
            row = self.n_data_rows - 1
        elif row >= self.n_data_rows + self.frame:
            row = self.frame
        self.row_selected = row

        self.update_window()

        return


    # *****************************************
    #
    # activity loop
    #
    # *****************************************
    def loop(self):
        position = 1

        self.win.keypad(1)
        while True:
            char = self.win.getch()
            if char == ord('q') or char == ord('Q'):
                #position = None
                return None
            elif char == 27:
                position = None
                break
            elif char == curses.KEY_UP:
               self.cursor_v(-1)
            elif char == curses.KEY_DOWN:
               self.cursor_v(+1)
            elif char == 10: #curses.KEY_ENTER
               position = self.win.getyx()[0]
               break
        self.win.keypad(0)
        return position - self.frame


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Simple mneu using python and curses')
    parser.add_argument('-f', '--file')
    parser.add_argument('-t', '--type', choices=['index', 'value'], default='index')
    parser.add_argument('-x', '--posx', type=int, default=-1)
    parser.add_argument('-y', '--posy', type=int, default=-1)
    parser.add_argument('-b', '--border', type=int, default=0)
    parser.add_argument('positional', nargs='*')

    args = parser.parse_args()
    out = None

    entries = []
    # Evaluating menu values
    # possible sources:
    #   file           - name taken from args
    #   commnad line   - all not keyword paramaters
    #   standard input - if no not-keyword paramaters 

    if args.file:
        # Read from file
        menufile = open(args.file)
        for line in menufile:
            entries.append(line[:-1])
        menufile.close()
    elif len(args.positional) > 0:
        # Read from command line    
        for line in args.positional:
            entries.append(line)
    else:
        # Try to read from stdin until EOF
        line = sys.stdin.readline()
        while len(line) > 1:
            entries.append(line[:-1])
            line = sys.stdin.readline()
        #termname = os.ttyname(sys.stdout.fileno())
        # Close the stdin file descriptor ...
        os.close(0);
        # ... end open again - as terminal
        # curses lib use 0 fd as input
        # Used as:
        # ./pyshmenu.sh <<EOF
        #   entry1
        #   entry2
        #   ....
        #   entryN
        # EOF 
        #
        sys.stdin = open('/dev/tty', 'r')
        sys._stdin = sys.stdin

        fd = os.dup(1)
        out = os.fdopen(fd, 'w')
        os.close(1)
        sys.stdout = open('/dev/tty', 'w')
        sys._stdout = sys.stdout


    position = None

    if len(entries) > 0:
        try:    
            stdscr = init()
            m = Menu(stdscr, entries, 
                     posx = args.posx, posy = args.posy, 
                     border = args.border)
            position = m.loop()
            fini()
        except curses.error as ex:
            curses.endwin()
            print(ex)


        if position and position >= 0:
            if args.type == 'index':
                print >> out, position  
                if out:
                    out.flush()
                #out.close()
                #print(position)
            elif args.type == 'value':
                if position >= 0: 
                    print >> out, entries[position]  
                    if out:
                        out.flush()
        else:
            sys.exit(1) 

    else:
        sys.exit(1)

