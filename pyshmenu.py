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


try:
    from debug import Dbg, DbgNull
except:
    class DbgNull:
        def out(self, msg):
            pass

dbg = None


# *********************************************************
#
#
#
# *********************************************************
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
    w_width  = None    # window height (with optional title and border)
    w_height = None    # window width (with optional title and border)
    #
    v_width  = None    # view height
    v_height = None    # view width
    v_top    = None    # view upper y coord (in window coordinates)
    v_bottom = None

    frame  = 0 
    header = 0
    #
    n_data_rows = 0    # max height of data
    n_data_cols = 0    # max width  of data
    data_pos_x = 0     # x position in data box
    data_pos_y = 0     # y position in data box
    row_selected = 0
    min_y = 0


    title = "Sel:"
    headstr = ""


    # *****************************************
    #
    #
    #
    # *****************************************
    def __init__(self, entries, header = 0):

        dbg.out("entries=%d\n" % len(entries))
        # init window
        if header:
            self.header = header
            self.headstr = entries[0]
            self.entries = entries[self.header:]
        else:
            self.entries = entries

        dbg.out("entries=%d\n" % len(self.entries))
        # calculate max width of data - number of columns
        for entry in entries:
            if len(entry) > self.n_data_cols:
                self.n_data_cols = len(entry)
        self.n_data_cols -= self.frame

        # calculate max height - number of rows
        self.n_data_rows = len(self.entries)


    # *****************************************
    #
    #   border:
    #     0 - no border
    #     1 - default border
    #
    # *****************************************
    def show(self, stdscr, posx = -1, posy = -1, width=None, height=None, border = 0, header = None):

        (maxy, maxx) = stdscr.getmaxyx()

        if border > 0:
            self.frame = 1

        # corrections of maxx and maxy based on posx and posy
        if posy > 0 and posy < maxy - 1:
            maxy = maxy - posy
        else:
            posy = 0
        if posx > 0 and posx < maxx - 1:
            maxx = maxx - posx
        else:
            posx = 0
        
        dbg.out("*****Debug*****\n")

        # Calculating height of window (with optional border and title)
        # correction for border and header
        if height:
            height = height + 2 * self.frame + self.header
        # select maximal possible window height 
        self.w_height = min(height, maxy) if height else maxy
        self.w_height = min(self.w_height, self.n_data_rows + 2 * self.frame + 1 * self.header)
        dbg.out("maxx=%d maxy=%d\n" % (maxx, maxy))

        # Hint: in case without border the width must be incremented 
        # by one otherwise addstr generate error in last row
        if width:
            self.w_width = min(width, self.n_data_cols + 1 + 2 * self.frame) 
        else:
            self.w_width = min(maxx, self.n_data_cols + 1 + 2 * self.frame)

        self.w_width = min(maxx, self.w_width)
        #dbg.out("width = %d height=%d\n" % (width, height))


        if posx == -1:
            self.posx = abs(maxx - self.w_width) / 2
        else:
            self.posx = posx
            #self.w_width = abs(self.w_width - posx)
        

        #self.posx = posx if posx > -1 else (maxx - width)  / 2 
        self.posy = posy if posy > -1 else (maxy - self.w_height) / 2


        # settings for view (on the screen) - only moving data
        #self.v_height = min(self.w_height - 2 * self.frame, self.n_data_rows - 2 * self.frame) 
        self.v_height = self.w_height - 2 * self.frame - self.header
        self.v_width = self.w_width - 2 * self.frame - 1
        #
        self.v_top = self.frame + self.header
        self.v_bottom = self.v_top + self.v_height - 1
        #self.v_bottom = self.w_height - self.frame

        # Update (adjust) header string to full view width
        self.headstr = "%-*.*s" % (self.v_width, self.v_width, self.headstr) 

        dbg.out("Window: h=%d w=%d x=%d y=%d\n" % (self.w_height, self.w_width, self.posx, self.posy))

        # init attributes
        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
            curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN)
            self.normal = curses.color_pair(1)
            self.marked = curses.color_pair(2)
            self.headattr = curses.color_pair(3)
        else:
            self.normal = curses.A_NORMAL #color_pair(curses.A_NORMAL)
            self.marked = curses.A_REVERSE #color_pair(curses.A_UNDERLINE)
            self.headattr = curses.A_REVERSE #color_pair(curses.A_UNDERLINE)

        try:
            self.win = curses.newwin(self.w_height,
                                     self.w_width,
                                     self.posy, 
                                     self.posx)
        except Exception as ex:
            print(ex)

        if border == 1:
            self.win.border()

        elif border == 2:
            self.win.border('|', '|', '-', '-', '+', '+', '+', '+')
        
        # Set otional title (only for window with frame)
        if border:
            if self.title:
                title_len = min(self.n_data_cols, len(self.title))
                self.win.addnstr(0, 1,
                                "%-*s" % (title_len, self.title), 
                                self.n_data_cols,
                                self.normal)
        # select current row (highlitet)
        self.row_selected = self.frame + self.header  # in the beginning 1st row is selected

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

        try:

            # Fill the window
            limit = self.v_height
            dbg.out("n_data_rows=%d w_height=%d v_height=%d\n" % (self.n_data_rows, self.w_height, self.v_height))


            if self.header:
                self.win.addnstr(row, col, 
                                self.headstr,
                                self.v_width ,
                                self.headattr)
            idx = 0
            entries = self.entries[self.data_pos_y : self.data_pos_y + self.v_height + 2]
            dbg.out("entries=%d\n" % len(entries))
            while idx < self.v_height:
                #row = idx + self.frame + self.header
                row = self.v_top + idx
                val = "%-*.*s" % (self.v_width, self.v_width, entries[idx]) 
                self.win.addnstr(row, col, 
                                val,
                                self.v_width ,#self.w_width - 2 * self.frame,
                                self.marked if row == self.row_selected else self.normal)
                dbg.out("idx=%d row=%d col=%d iWindow: h=%d w=%d l=%d \n" 
                        % 
                        (idx, row, col, self.w_height, self.w_width, len(val)))
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
    #
    #
    # *****************************************
    def cursor_b(self):
        
        self.data_pos_y = 0 
        self.row_selected = self.v_top

        #dbg.out("row=%d col=%d h=%d w=%d \n" % (row, col, self.w_height, self.w_width))

        self.update_window()

        return
       
    # *****************************************
    #
    #
    #
    # *****************************************
    def cursor_e(self):
        
        self.data_pos_y = self.n_data_rows - self.v_height
        self.row_selected = self.v_bottom #self.w_height - self.frame - 1

        #dbg.out("row=%d col=%d h=%d w=%d \n" % (row, col, self.w_height, self.w_width))

        self.update_window()

        return
       
    # *****************************************
    #
    #
    #
    # *****************************************
    def cursor_pu(self):
        (row, col) = self.win.getyx()
        
        self.data_pos_y = self.data_pos_y - self.w_height
        if self.data_pos_y < 0:
            self.data_pos_y = 0

        self.row_selected = self.v_top

        dbg.out("data_pos_y=%d, h=%d w=%d r=%d c=%d\n" % (self.data_pos_y, self.w_height, self.w_width, row, col))

        self.update_window()

        return

    # *****************************************
    #
    #
    #
    # *****************************************
    def cursor_pd(self):
        (row, col) = self.win.getyx()
        
        self.data_pos_y = self.data_pos_y + self.w_height
        if self.data_pos_y > self.n_data_rows - self.v_height:
            self.data_pos_y = self.n_data_rows - self.v_height

        self.row_selected = self.v_bottom

        dbg.out("data_pos_y=%d, h=%d w=%d r=%d c=%d\n" % (self.data_pos_y, self.w_height, self.w_width, row, col))

        self.update_window()

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

        #if row < self.frame:
        if row < self.v_top:
            # cursor out of display - move data window
            self.data_pos_y = self.data_pos_y - 1
            if self.data_pos_y < 0:
                self.data_pos_y = 0 
            row = self.v_top
                
        #elif row >= self.w_height - self.frame:
        elif row >= self.v_bottom:
            self.data_pos_y = self.data_pos_y + 1
            if self.data_pos_y > self.n_data_rows - self.v_height:
                self.data_pos_y = self.n_data_rows - self.v_height
            #row = self.w_height - self.frame - 1
            row = self.v_bottom


        self.row_selected = row

        dbg.out("data_pos_y=%d, h=%d w=%d r=%d c=%d\n" % (self.data_pos_y, self.w_height, self.w_width, row, col))

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
                return None
            elif char == 27:
                return None
            elif char == curses.KEY_UP:
               self.cursor_v(-1)
            elif char == curses.KEY_DOWN:
               self.cursor_v(+1)
            elif char == curses.KEY_HOME:
               self.cursor_b()
            elif char == curses.KEY_END:
               self.cursor_e()
            elif char == curses.KEY_PPAGE:
               self.cursor_pu()
            elif char == curses.KEY_NPAGE:
               self.cursor_pd()
            elif char == 10: #curses.KEY_ENTER
               position = self.win.getyx()[0] + self.data_pos_y
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
    # Simple method for fast displaying menu
    #  - init curses
    #  - display menu
    #  - fini curses
    # *****************************************
    def fast(entries, posx = -1, posy = -1, width=None, height=None, border = 0, header = 0):
        try:    
            stdscr = Menu.init_curses()
            m = Menu(entries, header)
            m.show(stdscr, posx, posy, width, height, border)
            position = m.loop()
            Menu.fini_curses()
            return position
        except curses.error as ex:
            Menu.fini_curses()
            return None

    # Make fast static method
    fast = staticmethod(fast)

# **********************************************
#
#
#
# **********************************************

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Simple mneu using python and curses')
    parser.add_argument('-f', '--file')
    parser.add_argument('-t', '--type', choices=['index', 'value'], default='index')
    parser.add_argument('-x', '--posx', type=int, default=-1)
    parser.add_argument('-y', '--posy', type=int, default=-1)
    parser.add_argument('-w', '--width', type=int)
    parser.add_argument('-l', '--header', type=int, default=0)
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
        dbg = Dbg(args.dbg)
    else:
        dbg = DbgNull()

    position = None

    if len(entries) > 0:

        position = Menu.fast(entries, posx = args.posx, posy = args.posy, 
                             border = args.border, header = args.header, width=args.width)
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

