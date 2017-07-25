#!/bin/bash

# setup pythonpath
parts=( $PYTHONPATH )
for d in pyexch; do
    parts+=( $( readlink -e $d ) )
done
OIFS="$IFS"
IFS=":"; PYPATH="${parts[*]}"
IFS="$OIFS"

PYTHONPATH="$PYPATH" \
PYEXCH_AD_DOMAIN=UOFI \
PYEXCH_EMAIL_DOMAIN=illinois.edu \
./env/bin/python3 vsl.py "$@"
