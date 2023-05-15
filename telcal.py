#! /usr/bin/env python

# Classes for reading VLA TelCal output files into python/sqlite data
# structures.
# P. Demorest, 2107/03

import string
import numpy
from collections import namedtuple
import sqlite3

telcaldir = '/home/mchammer/evladata/telcal/'

# Stores one or more lines of telcal gain (*.GN) results
# Note the order of field in this class needs to match the order in the
# TelcalDB class below for both to work togther.
class TelcalGN(namedtuple('TelcalGN',
    'mjd utc lst ifid freq ant amp phase resid delay flag zero source reason')):
    def __new__(cls,input):
        """Parse a .GN file line into the various fields."""
        try:
            line = input
            fields = line.split()
            mjd = float(fields[0])
            utc = fields[1]
            lst = float(fields[2])
            # Skip LST(h:m:s)
            ifid = fields[4]
            freq = float(fields[5])
            ant = fields[6]
            amp = float(fields[7])
            phase = float(fields[8])
            resid = float(fields[9])
            delay = float(fields[10])
            flag = (fields[11] == 'true')
            zero = (fields[12] == 'true')
            # skip HA, Az, El
            source = fields[16]
            if flag:
                reason = str.join(' ',fields[16:])
            else:
                reason = ''
            return super(TelcalGN,cls).__new__(cls, mjd, utc, lst, ifid, freq,
                    ant, amp, phase, resid, delay, flag, zero, source, reason)
        except AttributeError:
            # This allows filling the fields with, for example,
            # arrays of values rather than a single value.
            return super(TelcalGN,cls).__new__(cls, *input)

def read_telcal_file(fname):
    """Read a telcal GN file and return a list of results."""
    result = []
    for l in open(fname):
        try:
            tc = TelcalGN(l)
            result.append(tc)
        except (ValueError, IndexError):
            pass
    return result

class TelcalDB(object):
    def __init__(self,fname=None,basedir=telcaldir):
        self.db = sqlite3.connect(":memory:")
        c = self.db.cursor()
        # Note the order of fields here needs to match the order in the
        # TelcalGN defintion above for this to work.
        c.execute("""CREATE TABLE gn 
                (mjd real, utc text, lst real, ifid text, freq real, ant text, 
                amp real, phase real, resid real, delay real, 
                flag integer, zero integer, 
                source text, reason text)""")
        if fname is not None: self.load(basedir+'/'+fname)
        self.db.commit()

    def load(self,fname):
        c = self.db.cursor()
        gn = read_telcal_file(fname)
        c.executemany("INSERT INTO gn VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",gn)
        self.db.commit()

    #def get(self,cond=None,ant=None,ifid=None):
    def get(self,ants=[],strip=True,**kwargs):
        """
        Return fields listed in tuple 'what' as numpy arrays using
        stated 'where' condition.  If strip is True, bad (flagged
        or zeroed) results will not be included.
        """
        c = self.db.cursor()

        # Build up query
        where = ""
        for (k,v) in iter(kwargs.items()):
            where += " and %s='%s'" % (k, v)

        if len(ants):
            where += " and (ant='%s'" % ants[0]
            for a in ants[1:]:
                where += " or ant='%s'" % a
            where += ")"

        #if cond is not None:
        #    where += " and " + cond
        #if ant is not None: 
        #    where += " and ant='%s'" % ant
        #if ifid is not None:
        #    where += " and ifid='%s'" % ifid

        if strip:
            qry = "SELECT * from gn WHERE not flag and not zero" + where
        else:
            qry = "SELECT * from gn WHERE TRUE" + where
        c.execute(qry)
        rows = c.fetchall()
        ncol = 14 # number of columns; get automatically?
        stuff = [ numpy.array([ r[i] for r in rows ]) for i in range(ncol) ]
        return TelcalGN(stuff)

    def get_distinct(self,field):
        """Return list of unique values of given field."""
        c = self.db.cursor()
        c.execute("SELECT distinct %s from gn" % field)
        rows = c.fetchall()
        return [r[0] for r in rows] # de-tupleize

    @property
    def ants(self):
        """Return list of antennas"""
        return self.get_distinct('ant')

    @property
    def ifids(self):
        """Return list of IFs"""
        return self.get_distinct('ifid')

