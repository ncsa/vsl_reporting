import grab
import logging
import datetime
import tzlocal
import string
import re
import pyexch

import getpass
import pprint

LOGR = logging.getLogger(__name__)
LOGR.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s [%(filename)s:%(funcName)s:%(lineno)s] %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
LOGR.addHandler(ch)


class VSL_Reporter( object ):

    #URL = 'https://internal.ncsa.illinois.edu/'
    MIDNIGHT = { 'hour': 0, 'minute': 0, 'second': 0 }
    URL = 'https://internal.ncsa.illinois.edu/mis/vsl/'
    MONTH_URL = string.Template( (
        'https://internal.ncsa.illinois.edu/mis/vsl/index.php'
        '?content=month'
        '&time_v=$timev' ) )
    DAY_URL = string.Template( ( 
        'https://internal.ncsa.illinois.edu/mis/vsl/index.php'
        '?content=form'
        '&time_v=$timev'
        '&day_v=$dayv' ) )


    def __init__( self, username, password, *a, **k ):
        self.user = username
        self.passwd = password
        self.userpwd = '{}:{}'.format( username, password )
        self.g = grab.Grab( userpwd=self.userpwd )
        self.tz = tzlocal.get_localzone() # get pytz timezone


    def ts2datetime( self, ts ):
        return datetime.datetime.fromtimestamp( float( ts ), self.tz )

    def _go( self, url, outfn=None ):
        self.g.go( url )
        LOGR.debug( 'CODE: {}'.format( self.g.doc.code ) )
        LOGR.debug( 'HDRS: {}'.format( pprint.pformat( self.g.doc.headers ) ) )
        if outfn:
            self.g.doc.save( outfn )


    def _get_cycle_start( self, the_date ):
        ''' Cycle runs from 16th of month 1 to 15th of month 2
            Return cycle start date
            for the cycle that the_date falls within
        '''
        if the_date.day == 16:
            start_date = the_date
        elif the_date.day > 16:
            diff = datetime.timedelta( days=(the_date.day - 16) )
            start_date = the_date - diff
        else: #the_date.day < 16
            # calc shortest diff to 16th day of previous month 
            # shortest month is 28 days, so smallest possible diff is 28 - 16 = 12,
            # which is true if the_date = 1st Mar
            diff = datetime.timedelta( days=( the_date.day + 11 ) )
            start_date = the_date - diff
            adjustment = start_date.day % 16
            diff = datetime.timedelta( days=( the_date.day + 11 + adjustment ) )
            start_date = the_date - diff
        return start_date


    def _get_cycle_end( self, the_date ):
        ''' Cycle runs from 16th of month 1 to 15th of month 2
            Return cycle end date
            for the cycle that the_date falls within
        '''
        if the_date.day == 15:
            end_date = the_date
        elif the_date.day < 15:
            diff = datetime.timedelta( days=( 15 - the_date.day ) )
            end_date = the_date + diff
        else: #the_date.day > 15
            # shortest diff to 15th day of next month is 15
            # which is true if the_date = last day of the month
            d1 = the_date + datetime.timedelta( days=15 )
            if d1.day == 15:
                end_date = d1
            elif d1.day < 15:
                adjustment = 15 - d1.day
                end_date = d1 + datetime.timedelta( days=adjustment )
            else:
                d2 = d1 + datetime.timedelta( days=15 )
                adjustment = 15 - d2.day
                end_date = d2 + datetime.timedelta( days=adjustment )
        return end_date


    def _mk_month_url( self, the_date ):
        ts_month = self._get_cycle_start( the_date ).timestamp()
        new_url = self.MONTH_URL.substitute( timev=ts_month )
        LOGR.debug( 'URL: {}'.format( new_url ) )
        return new_url


    def _mk_day_url( self, the_date ):
        data = { 'timev': self._get_cycle_start( the_date ).timestamp(),
                 'dayv': the_date.timestamp(),
               }
        new_url = self.DAY_URL.substitute( data )
        return new_url


    def get_overdue_months( self ):
        """ Only gets first (oldest) overdue month right now
        """
        #today = datetime.datetime.now( tz=self.tz ).replace( **self.MIDNIGHT )
        #url = self._mk_month_url( today )
        #self._go( url, outfn='00_month.html' )
        self._go( self.URL, outfn='00_month.html' )
        #pprint.pprint( self.g.doc.tree )
        # this negative lookahead regex magic groc'd from http://www.perlmonks.org/?node_id=188907
        re_pattern = 'a href=[^>]*content=month&time_v=([0-9]+)(?:(?!<\/tr>).)*Overdue'
        re_overdue = re.compile( re_pattern, re.DOTALL )
        match_overdue = self.g.doc.rex_text( re_overdue )
        LOGR.debug( match_overdue )
        return match_overdue
        #LOGR.debug( self.g.doc.tree )


    def load_date( self, the_date ):
        url = self._mk_day_url( the_date )
        LOGR.debug( 'DAY URL: {}'.format( url ) )
        self._go( url, outfn='01_day.html' )

def run():
    user = 'aloftus'
    with open( '/home/aloftus/.ssh/imap_illinois_edu', 'r' ) as f:
        for l in f:
            pwd = l.rstrip()
            break
    vsl = VSL_Reporter( user, pwd )
    overdue_ts = vsl.get_overdue_months()
    overdue_month_start = vsl.ts2datetime( overdue_ts )
#    overdue_month_end = vsl._get_cycle_end( overdue_month_start )
 
    # Get sick / vacation info from Exchange
    domain_user = 'UOFI\\{}'.format( user )
    email = '{}@illinois.edu'.format( user )
    px = pyexch.PyExch( user=domain_user, email=email, pwd=pwd )
    #events = px.get_events_filtered( overdue_month_start )
    #pprint.pprint( events )
    days_report = px.per_day_report( overdue_month_start )
    pprint.pprint( days_report )

if __name__ == '__main__':
    run()
