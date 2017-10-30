# vsl_reporting
A tool to automate reporting personal time to NCSA's VSL calendar using data from Exchange calendar.

# Dependencies
* Python >= 3.6

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
* NETRC
  * default: /root/.netrc
* PYEXCH_REGEX_JSON
  * default: pyexch.PyExch.DEFAULT_REGEX_MAP
  * JSON formatted [dictionary](https://www.w3resource.com/JSON/structures.php)
    with keys `SICK` and `VACATION`. For each key, the value should be a regular
    expression. The regular expression is matched against the **subject** of events
    found in exchange. Durations are extracted from matching exchange events and used
    to fill in the VSL calendar for the appropriate *vsl type* matching the
    _dictionary key_.
  * Example:
    * `PYEXCH_REGEX_JSON='{"SICK":"(sick|doctor|dr. appt)","VACATION":"(vacation|OOTO|OOO|out of the office|out of office)"}'`
  * Additional valid keys
    * SICK
      * rounded to nearest half-day
    * VACATION
      * rounded to nearest half-day
    * FLOATINGHOLIDAY
      * rounded to nearest full day
    * BEREAVEMENT
      * rounded to nearest hour
    * JURYDUTY
      * rounded to nearest hour
    * MILITARYLEAVE
      * rounded to nearest hour

# Format of **.netrc** file
Netrc file should follow standard formatting rules.

## Expected Keys
* NCSA_VSL
  * User and password to login to the NSCA VSL calendar interface
  * Required parameters
    * login
    * password
* EXCH
  * Used by [pyexch](https://github.com/andylytical/pyexch) to access Exchange calendar
  * Required parameters
    * login
      * format should be *user@domain*
    * account
      * format should be *user@domain*
    * password

## Sample Netrc
```
machine NCSA_VSL
login myvslusername
password myvslpassword

machine EXCH
login myexchusername@illinois.edu
password myexchpasswd
account myexchusername@illinois.edu
```
