# vsl_reporting
A tool to automate reporting time to UIUC Engr IT VSL calendar using data from Exchange calendar.

# Quick start
## Linux
```
docker run --rm -it \
--mount type=bind,src=$HOME,dst=/home \
-e NETRC=/home/.ssh/netrc \
-e PYEXCH_REGEX_JSON='{"SICK":"(sick|doctor|dr.appt)","VACATION":"(vacation|PTO|paid time off|personal day)"}' \
andylytical/ncsa-vsl-reporter:v3.0.1
```

## Windows (via Powershell)
```
docker run --rm -it `
--mount type=bind,src=e:\aloftus\private,dst=/private `
-e NETRC=/private/.netrc `
-e PYEXCH_REGEX_JSON='{"SICK":"(sick|doctor|dr.appt)","VACATION":"(vacation|PTO|paid time off|personal day)"}' `
andylytical/ncsa-vsl-reporter:v3.0.1
```

## Inside Docker container
```
./run.sh --help                   # Show cmdline help message
./run.sh --list-sel               # Show VSL entries for self
./run.sh --list-self --auto       # Auto report VSL entries for self
./run.sh --list-employees         # Show pending entries for employees
./run.sh --list-employees --auto  # Auto approve pending entries for employees
```


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
See: [The .netrc file format](https://everything.curl.dev/usingcurl/netrc)

### Expected Keys
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

### Sample Netrc
```
machine NETID
login mynetid
password mynetidpassword

machine EXCH
login mynetid@illinois.edu
password mynetidpassword
account mynetid@illinois.edu
```

# See also
* https://hub.docker.com/repository/docker/andylytical/ncsa-vsl-reporter
* https://github.com/ncsa/vsl_reporting
