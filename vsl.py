#!/bin/env python3

import logging
import pyexch
import argparse
import vsl_reporter
import datetime
import getpass
import tzlocal
import os

import pprint

def process_args():
    desc = { 'description': 'NCSA Vacation/Sick Leave Time Reporting tool.',
             'epilog': '''PYEXCH_REGEX_CLASSES = Dict
                          PYEXCH_USER = String
                          PYEXCH_AD_DOMAIN = String
                          PYEXCH_EMAIL_DOMAIN = String
                          Regex matching is always case-insensitive. 
                       '''
           }
    parser = argparse.ArgumentParser( **desc )
    parser.add_argument( '--user', help='Username' )
    parser.add_argument( '--pwdfile',
        help='Plain text passwd ***WARNING: for testing only***' )
    parser.add_argument( '--passwd', help=argparse.SUPPRESS )
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
    # check user
    if not args.user:
        args.user = os.getenv( 'PYEXCH_USER' )
    if not args.user:
        args.user = getpass.getuser()
        logging.info( 'No user specified. Using "{0}".'.format( args.user ) )
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
    try:
        overdue_ts = vsl.get_overdue_month()
    except ( UserWarning ) as e:
        if e.args[0] == "No Overdue Months":
            now = datetime.datetime.now().astimezone( vsl.tz )
            month_start = vsl.get_cycle_start( now )
            overdue_ts = month_start.timestamp()
        else:
            raise e
    overdue_month_start = vsl.ts2datetime( overdue_ts )
    overdue_month_end = vsl.get_cycle_end( overdue_month_start )

    if args.list_overdue:
        print( "Earliest Overdue Month: {}".format( overdue_month_start ) )
        raise SystemExit()
 
    # Get sick / vacation info from Exchange
    ptr_regex = { 'SICK'     : '(sick|doctor|dr. appt)',
                  'VACATION' : '(vacation|OOTO|OOO|out of the office|out of office)',
    }
    px = pyexch.PyExch( regex_map=ptr_regex )
    days_report = px.per_day_report( overdue_month_start )
    pprint.pprint( days_report )
    for ewsdate, data in days_report.items():
        #force EWSDate to naive Python date
        date = datetime.datetime(ewsdate.year, ewsdate.month, ewsdate.day )
        if args.dryrun:
            print( 'DRYRUN: date:{} data:{} ... doing nothing'.format( date, pprint.pformat( data ) ) )
            continue
        else:
            vsl.submit_date( date, **data )

if __name__ == '__main__':
    run()
