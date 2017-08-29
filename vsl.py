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
Setting parameters via Environment Variables (same as pyexch.PyExch):
    PYEXCH_USER
    PYEXCH_AD_DOMAIN
    PYEXCH_EMAIL_DOMAIN
    PYEXCH_PWD_FILE
    PYEXCH_REGEX_JSON
''',
           }
    parser = argparse.ArgumentParser( **constructor_args )
    parser.add_argument( '--user', help='Username' )
    parser.add_argument( '--pwdfile',
        help='Plain text passwd ***WARNING: for testing only***' )
    parser.add_argument( '--ad_domain', help="Default: %(default)s" )
    parser.add_argument( '--email_domain', help="Default: %(default)s" )
    parser.add_argument( '-n', '--dryrun', action='store_true' )
    action = parser.add_mutually_exclusive_group( required=True )
    action.add_argument( '--exch', action='store_true',
        help='Load data from Exchange' )
    action.add_argument( '--list-overdue', action='store_true',
        help='List overdue dates and exit' )
    defaults = { 'user': None,
                 'pwdfile': None,
                 'passwd': None,
                 'ad_domain': 'UOFI',
                 'email_domain': 'illinois.edu',
    }
    parser.set_defaults( **defaults )
    args = parser.parse_args()
    # check user
    if not args.user:
        args.user = os.getenv( 'PYEXCH_USER' )
    if not args.user:
        args.user = getpass.getuser()
        logging.warning( 'No user specified. Using "{0}".'.format( args.user ) )
    if not args.passwd:
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
#            now = datetime.datetime.now().astimezone( vsl.tz )
#            now = datetime.datetime.today().replace( **vsl.MIDNIGHT )
            now = datetime.datetime.today()
            overdue_month_start = vsl.get_cycle_start( now )
#            overdue_ts = overdue_month_start.timestamp()
        else:
            raise e
    if not overdue_month_start:
        overdue_month_start = vsl.ts2datetime( overdue_ts )
    #overdue_month_end = vsl.get_cycle_end( overdue_month_start )
#    logging.debug( "overdue_ts: {}".format( overdue_ts ) )
    logging.debug( "overdue_month_start: {}".format( overdue_month_start ) )
#    logging.debug( "overdue_month_end: {}".format( overdue_month_end ) )

    if args.list_overdue:
        print( "Earliest Overdue Month: {}".format( overdue_month_start ) )
        logging.info( "overdue month: {}".format( overdue_month_start ) )
        raise SystemExit()
 
    # Get sick / vacation info from Exchange
    px = pyexch.PyExch( user=args.user, 
                        pwd=args.passwd, 
                        ad_domain=args.ad_domain,
                        email_domain=args.email_domain
                      )
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
#    ch = logging.StreamHandler()
#    ch.setLevel( logging.DEBUG )
    fmt = '%(levelname)s [%(filename)s:%(funcName)s:%(lineno)s] %(message)s'
#    formatter = logging.Formatter( fmt=fmt, style='%' )
#    ch.setFormatter( formatter )
    logging.basicConfig( level=logging.INFO, format=fmt )
    run()
