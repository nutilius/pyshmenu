#!/usr/bin/env python
import os
import sys
import argparse
import curses 


# *********************************************************************
# 
#  Example usage 
#       try:    
#           # Otional init curses
#           stdscr = MenuFast.init_curses()
#           m = Menu(stdscr, entries, 
#                    posx = args.posx, posy = args.posy, 
#                    border = args.border)
#           position = m.loop()
#           # Optional close curses
#           MenuFast.fini_curses()
#       except curses.error as ex:
#           curses.endwin()
#           print(ex)
# *********************************************************************


from debug import Dbg, DbgNull
dbg = None


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
    n_data_rows = 0    # max height of data
    n_data_cols = 0    # max width  of data
    row_selected = 0
    frame  = 0 
    datapos_x = 0
    datapos_y = 0 

    title = "Sel:"


    # *****************************************
    #
    #
    #
    # *****************************************
    def __init__(self, entries):

        # init window
        self.entries = entries

        # calculate max width of data - number of columns
        for entry in entries:
            if len(entry) > self.n_data_cols:
                self.n_data_cols = len(entry)
        self.n_data_cols -= self.frame

        # calculate max height - number of rows
        self.n_data_rows = len(entries)


    # *****************************************
    #
    #   border:
    #     0 - no border
    #     1 - default border
    #
    # *****************************************
    def show(self, stdscr, posx = -1, posy = -1, width=None, height=None, border = 0):

        (maxy, maxx) = stdscr.getmaxyx()
        #maxx -= 1
        #maxy -= 1
        
        
        #self.width  = min(width,  maxx) if width  else maxx
        dbg.out("*****Debug*****\n")
        self.height = min(height, maxy) if height else maxy
        dbg.out("maxx=%d maxy=%d\n" % (maxx, maxy))

        if border > 0:
            self.frame = 1


        # Hint: in case without border the width must be incremented 
        # by one otherwise addstr generate error in last row
        if width:
            self.width = min(width, self.n_data_cols + 1 + 1 * self.frame) 
        else:
            self.width = min(maxx, self.n_data_cols + 1 + 1 * self.frame)

        self.width = min(maxx, self.width)
        #dbg.out("width = %d height=%d\n" % (width, height))

        #height = self.n_data_rows + 2 * self.frame 

        if posx == -1:
            self.posx = abs(maxx - self.width) / 2
        else:
            self.posx = posx
            self.width = abs(self.width - posx)
        

        #self.posx = posx if posx > -1 else (maxx - width)  / 2 
        self.posy = posy if posy > -1 else (maxy - self.height) / 2



        dbg.out("h=%d w=%d x=%d y=%d\n" % (self.height, self.width, self.posx, self.posy))

        # init attributes
        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
            self.normal = curses.color_pair(1)
            self.marked = curses.color_pair(2)
        else:
            self.normal = curses.A_NORMAL #color_pair(curses.A_NORMAL)
            self.marked = curses.A_REVERSE #color_pair(curses.A_UNDERLINE)

        try:
            self.win = curses.newwin(self.height,
                                     self.width,
                                     self.posy, 
                                     self.posx)
            #self.win = curses.newwin(20,
            #                         self.posy, 
            #                         1,
            #                         1)
        except Exception as ex:
            print(ex)

        if border == 1:
            self.win.border()

            if self.title:
                title_len = min(self.n_data_cols, len(self.title))
                self.win.addnstr(0, 1,
                                "%-*s" % (title_len, self.title), 
                                self.n_data_cols,
                                self.normal)
        elif border == 2:
            self.win.border('|', '|', '-', '-', '+', '+', '+', '+')
        
        # select current row (highlitet)
        self.row_selected = self.frame # in the beginning 1st row is selected

        #self.win.refresh()
        self.update_window()


    # *****************************************
    # Redraw windows:
    #  - redraw current line with marked background
    #  - redraw other lines with normal background
    #  - position cursor in valid place
    #
    # *****************************************
    def update_window(self):

        row = self.frame
        col = self.frame
        val = None
        lval = None

        idx = 0

        try:

            # Fill the window
            #while idx < len(self.entries):
            limit = min(self.height - 2 * self.frame, self.n_data_rows - 2 * self.frame) 
            dbg.out("n_data_rows=%d\n" % self.n_data_rows)
            dbg.out("height=%d\n" % self.height)
            dbg.out("limit=%d\n" % limit)
            while idx < limit:
                row = idx + self.frame
                #self.win.addnstr(row, col, 
                #                "%-*s" % (self.n_data_cols, self.entries[idx]), 
                #                self.n_data_cols,
                #                self.marked if row == self.row_selected else self.normal)
                maxl = self.width - 2 * self.frame - 1
                #val = self.entries[idx][:maxl]
                val = "%-.*s" % (self.width - 2 * self.frame - 1, self.entries[idx]) 
                self.win.addnstr(row, col, 
                                val,
                                self.width - 2 * self.frame,
                                self.marked if row == self.row_selected else self.normal)
               #self.win.addnstr(row, col, "x", self.n_data_cols, self.normal)
                dbg.out("idx=%d row=%d col=%d h=%d w=%d l=%d maxl=%d\n" % (idx, row, col, self.height, self.width, len(val), maxl))
                idx += 1

            dbg.out("limit=%d\n" % limit)
            self.win.move(self.row_selected, self.frame)

            self.win.refresh()

        except curses.error as ex:
            Menu.fini_curses()

            print("idx=%d row=%d col=%d len=%d val=>%s<\n" % (idx, row, col, len(val), val))
            print(ex)
            print(curses.ERR)
            sys.exit(1)

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
            row = self.height - 1 - self.frame
            #row = self.n_data_rows - 1
        elif row >= self.height - self.frame:
            row = self.frame
        self.row_selected = row

        self.update_window()

        dbg.out("h=%d w=%d r=%d c=%d\n" % (self.height, self.width, row, col))


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
                return None
            elif char == curses.KEY_UP:
               self.cursor_v(-1)
            elif char == curses.KEY_DOWN:
               self.cursor_v(+1)
            elif char == 10: #curses.KEY_ENTER
               position = self.win.getyx()[0]
               break
        self.win.keypad(0)
        return position - self.frame

    # *****************************************
    #
    #
    #
    # *****************************************
    def init_curses():
            stdscr = curses.initscr()
            curses.start_color()
            curses.noecho()
            curses.cbreak()
            curses.curs_set(0)

            return stdscr
    # make method static
    init_curses = staticmethod(init_curses)

    # *****************************************
    #
    #
    #
    # *****************************************
    def fini_curses():
        curses.nocbreak()
        curses.echo()
        curses.endwin()

    # make method static
    fini_curses = staticmethod(fini_curses) 

    # *****************************************
    #
    #
    #
    # *****************************************
    def fast(entries, posx = -1, posy = -1, width=None, height=None, border = 0):
        try:    
            stdscr = Menu.init_curses()
            m = Menu(entries)
            m.show(stdscr, posx, posy, width, height, border)
            position = m.loop()
            Menu.fini_curses()
            return position
        except curses.error as ex:
            Menu.fini_curses()
            return None

    # Make fast static method
    fast = staticmethod(fast)

# *********************************************************************
#
#
#
#
#
# *********************************************************************
class MenuFast():

    stdscr = None
    entries = None

    def __init__(self, entries):
        self.entries = entries

    def init_curses(self):
            self.stdscr = curses.initscr()
            curses.start_color()
            curses.noecho()
            curses.cbreak()
            curses.curs_set(0)

            return self.stdscr

    def fini_curses(self):
        curses.nocbreak()
        curses.echo()
        curses.endwin()

    def show(self, posx = -1, posy = -1, width=None, height=None, border = 0):
        try:    
            stdscr = self.init_curses()
            m = Menu(stdscr, self.entries, posx, posy, width, height, border)
            position = m.loop()
            self.fini_curses()
            return position
        except curses.error as ex:
            self.fini_curses()
            return None
            #print(ex)


# *****************************************
#
#
#
# *****************************************

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Simple mneu using python and curses')
    parser.add_argument('-f', '--file')
    parser.add_argument('-t', '--type', choices=['index', 'value'], default='index')
    parser.add_argument('-x', '--posx', type=int, default=-1)
    parser.add_argument('-y', '--posy', type=int, default=-1)
    parser.add_argument('-w', '--width', type=int)
    parser.add_argument('-b', '--border', type=int, default=0)
    parser.add_argument('-d', '--dbg' )
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

        
    if args.dbg:
        print("Debug!")
        dbg = Dbg(args.dbg)
    else:
        dbg = DbgNull()

    position = None

    if len(entries) > 0:

        position = Menu.fast(entries, posx = args.posx, posy = args.posy, border = args.border, width=args.width)
        if position == None:
            sys.exit(1) 
        else:
            if args.type == 'index':
                print >> out, position  
                if out:
                    out.flush()
                #out.close()
            elif args.type == 'value':
                #if position >= 0: 
                print >> out, entries[position]  
                if out:
                    out.flush()

    else:
        sys.exit(1)

