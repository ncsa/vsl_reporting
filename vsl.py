#!/bin/env python3

import logging
import pyexch
import argparse
import vsl_reporter
import datetime
import getpass
import tzlocal

import pprint

LOGR = logging.getLogger(__name__)
LOGR.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s [%(filename)s:%(funcName)s:%(lineno)s] %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
LOGR.addHandler(ch)


def process_args():
    desc = { 'description': 'NCSA Vacation/Sick Leave Time Reporting tool.',
             'epilog': '''Set environment variable PYEXCH_REGEX_CONFIG
                          as a filename of a YAML formatted file with settings:
                          PYEXCH_REGEX_CLASSES = Dict
                          One of: PYEXCH_USER or PYEXCH_AD_DOMAIN
                            PYEXCH_USER = String; in the form user\\AD_DOMAIN
                            PYEXCH_AD_DOMAIN = String
                          One of: PYEXCH_EMAIL or PYEXCH_EMAIL_DOMAIN
                            PYEXCH_EMAIL = String; in the form user@email.domain
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
    parser.add_argument( '-q', '--quiet', action='store_true' )
    parser.add_argument( '-d', '--debug', action='store_true' )
    parser.add_argument( '-o', '--once', action='store_true',
        help='Submit only one week, then exit.' )
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
        args.user = getpass.getuser()
        logging.info( 'No user specified. Using "{0}".'.format( args.user ) )
    if args.pwdfile:
        # get passwd from file
        with open( args.pwdfile, 'r' ) as f:
            for l in f:
                args.passwd = l.rstrip()
                break
    else:
        # prompt user for passwd
        prompt = "Enter passwd for '{0}':".format( args.user )
        args.passwd = getpass.getpass( prompt )
    return args


def run():
    args = process_args()
    vsl = vsl_reporter.VSL_Reporter( username=args.user, password=args.passwd )
    overdue_ts = vsl.get_overdue_months()
    overdue_month_start = vsl.ts2datetime( overdue_ts )
    overdue_month_end = vsl.get_cycle_end( overdue_month_start )
 
    # Get sick / vacation info from Exchange
    domain_user = 'UOFI\\{}'.format( args.user )
    email = '{}@illinois.edu'.format( args.user )
    ptr_regex = { 'SICK'     : '(sick|doctor|dr. appt)',
                  'VACATION' : '(vacation|OOTO|OOO|out of the office|out of office)',
    }
    px = pyexch.PyExch( user=domain_user, email=email, pwd=args.passwd, regex_map=ptr_regex )
    days_report = px.per_day_report( overdue_month_start )
    pprint.pprint( days_report )
#    tz_str = tzlocal.get_localzone()
    for ewsdate, data in days_report.items():
        #force EWSDate to Python date
        date = datetime.datetime(ewsdate.year, ewsdate.month, ewsdate.day, tzinfo=tz_str)
#        if date > overdue_month_end:
#            LOGR.debug( 'End of month, skipping remaining dates' )
#            break
        vsl.submit_date( date, **data )

if __name__ == '__main__':
    run()
