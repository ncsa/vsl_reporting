#!/bin/env python3

import logging
import pyexch
import argparse
import vsl_reporter
import datetime
import getpass
import os
import pprint

def process_args():
    constructor_args = { 
        'formatter_class': argparse.RawDescriptionHelpFormatter,
        'description': 'NCSA Vacation/Sick Leave Time Reporting tool.',
        'epilog': '''
Program is controlled using environment variables.
VSL calendar:
    VSL_USER
    VSL_PWD_FILE
Exchange calendar:
    PYEXCH_USER
    PYEXCH_PWD_FILE
    PYEXCH_AD_DOMAIN
    PYEXCH_EMAIL_DOMAIN
    PYEXCH_REGEX_JSON
''',
           }
    parser = argparse.ArgumentParser( **constructor_args )
    parser.add_argument( '-n', '--dryrun', action='store_true' )
    action = parser.add_mutually_exclusive_group( required=True )
    action.add_argument( '--exch', action='store_true',
        help='Load data from Exchange' )
    action.add_argument( '--list-overdue', action='store_true',
        help='List overdue dates and exit' )
    defaults = { 'user': None,
                 'pwdfile': None,
                 'passwd': None,
    }
    parser.set_defaults( **defaults )
    args = parser.parse_args()
    # USER
    if not args.user:
        args.user = os.getenv( 'VSL_USER' )
    if not args.user:
        args.user = os.getenv( 'PYEXCH_USER' )
    if not args.user:
        args.user = getpass.getuser()
        logging.warning( 'No user specified. Using "{0}".'.format( args.user ) )
    # PASSWORD
    if not args.passwd:
        if not args.pwdfile:
            args.pwdfile = os.getenv( 'VSL_PWD_FILE' )
        if not args.pwdfile:
            args.pwdfile = os.getenv( 'PYEXCH_PWD_FILE' )
        if args.pwdfile:
            # get passwd from file
            with open( args.pwdfile, 'r' ) as f:
                for l in f:
                    args.passwd = l.rstrip()
                    break
    if not args.passwd:
        # prompt user for passwd
        prompt = "Enter passwd for '{0}':".format( args.user )
        args.passwd = getpass.getpass( prompt )
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
    logging.basicConfig( level=logging.DEBUG, format=fmt )
#    for key in logging.Logger.manager.loggerDict:
#        print(key)
    no_debug = [ 
        'connectionpool',
        'weblib', 
        'selection', 
        'grab', 
        'requests', 
        'ntlm_auth', 
        'exchangelib', 
        'future_stdlib' ]
    for key in no_debug:
            logging.getLogger(key).setLevel(logging.CRITICAL)
    run()
