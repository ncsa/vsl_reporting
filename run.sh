#!/bin/bash

# Try to use python from virtualenv if it exists, else use system version
py3=.venv/bin/python3
[[ -x "$py3" ]] || py3=$( which python3 )

# setup pythonpath
parts=( $PYTHONPATH )
for d in pyexch; do
    parts+=( $( readlink -e $d ) )
done
OIFS="$IFS"
IFS=":"; PYPATH="${parts[*]}"
IFS="$OIFS"

PYTHONPATH="$PYPATH" \
# $py3 vsl.py "$@"

export PYEXCH_REGEX_JSON='{
"SICK":"(sick|doctor|dr.appt)",
"VACATION":"(vacation|PTO|paid time off|personal day)"
}'

#$py3 vsl.py --list-overdue "$@"
$py3 vsl.py 
