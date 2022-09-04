import datetime
import grab
import json
import logging
import pathlib
import re
import string
import time
import tzlocal
import weblib.error
import urllib.parse

import pprint

LOGR = logging.getLogger(__name__)


class VSL_Reporter( object ):

    MIDNIGHT = { 'hour': 0, 'minute': 0, 'second': 0, 'microsecond': 0 }
    URL = {
        'vsl': 'https://my.engr.illinois.edu/vacation/',
        'setdate': 'https://my.engr.illinois.edu/vacation/setdate.asp',
        'myemployees': 'https://my.engr.illinois.edu/vacation/myemployees.asp',
        'userdetails': 'https://my.engr.illinois.edu/vacation/userdetails.asp',
        'approve': 'https://my.engr.illinois.edu/vacation/change_status.asp?ns=A',
    }
    FN_COOKIES = pathlib.Path( 'cookiefile' )
    LOGIN_TIMELIMIT = datetime.timedelta( hours=1 )


    def __init__( self, username, password, *a, **k ):
        self.usr = username
        self.pwd = password
        self.userpwd = '{}:{}'.format( username, password )
        self.g = grab.Grab()
        self.g.setup( cookiefile=self.FN_COOKIES )
        self.FN_COOKIES.touch()
        if LOGR.getEffectiveLevel() is logging.DEBUG:
            self.g.setup( debug=True, log_dir='LOGS' )
        self.tz = tzlocal.get_localzone() # get pytz timezone
        self.in_login = False


    def _go( self, url, **kwargs ):
        LOGR.debug( f'URL: {url}' )
        self.g.go( url, **kwargs )
        # if we got redirected to the login page, then have to login
        url_parts = self.g.doc.url_details()
        # url_details is a SplitResult object ...
        # SplitResult(scheme='https', netloc='shibboleth.illinois.edu', path='/login.asp', query='/vacation/index.asp%7C', fragment='')
        if 'login' in url_parts.netloc and not self.in_login:
            LOGR.info( 'Found login page' )
            self._do_login()


    def get_overdue_period( self ):
        """ Attempt to get overdue reporting period
            Return: tuple( startdate, enddate )
            Throws: UserWarning( 'No Overdue Months' )
        """
        self._go( self.URL['vsl'] )
        # negative lookahead regex
        # from http://www.perlmonks.org/?node_id=188907
        # tested at https://regex101.com/
        re_pattern = (
            'Reporting Period Signature Due'
            '(?:(?!<\/table>).)*?'
            '([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})'
            ' - '
            '([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})'
            )
        re_get_dates = re.compile( re_pattern, flags=re.DOTALL )
        match = self.g.doc.rex_search( re_get_dates, default=None )
        start, end = None, None
        if match:
            # get start and end; month, day, year values (and cast each to an int)
            sm, sd, sy, em, ed, ey = [ int(x) for x in match.groups() ]
            start = datetime.datetime( sy, sm, sd, tzinfo=self.tz )
            end = datetime.datetime( ey, em, ed, tzinfo=self.tz )
        return [ start, end ]


    def list_employees( self ):
        """ Get list of employee UID's
        """
        UIDs = []
        self._go( self.URL['myemployees'] )
        # submit the form for each different employee type
        for typ in ( 'ac', 'cce', 'cc' ):
            LOGR.debug( f"Checking for employees of type '{typ}'" )
            self.g.doc.choose_form( name='frm_type' )
            self.g.doc.set_input( 'type', typ )
            self.g.submit()
            # Get all employees from the returned doc
            re_get_employees = re.compile( r'A HREF="userdetails.asp\?user=([a-z0-9]+)"' )
            for match in re_get_employees.finditer( self.g.doc.unicode_body() ):
                for m in match.groups():
                    LOGR.debug( f"Employee: '{m}'" )
                    UIDs.append( f'{m}' )
        return UIDs


    def get_pending_approvals( self ):
        pending_approvals = {}
        for uid in self.list_employees():
            LOGR.debug( f"Getting pending approvals for UID '{uid}'..." )
            pending_approvals[uid] = []
            url = f"{self.URL['userdetails']}?user={uid}"
            self._go( url )
            re_get_approval_key = re.compile( 
                r'href="change_status.asp\?key=\{([^}]+)\}\&ns=A"' )
            approval_keys = []
            for match in re_get_approval_key.finditer( self.g.doc.unicode_body() ):
                for m in match.groups():
                    LOGR.debug( f"Pending: '{m}'" )
                    pending_approvals[uid].append( m )
        return pending_approvals


    def approve_pending( self, pend_key ):
        self._go( f"{self.URL['approve']}&key={pend_key}" )


    def _do_login( self ):
        self.in_login = True
        URL = {
            # 'user-pass': 'login.microsoftonline.com/44467e6f-462c-4ea2-823f-7800de5434e3/login',
            'user-pass': 'login',
        }
        LOGR.info( 'Attempting to login ...' )

        # create and submit the form in LOGS/06.html
        # (form is normally created dynamically via JS)
        scripts = self.g.doc.select( "//script[@type='text/javascript']" )
        config_str = None
        for s in scripts:
            text = s.text()
            if text.startswith( '//<![CDATA[ $Config=' ):
                #LOGR.debug( f'SCRIPT {i}: {s.text()}' )
                config_str = text[20:-7]
        if not config_str:
            raise UserWarning( '$Config javascript not found' )
        #LOGR.debug( f'Config Str: {config_str}' )
        cfg = json.loads( config_str )
        # LOGR.debug( f"Config:\n{pprint.pformat(cfg)}" )
        post_data = {
        'canary': cfg['canary'],
        'ctx': cfg['sCtx'],
        'flowToken': cfg['sFT'],
        'hpgrequestid': cfg['sessionId'],
        'login': self.usr,
        'loginfmt': self.usr,
        'passwd': self.pwd,
        # 'CookieDisclosure': 0,
        # 'FoundMSAs': '',
        # 'IsFidoSupported': 1,
        # 'LoginOptions': 3,
        # 'NewUser': 1,
        # 'PPSX': '',
        # 'fspost': 0,
        # 'hisRegion': '',
        # 'hisScaleUnit': '',
        # 'i13': '0',
        # 'i19': 26209,
        # 'i21': 0,
        # 'isSignupPost': 0,
        # 'lrt': '',
        # 'lrtPartition': '',
        # 'ps': 2,
        # 'psRNGCDefaultType': '',
        # 'psRNGCEntropy': '',
        # 'psRNGCSLK': '',
        # 'type': 11,
        }
        # LOGR.debug( f'Form post data:\n{pprint.pformat(post_data)}' )
        self._go(
            url=URL['user-pass'],
            post=post_data,
            )


        # submit the form in LOGS/07.html
        self.g.submit()

        # submit the form in LOGS/08.html
        self.g.submit()

        # submit the form in LOGS/09.html -> form method=get, clone this grab and then send?
        url_parts = list( urllib.parse.urlsplit( self.g.doc.form.action )[:3] )
        form_fields = self.g.doc.form_fields()
        app_tx = form_fields['request']
        url_parts.append( urllib.parse.urlencode( form_fields ) ) #query string
        url_parts.append( '' ) #fragment
        LOGR.debug( f'URLparts:\n{pprint.pformat(url_parts)}\nFormFields:\n{pprint.pformat(form_fields)}' )
        duo_url = urllib.parse.urlunsplit( url_parts )
        LOGR.debug( f'DUO URL:\n{duo_url}' )
        self.duo_authenticate( duo_url )
        raise UserWarning('Testing STOP')
        #self.g.submit()

        # submit the form in LOGS/11.html
        url_parts = self.g.doc.url_details()
        #LOGR.debug( f'11.LOG: URL parts:\n{url_parts}' )
        self.g.submit()

        # NOW at 13.html
        url_parts = self.g.doc.url_details()
        LOGR.debug( f'13.LOG: URL parts:\n{url_parts}' )

        # Use a clone of grab to get duo phone data
        # gclone = self.g.clone()
        # if LOGR.getEffectiveLevel() is logging.DEBUG:
        #     gclone.setup( debug=True, log_dir='LOGS_CLONE' )
        # # build URL for data request
        # data_path = f'{url_parts[2]}/data'
        # data_query = urllib.parse.parse_qs( url_parts[3] ) #string -> dict
        # data_query['post_auth_action'] = 'OIDC_EXIT' #add item to dict
        # LOGR.debug( f'data_query: {data_query}' )
        # data_url_parts = [ x for x in url_parts ]
        # data_url_parts[2] = data_path
        # data_url_parts[3] = urllib.parse.urlencode( data_query ) #dict -> string
        # data_url = urllib.parse.urlunsplit( data_url_parts )
        # LOGR.debug( f'data_url: {data_url}' )
        # gclone.go( data_url )
        # duo_auth_data = gclone.doc.json
        # LOGR.debug( f'duo_auth_data: {duo_auth_data}' )

        # LOGS/13.html
        # get fields needed later for duo
        LOGR.debug( f'13 form fields: {self.g.doc.form_fields()}' )
        raise UserWarning('Testing STOP')
        duo_data = {}
        for k in ( 'sid', 'device', 'factor', '_xsrf' ):
            duo_data[k] = urllib.parse.unquote_plus( self.g.doc.form_fields()[k] )
        # submit the form ... will send DUO prompt to the user's device
        # DOES THIS FORM NEED TO SUBMIT WITH ONLY A FEW FIELDS:
        #     device=phone1
        #     factor=Duo Push
        #     sid=frameless-9c0e3d8d-c5bc-4423-8a94-e38dd064d5b1
        self.g.submit()


        # Get the txid from JSON response
        duo_txid = self.g.doc.json['response']['txid']
        #LOGR.debug( f'TXID: {duo_txid}' )
        # create status URL from "prompt" URL
        url_parts = self.g.doc.url_details()
        # (scheme='https', netloc='shibboleth.illinois.edu', path='/login.asp', query='/vacation/index.asp%7C', fragment='')
        LOGR.debug( f'URL parts:\n{url_parts}' )
        new_url_parts = [ x for x in url_parts ]
        new_url_parts[2] = url_parts[2].replace('prompt','status')
        LOGR.debug( f'NEW URL parts:\n{new_url_parts}' )
        duo_status_url = urllib.parse.urlunsplit( new_url_parts )
        LOGR.debug( f'DUO STATUS URL: {duo_status_url}' )

        # post_data = {
        #     'txid': duo_txid,
        #     'sid': duo_sid,
        #     }
        post_data = {
            'sid': duo_sid,
            'device': duo_device,
            'factor': duo_factor,
            }
        self._go( duo_status_url, post=post_data )
        login_status = self.g.doc.json
        LOGR.debug( f'STATUS 1: {login_status}' )

        raise UserWarning('Testing STOP')


        # Loop to get the DUO response status
        max_tries = 4
        pause = 5
        for count in range(4):
            LOGR.debug( f'Attempt {count} of {max_tries}' )
            #timestamp = int( time.time() )
            self._go( duo_status_url, post=post_data )
            # check duo auth status
            login_status = self.g.doc.json
            if login_status['response']['status_code'] == 'allow':
                break
            LOGR.info( f'sleep {pause} seconds' )
            time.sleep( pause )
        if login_status['response']['status_code'] != 'allow':
            raise UserWarning( 'DUO authentication failed' )
        else:
            LOGR.info ( 'DUO authentication succeeded' )

        raise UserWarning('Testing STOP')

        self.in_login = False







        # Now we have the page with the DUO iframe,
        # get TX and APP values
        re_tx_val = re.compile( "sig_request.: .(TX\|[^:]+):(APP\|[^'\"]+)" )
        match = self.g.doc.rex_search( re_tx_val )
        post_data = {
            'tx': match.group(1),
            'app': match.group(2),
        }
        LOGR.debug( f"tx: {post_data['tx']}" )
        LOGR.debug( f"app: {post_data['app']}" )

        # get "Context" and "AuthMethod"
        self.g.doc.choose_form( id='duo_form' )
        fields = self.g.doc.form_fields()
        LOGR.debug( f'add duo_form fields to post data: {pprint.pformat( fields )}' )
        post_data.update( fields )
        # get "parent"
        self.g.doc.choose_form( id='options' )
        post_data['parent'] = self.g.doc.form.action
        LOGR.debug( f"parent: {post_data['parent']}" )

        # Do the DUO auth
        # ... Duo auth needs "tx" and "parent"; it will return "auth"
        # ... After Duo auth, will need to build sig_response from "auth" + "app"
        # ... and pass it to "parent"
        login_status = self.duo_authenticate( post_data['tx'], post_data['parent'] )

        # Create sig_response from "auth" (from duo) and "app" (from above)
        post_data['auth'] = login_status['authSig']
        sig_response=':'.join( ( post_data['auth'], post_data['app'] ) ) 
        post = {
            'sig_response': sig_response,
            'Context': post_data['Context'],
            'AuthMethod': post_data['AuthMethod']
        }
        # Redirect back to parent (SAML2 SSO)
        self.g.go( post_data['parent'], post=post )

        # Response should be "... press the Continue button once to proceed."
        # .. sets SAMLResponse
        self.g.submit()
        self.g.submit()


    def duo_authenticate( self, url ):
        g = grab.Grab() #create a new grab instance (don't poison the other one)
        if LOGR.getEffectiveLevel() is logging.DEBUG:
            g.setup( debug=True, log_dir='LOGS.DUO' )

        g.go( url )
        raise UserWarning('Testing STOP')






        # DUO = {}
        # DUO['initialize'] = 'https://verify.uillinois.edu/frame/web/v1/auth'
        # DUO['pre_auth'] = 'https://verify.uillinois.edu/frame/devices/preAuth'
        # DUO['push'] = 'https://verify.uillinois.edu/frame/devices/authPush_async'
        # DUO['status'] = 'https://verify.uillinois.edu/frame/devices/authStatus/'
        # DUO['v'] = '2.6'
        # Initialize DUO (get JSESSIONID)
        url_parts = (
            f"{DUO['initialize']}",
            f'?tx={tx}',
            f'&parent={parent}',
            f'&pullStatus=0',
            f"&v={DUO['v']}"
            )
        g.go( ''.join(url_parts) )

        # pre-Auth (get DUO push device id)
        post = {
            'tx': tx,
            'parent': parent,
        }
        g.go( DUO['pre_auth'], post=post )
        auth_string = g.doc.body
        auth_data = json.loads( auth_string )
        LOGR.debug( f'JSON: {json.dumps(auth_data, indent=2)}' )
        # Find default device
        default_device = None
        for dev in auth_data['devices']:
            if dev['defDevice'] is True:
                default_device = dev
                break
        if default_device is None:
            raise UserWarning( 'Did not find a default duo auth device.' )
        LOGR.debug( f'DEFAULT DEVICE: {json.dumps( default_device, indent=2 )}' )

        # Initiate duo auth with default device
        post = {
            'tx': tx,
            'parent': parent,
            'device': default_device
        }
        # manually set content-type for json
        g.setup( headers={'Content-Type': 'application/json', 'charset':'UTF-8'} )
        g.go( DUO['push'], post=json.dumps( post ) )
        LOGR.info( 'Sent DUO authentication request to default device' )

        # Get txid, check status (NOTE: txid has nothing to do with TXval from above)
        txid = json.loads( g.doc.body )['status']
        timestamp=0
        url_parts = [
            DUO['status'],
            txid,
            f'?tx={tx}',
            f'&parent={parent}',
            f'&_={timestamp}'
        ]
        max_tries = 4
        pause = 5
        for count in range(4):
            LOGR.debug( f'Attempt {count} of {max_tries}' )
            timestamp = int( time.time() )
            url_parts[-1] = f'&_={timestamp}'
            url = ''.join( url_parts )
            g.setup( headers={'Content-Type': 'application/json', 'charset':'UTF-8'} )
            g.go( url )
            # check duo auth status
            login_status = json.loads( g.doc.body )
            if login_status['status'] == 'allow':
                break
            LOGR.info( f'sleep {pause} seconds' )
            time.sleep( pause )
        if login_status['status'] != 'allow':
            raise UserWarning( 'DUO authentication failed' )
        else:
            LOGR.info ( 'DUO authentication succeeded' )
        self.in_login = False
        return login_status


    def date_as_midnight( self, thedate ):
        ''' Return a datetime for midnight of the day given in thedate.
            Input: datetime.date or datetime.datetime
        '''
        return datetime.datetime( thedate.year, thedate.month, thedate.day )


    def _load_date( self, d ):
        datestr = f'{d.month}/{d.day}/{d.year}'
        self._go( f"{self.URL['setdate']}?{datestr}" )
        error_list = (
            'is on a weekend',
            'already submitted',
            'already finalized leave submission',
            )
        for msg in error_list:
            if self.g.doc.text_search( msg ):
                raise UserWarning( f'{d} {msg}' )


    def _secs2halfday( self, s ):
        ''' Return 0, 0.5, or 1.0
            indicating zero-day, half-day, or full-day, respectively
            half-day: ( 7200 <= half-day < 21600 )
        '''
        rv = 0.5
        if s < 7200 :
            rv = 0.0
        elif s >= 21600 :
            rv = 1.0
        return rv


    def _secs2fullday( self, s ):
        ''' Return 0 or 1, indicating zero or full-day, respectively
        '''
        rv = 0.0
        if s > 0:
            rv = 1.0
        return rv


    def submit_date( self, the_date, **k ):
        ''' Submit vacation / sick leave for the given date.
            INPUT:
                the_date = python date object
                k = secs for each type of personal time to report
            Valid keys are: VACATION, SICK, FLOATINGHOLIDAY
            If key is 
                SICK or VACATION: secs will be rounded to the nearest half-day
                FLOATINGHOLIDAY: secs will be rounded UP to the nearest full-day
        '''
        type_vals = {
            'VACATION'        : '0',
            'SICK'            : '1',
            'FLOATINGHOLIDAY' : '2',
            }
        timevalconversion = {
            'VACATION'        : self._secs2halfday,
            'SICK'            : self._secs2halfday,
            'FLOATINGHOLIDAY' : self._secs2fullday,
            }

        # Load the page, skip if it's an invalid date
        try:
            self._load_date( the_date )
        except UserWarning as e:
            LOGR.warning( e )
            return

        leave_name, num_seconds = k.popitem()
        leave_type = type_vals[ leave_name ]
        timeval = timevalconversion[ leave_name ]( num_seconds )
        if timeval <= 0.0:
            LOGR.warning( f'Reported time rounds to 0' )
            return

        LOGR.debug( f"date:'{the_date}' {leave_name} type:='{leave_type}' units:'{timeval}'" )
        # Fill in the form data
        self.g.doc.choose_form( name='frmEntry' )
        self.g.doc.set_input( 'type', str(leave_type) )
        self.g.doc.set_input( 'units', str(timeval) )
        # Submit form
        self.g.submit()


if __name__ == '__main__':
    print( 'VSL Reporter Module not valid from cmdline' )
