import grab
import weblib.error
import logging
import datetime
import tzlocal
import string
import re

import pprint

LOGR = logging.getLogger(__name__)


class VSL_Reporter( object ):

    #URL = 'https://internal.ncsa.illinois.edu/'
    MIDNIGHT = { 'hour': 0, 'minute': 0, 'second': 0, 'microsecond': 0 }
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
        ''' Return datetime for midnight of the timestamp "ts"
        '''
#        return datetime.datetime.fromtimestamp( float( ts ), self.tz )
        dt = datetime.datetime.fromtimestamp( float( ts ), self.tz )
        return dt.replace( **(self.MIDNIGHT) )


    def date_as_midnight( self, thedate ):
        ''' Return a datetime for midnight of the day given in thedate.
            Input: datetime.date or datetime.datetime
        '''
        return datetime.datetime( thedate.year, thedate.month, thedate.day )

    def _go( self, url, outfn=None ):
        LOGR.debug( 'URL: {}'.format( url ) )
        self.g.go( url )
        LOGR.debug( 'CODE: {}'.format( self.g.doc.code ) )
#        LOGR.debug( 'HDRS: {}'.format( pprint.pformat( self.g.doc.headers ) ) )
        if outfn:
            self.g.doc.save( outfn )


    def get_cycle_start( self, the_date ):
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
        return self.date_as_midnight( start_date )


    def get_cycle_end( self, the_date ):
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
        return self.date_as_midnight( end_date )


    def _mk_month_url( self, the_date ):
        ts_month = int( self.get_cycle_start( the_date ).timestamp() )
        new_url = self.MONTH_URL.substitute( timev=ts_month )
        LOGR.debug( 'URL: {}'.format( new_url ) )
        return new_url


    def _mk_day_url( self, the_date ):
        data = { 'timev': int( self.get_cycle_start( the_date ).timestamp() ),
                 'dayv': int( the_date.timestamp() ),
               }
        new_url = self.DAY_URL.substitute( data )
        return new_url


    def _load_date( self, the_date ):
        url = self._mk_day_url( the_date )
        LOGR.debug( 'DAY URL: {}'.format( url ) )
        self._go( url, outfn='01_day.html' )


    def get_overdue_month( self ):
        """ Only gets first (oldest) overdue month
            Return: String - Unix timestamp
            Throws: UserWarning( 'No Overdue Months' )
        """
        #today = datetime.datetime.now( tz=self.tz ).replace( **self.MIDNIGHT )
        #url = self._mk_month_url( today )
        #self._go( url, outfn='00_month.html' )
        self._go( self.URL, outfn='00_month.html' )
        #pprint.pprint( self.g.doc.tree )
        # this negative lookahead regex magic groc'd from http://www.perlmonks.org/?node_id=188907
        re_pattern = 'a href=[^>]*content=month&time_v=([0-9]+)(?:(?!<\/tr>).)*Overdue'
        re_overdue = re.compile( re_pattern, re.DOTALL )
        try:
            match_overdue = self.g.doc.rex_text( re_overdue )
        except ( weblib.error.DataNotFound ) as e:
            raise UserWarning( "No Overdue Months" )
        LOGR.debug( match_overdue )
        return match_overdue
        #LOGR.debug( self.g.doc.tree )


    def _secs2halfday( self, s ):
        ''' Return 0, 1, or 2 
            indicating zero-day, half-day, or full-day, respectively
        '''
        rv = 1
        if s < 7200 :
            rv = 0
        elif s >= 21600 :
            rv = 2
        return rv


    def _secs2fullday( self, s ):
        ''' Return 0 or 1, indicating zero or full-day, respectively
            half-day: ( 7200 <= half-day < 21600 )
        '''
        rv = 0
        if s > 0:
            rv = 1
        return rv


    def _secs2hours( self, s ):
        ''' Round to nearest full number of hours
        '''
        hours = int( s / 3600 )
        secs = s % 3600
        if secs > 30:
            hours += 1
        if hours > 8:
            hours = 8
        if hours < 1:
            hours = ''
        return hours


    def submit_date( self, the_date, **k ):
        #TODO - WILL THIS WORK BY JUST CREATING AN HTTP GET (instead of posting the form)?
        ''' Submit vacation / sick leave for the given date.
            INPUT:
                the_date: python date object
                       k: secs for each type of personal time to report
            Valid keys are: VACATION, SICK, FLOATINGHOLIDAY, BEREAVEMENT,
                            JURYDUTY, MILITARYLEAVE
            If key is 
                SICK or VACATION: secs will be rounded to the nearest half-day
                FLOATINGHOLIDAY: secs will be rounded UP to the nearest full-day
                anything else: secs are converted to hours (up tp a max of 8)
        '''
        formdata = { 'VACATION'        : { 'NAME': 'vac' },
                     'SICK'            : { 'NAME': 'sick' },
                     'FLOATINGHOLIDAY' : { 'NAME': 'fholiday' },
                     'BEREAVEMENT'     : { 'NAME': 'bereavement' },
                     'JURYDUTY'        : { 'NAME': 'juryduty' },
                     'MILITARYLEAVE'   : { 'NAME': 'military' },
                 }
        timevals = { 'VACATION'        : 0,
                     'SICK'            : 0,
                     'FLOATINGHOLIDAY' : 0,
                     'BEREAVEMENT'     : 0,
                     'JURYDUTY'        : 0,
                     'MILITARYLEAVE'   : 0,
                   }
        timevals.update( k )

        # Convert vacation, sick to half-days
        choices = { 'VACATION': [ 'RM', 'VH', 'VF' ],
                    'SICK'    : [ 'RM', 'SH', 'SF' ],
                  }
        for k, vlist in choices.items():
            secs = timevals[ k ]
            i = self._secs2halfday( secs )
            formdata[ k ][ 'VAL' ] = vlist[i]
#            LOGR.debug( 'Setting option {} to index {} as {}'.format( k, i, vlist[i] ) )
#            LOGR.debug( 'Actual result: {}'.format( formdata[ k ][ 'VAL' ] ) )

        # Round floating holiday to full-day
        choices = { 'FLOATINGHOLIDAY': [ 'RM', 'FH' ] }
        for k, vlist  in choices.items():
            secs = timevals[ k ]
            i = self._secs2halfday( secs )
            formdata[ k ][ 'VAL' ] = vlist[i]
            
        # Remaining keys (in timevals) are per-hour values
        for k in ( 'BEREAVEMENT', 'JURYDUTY', 'MILITARYLEAVE' ):
            secs = timevals[ k ]
            hours = self._secs2hours( secs )
            formdata[ k ][ 'VAL' ] = str( hours )

#        LOGR.debug( 'FORM DATA: {}'.format( pprint.pformat( formdata ) ) )
#        raise SystemExit( 'abc' )

        # Load the page
        self._load_date( the_date )
        # Get the form
        self.g.doc.choose_form( name='form1' )
        # Set the form values
        for key in formdata:
            name = formdata[ key ][ 'NAME' ]
            val = formdata[ key ][ 'VAL' ]
            self.g.doc.set_input( name, val )
        # Submit form
        self.g.submit()
        # Save return page
        self.g.doc.save( '02_submit_response.html' )


if __name__ == '__main__':
    print( 'VSL Reporter Module not valid from cmdline' )
