#!/usr/bin/env python
dbg = None

class Dbg:

    dbg = None

    def __init__(self, outfile):
            self.dbg = open(outfile, "wt")

    def out(self, value):
        if self.dbg: 
            self.dbg.write(value)
            self.dbg.flush()
class DbgNull:


    def __init__(self):
        pass

    def out(self, value):
        pass

