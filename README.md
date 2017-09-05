# vsl_reporting
A tool to automate reporting personal time to NCSA's VSL calendar using data from Exchange calendar.

# Dependencies
* Python 3.x (tested with Python v3.6)

# Installation and Usage
There are two ways to use this tool: Docker and Python Virtual Environment

## Docker
1. `curl -o ~/vsl_reporter_as_docker.sh https://raw.githubusercontent.com/ncsa/vsl_reporting/master/docker_run.sh`
1. Edit `~/vsl_reporter_as_docker.sh` to set evnironment variables
1. `~/vsl_reporter_as_docker.sh`
1. Inside docker container
   1. `./run.sh --help`
   1. `./run.sh --list-overdue`
   1. `./run.sh -n --exch`
   1. `./run.sh --exch`

## Python Virtual Environment
NOTE: Requires Python 3 installed in a local linux environment
1. `git clone https://github.com/ncsa/vsl_reporting.git`
1. `cd vsl_reporting`
1. `./setup.sh`
1. `run.sh --help`

# Environment Variables
Configuration is controlled through the following environment variables:
*   VSL_USER             ( default: $PYEXCH_USER )
*   VSL_PWD_FILE         ( default: $PYEXCH_PWD_FILE )
*   PYEXCH_USER          ( no default )
*   PYEXCH_PWD_FILE      ( no default )
*   PYEXCH_AD_DOMAIN     ( default: UOFI )
*   PYEXCH_EMAIL_DOMAIN  ( default: illinois.edu
*   PYEXCH_REGEX_JSON    ( default: pyexch.PyExch.DEFAULT_REGEX_MAP )
