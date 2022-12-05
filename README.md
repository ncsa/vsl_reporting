# vsl_reporting
A tool to automate reporting time to UIUC Engr IT VSL calendar using data from Exchange calendar.

# Quick start
## Linux
1. `curl -o go_vsl.sh https://raw.githubusercontent.com/ncsa/vsl_reporting/main/go.sh`
1. `bash ./go_vsl.sh`


## Inside Docker container
```
./vsl.py --help                   # Show cmdline help message
./vsl.py --list_self              # Show VSL entries for self
./vsl.py --list_self --auto       # Auto report VSL entries for self
./vsl.py --list_employees         # Show pending entries for employees
./vsl.py --list_employees --auto  # Auto approve pending entries for employees
```


# Environment Variables
Configuration is controlled through the following environment variables:
* NETRC
  * default: ~/.netrc
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
See: [The .netrc file format](https://everything.curl.dev/usingcurl/netrc)

### Expected Keys
* NETID
  * University of Illinois NetID login
  * Required parameters
    * login
      * format should be *ad.uillinois.edu\NETID*
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

### Sample Netrc
```
machine NETID
login ad.uillinois.edu\aloftus
password ...

machine EXCH
login aloftus@illinois.edu
account aloftus@illinois.edu
password ...
```

# See also
* https://hub.docker.com/repository/docker/andylytical/ncsa-vsl-reporter
* https://github.com/ncsa/vsl_reporting
