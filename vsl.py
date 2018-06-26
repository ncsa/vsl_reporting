#!/bin/env python3

import logging
import pyexch
import argparse
import vsl_reporter
import datetime
import getpass
import os
import pprint
import netrc

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
    action = parser.add_mutually_exclusive_group( required=True )
    action.add_argument( '--exch', action='store_true',
        help='Load data from Exchange' )
    action.add_argument( '--list-overdue', action='store_true',
        help='List overdue dates and exit' )
    defaults = { 'user': None,
                 'passwd': None,
                 'netrckey': 'NCSA_VSL',
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
    overdue_month_start = None
    try:
        overdue_ts = vsl.get_overdue_month()
    except ( UserWarning ) as e:
        if e.args[0] == "No Overdue Months":
            logging.debug( "caught No Overdue Months" )
            now = datetime.datetime.today()
            overdue_month_start = vsl.get_cycle_start( now )
        else:
            raise e
    if not overdue_month_start:
        overdue_month_start = vsl.ts2datetime( overdue_ts )
    logging.debug( "overdue_month_start: {}".format( overdue_month_start ) )

    if args.list_overdue:
        print( "Earliest Overdue Month: {}".format( overdue_month_start ) )
        logging.info( "overdue month: {}".format( overdue_month_start ) )
        raise SystemExit()
 
    # Get sick / vacation info from Exchange
    px = pyexch.PyExch()
    days_report = px.per_day_report( overdue_month_start )
    logging.debug( 'Days report from Exchange: {}'.format( days_report ) )
    for ewsdate, data in days_report.items():
        #force EWSDate to naive Python date
        date = datetime.datetime(ewsdate.year, ewsdate.month, ewsdate.day )
        if args.dryrun:
            print( 'DRYRUN: date:{} data:{} ... doing nothing'.format( 
                date, pprint.pformat( data ) ) )
        else:
            vsl.submit_date( date, **data )
            logging.info( "Successfully submittited date:{} {}".format( date, data ) )

if __name__ == '__main__':
    fmt = '%(levelname)s [%(filename)s:%(funcName)s:%(lineno)s] %(message)s'
    logging.basicConfig( level=logging.INFO, format=fmt )
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
