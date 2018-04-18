#!/usr/bin/env python
import os
import sys
import argparse
import curses 

stdscr = None

def init():

    global stdscr

    if not stdscr:
        stdscr = curses.initscr()
        curses.start_color()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)

def fini():
    curses.nocbreak()
    curses.echo()
    curses.endwin()

class Menu:
    '''
    Simple Menu class to show menu entries on system where ncurses is available

    '''

    win = None
    brd = None
    entries = None
    normal = None
    marked = None

    posx = 5
    posy = 4
    width  = 0
    height = 0
    frame  = 1 


    # *****************************************
    #
    # init 
    #
    # *****************************************
    def __init__(self, entries, posx = 0, posy = 0, border = True):
        # checking max size of the line
        self.width = 0
        self.posx = posx
        self.posy = posy

        if border:
            self.frame = 1

        # calculate max width
        for entry in entries:
            if len(entry) > self.width:
                self.width = len(entry)

        # calculate max height
        self.height = len(entries)
        screen_w = stdscr.getmaxyx()[1]

        # init window
        self.entries = entries

        self.win = curses.newwin(self.height + 2 * self.frame, 
                                 self.width  + 2 * self.frame, 
                                 self.posy, 
                                 self.posx)
        if border > 0:
            self.win.border()
        
        # init attributes
        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
            self.normal = curses.color_pair(1)
            self.marked = curses.color_pair(2)
        else:
            self.normal = curses.A_NORMAL #color_pair(curses.A_NORMAL)
            self.marked = curses.A_REVERSE #color_pair(curses.A_UNDERLINE)

        # Fill the window
        row = 0
        for entry in entries:
            self.win.addstr(row + self.frame, 0 + self.frame, 
                            "%-*s" % (self.width, entry), 
                            self.marked if row == 0 else self.normal)
            row += 1
        # move cursor
        self.win.move(self.frame, self.frame)

        self.win.refresh()


    # *****************************************
    #
    # Moving cursor in vertical direction
    #   dir:
    #     -1 - up
    #     +1 - down
    #
    # *****************************************
    def cursor_v(self, dir):
        (my, mx) = self.win.getmaxyx()
        my -= self.frame
        mx -= self.frame
        (cy, cx) = self.win.getyx()
        
        self.win.addstr(cy + 0, 0 + self.frame,# cy, 0, 
                        "%-*s" % (self.width, self.entries[cy - 1]), 
                        self.normal)         
        cy = cy + dir 
        if cy < self.frame:
            cy = my - 1
        elif cy >= my:
            cy = 1
        self.win.addstr(cy + 0, 0 + self.frame,# cy, 0, 
                        "%-*s" % (self.width, self.entries[cy - 1]), 
                        self.marked)         
        self.win.move(cy, cx)
        self.win.refresh()

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
                position = None
                break
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
    parser.add_argument('-b', '--box', type=bool, default=True)
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
            init()
            m = Menu(entries, posx = 25, posy = 19, border = True)
            position = m.loop()
        except:
            pass

        fini()

        if position >= 0:
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

