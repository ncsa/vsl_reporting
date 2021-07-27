#!/bin/env python3

import argparse
import datetime
import getpass
import logging
import netrc
import os
import pprint
import pyexch.pyexch
import vsl_reporter

def process_args():
    constructor_args = { 
        'formatter_class': argparse.RawDescriptionHelpFormatter,
        'description': 'NCSA Vacation/Sick Leave Time Reporting tool.',
        'epilog': '''
Program is controlled using the following environment variables:
    NETRC
        path to netrc file (default: ~/.netrc)
        where netrc file has keys "NCSA_VSL" and "EXCH"
        and the "EXCH" key has values for login, password, account
    PYEXCH_REGEX_JSON
        JSON formatted string for use by PYEXCH to select and categorize
        exchange events

See also: https://github.com/andylytical/pyexch
''',
           }
    parser = argparse.ArgumentParser( **constructor_args )
    parser.add_argument( '-n', '--dryrun', action='store_true' )
    parser.add_argument( '-k', '--netrckey',
        help='key in netrc to use for login,passwd; default=%(default)s' )
    parser.add_argument( '--list-overdue', action='store_true',
        help='List overdue dates and exit' )
    defaults = { 'user': None,
                 'passwd': None,
                 'netrckey': 'NETID',
    }
    parser.set_defaults( **defaults )
    args = parser.parse_args()
    # Load login and passwd from netrc
    netrc_fn = os.getenv( 'NETRC' )
    nrc = netrc.netrc( netrc_fn )
    nrc_parts = nrc.authenticators( args.netrckey )
    if nrc_parts:
        args.user = nrc_parts[0]
        args.passwd = nrc_parts[2]
    if not args.user:
        raise UserWarning( 'Empty username not allowed' )
    if not args.passwd:
        raise UserWarning( 'Empty passwd not allowed' )
    return args


def run():
    args = process_args()
    vsl = vsl_reporter.VSL_Reporter( username=args.user, password=args.passwd )

    start, end = vsl.get_overdue_period()
    if start is None:
        raise SystemExit( 'No reports are due' )

    msg = f'Report due for period: {start} - {end}'
    logging.info( msg )
    if args.list_overdue:
        raise SystemExit()
 
    # Get sick / vacation info from Exchange
    px = pyexch.pyexch.PyExch()
    days_report = px.per_day_report( start, end )
    logging.debug( f'Days report from Exchange: {pprint.pformat(days_report)}' )
    for ewsdate, data in days_report.items():
       #force EWSDate to naive Python date
       # date = datetime.datetime(ewsdate.year, ewsdate.month, ewsdate.day )
       date = ewsdate
       if args.dryrun:
           print( f'DRYRUN: {date} {pprint.pformat(data)} ... doing nothing' )
       else:
           vsl.submit_date( date, **data )
           logging.info( "Successfully submittited date:{} {}".format( date, data ) )

if __name__ == '__main__':
    fmt = '%(levelname)s [%(filename)s:%(funcName)s:%(lineno)s] %(message)s'
    log_lvl = logging.DEBUG
    # log_lvl = logging.INFO
    logging.basicConfig( level=log_lvl, format=fmt )
#    for key in logging.Logger.manager.loggerDict:
#        print(key)
    no_debug = [ 
        'connectionpool',
        'exchangelib', 
        'future_stdlib',
        'grab', 
        'ntlm_auth', 
        'requests', 
        'selection', 
        'urllib3',
        'weblib', 
        ]
    for key in no_debug:
            logging.getLogger(key).setLevel(logging.CRITICAL)
    run()
