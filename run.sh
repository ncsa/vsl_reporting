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
python3 vsl.py "$@"
