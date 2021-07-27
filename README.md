# vsl_reporting
A tool to automate reporting time to UIUC Engr IT VSL calendar using data from Exchange calendar.

# Dependencies
* Python >= 3.9

# Installation and Usage

## Pre-built Docker Image
See: ...

## Build the Docker Image locally
1. git clone https://github.com/ncsa/vsl_reporting

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
    * `PYEXCH_REGEX_JSON='{"SICK":"(sick|doctor|dr. appt)","VACATION":"(vacation|PTO|paid time off|personal day)"}'`
  * Additional valid keys
    * SICK
      * rounded to nearest half-day
    * VACATION
      * rounded to nearest half-day
    * FLOATINGHOLIDAY
      * rounded to nearest full day

# Format of **.netrc** file
Netrc file should follow standard formatting rules.

## Expected Keys
* NETID
  * University of Illinois NetID login
  * Required parameters
    * login
    * password
* EXCH
  * Used by [pyexch](https://github.com/andylytical/pyexch) to access Exchange calendar
  * These are likely the same as above, but the format is different
  * Required parameters
    * login
      * format should be *user@domain*
    * account
      * format should be *user@domain*
    * password

## Sample Netrc
```
machine NETID
login mynetid
password mynetidpassword

machine EXCH
login myexchusername@illinois.edu
password myexchpasswd
account myexchusername@illinois.edu
```
