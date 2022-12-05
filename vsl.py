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
    parser.add_argument( '--debug', action='store_true',
        help='Debug mode. Lots of data stored in LOGS/ and LOGS.DUO/' )
    parser.add_argument( '-k', '--netrckey',
        help='key in netrc to use for login,passwd; default=%(default)s' )
    parser.add_argument( '-a', '--auto', action='store_true',
        help="When used with --list_self, auto-submit dates from Exchange.\n" \
             "When used with with --list_employees, auto-approve pending entries." )
    parser.add_argument( '-s', '--list_self', action='store_true',
        help='List overdue dates for self' )
    parser.add_argument( '-e', '--list_employees', action='store_true',
        help='List employee pending entries and exit' )
    defaults = { 'debug': False,
                 'user': None,
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


def list_self( args, vsl ):
    start, end = vsl.get_overdue_period()
    if start is None:
        raise SystemExit( 'No reports are due' )

    logging.info( f'Report due for period: {start} - {end}' )

    # Get sick / vacation info from Exchange
    px = pyexch.pyexch.PyExch()
    days_report = px.per_day_report( start, end )
    logging.debug( f'Days report from Exchange: {pprint.pformat(days_report)}' )
    for ewsdate, data in days_report.items():
        date = ewsdate
        if args.auto:
           vsl.submit_date( date, **data )
           logging.info( "Successfully submittited date:{} {}".format( date, data ) )
        else:
           print( f'EXCH EVENT: {date} {pprint.pformat(data)} ' )


def list_employees( args, vsl ):
    user_pending = vsl.get_pending_approvals()
    for uid, approval_keys in user_pending.items():
        logging.info( f"USER: '{uid}'..." )
        for akey in approval_keys:
            logging.info( f"\tPending: '{akey}'" )
            if args.auto:
                vsl.approve_pending( akey )
                logging.info( f"\t... Approved: '{akey}'" )


def run( args ):
    # args = process_args()
    vsl = vsl_reporter.VSL_Reporter( username=args.user, password=args.passwd )

    if args.list_employees:
        list_employees( args, vsl )
    elif args.list_self:
        list_self( args, vsl )
    else:
        list_self( args, vsl )


if __name__ == '__main__':
    # log_lvl = logging.DEBUG
    log_lvl = logging.INFO
    args = process_args()
    if args.debug:
        log_lvl = logging.DEBUG

    fmt = '%(levelname)s %(message)s'
    if log_lvl == logging.DEBUG:
        fmt = '%(levelname)s [%(filename)s:%(funcName)s:%(lineno)s] %(message)s'
        os.makedirs( 'LOGS', mode=700, exist_ok=True )
        os.makedirs( 'LOGS.DUO', mode=700, exist_ok=True )
    logging.basicConfig( level=log_lvl, format=fmt )
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
    run( args )
