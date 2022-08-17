# vsl_reporting
A tool to automate reporting time to UIUC Engr IT VSL calendar using data from Exchange calendar.

# Quick start
## Linux
```
latest=$(wget -q
https://registry.hub.docker.com/v1/repositories/andylytical/ncsa-vsl-reporter/tags
-O -  | sed -e 's/[][]//g' -e 's/"//g' -e 's/ //g' | tr '}' '\n' | awk -F:
'{print $3}' | sort -V )
docker run --rm -it --pull always \
--mount type=bind,src=$HOME,dst=/home \
-e NETRC=/home/.ssh/netrc \
-e PYEXCH_REGEX_JSON='{"SICK":"(sick|doctor|dr.appt)","VACATION":"(vacation|PTO|paid time off|personal day)"}' \
andylytical/ncsa-vsl-reporter:main
```

## Windows (via [Git Bash](https://gitforwindows.org/))
Same as Linux instructions, above.

## Windows (via Powershell)
NOTE: Not tested anymore. YMMV
```
docker run --rm -it --pull always `
--mount type=bind,src=e:\aloftus\private,dst=/private `
-e NETRC=/private/.netrc `
-e PYEXCH_REGEX_JSON='{"SICK":"(sick|doctor|dr.appt)","VACATION":"(vacation|PTO|paid time off|personal day)"}' `
andylytical/ncsa-vsl-reporter:main
```

## Inside Docker container
```
./run.sh --help                   # Show cmdline help message
./run.sh --list_self              # Show VSL entries for self
./run.sh --list_self --auto       # Auto report VSL entries for self
./run.sh --list_employees         # Show pending entries for employees
./run.sh --list_employees --auto  # Auto approve pending entries for employees
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
