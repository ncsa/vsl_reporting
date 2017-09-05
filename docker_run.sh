#!/bin/bash

# Uncomment to turn on debugging
DEBUG=1

# Uncomment to enable test mode (show what would be run)
#TEST=1

[[ $DEBUG -eq 1 ]] && set -x

# Set volume mounts
# Format is 2-tuple of (local source, mount point inside container)
MOUNTPOINT=( "j:\\aloftus\\private" "/private" )

# Set Image Name
IMAGE="andylytical/ncsa-vsl-reporter:20170905"


# Set Environment Vars for Container
# Possible environment vars are:
#   VSL_USER             ( default: $PYEXCH_USER )
#   VSL_PWD_FILE         ( default: $PYEXCH_PWD_FILE )
#   PYEXCH_USER          ( no default )
#   PYEXCH_PWD_FILE      ( no default )
#   PYEXCH_AD_DOMAIN     ( default: UOFI )
#   PYEXCH_EMAIL_DOMAIN  ( default: illinois.edu
#   PYEXCH_REGEX_JSON    ( default: pyexch.PyExch.DEFAULT_REGEX_MAP )
PYEXCH_USER=aloftus
PYEXCH_PWD_FILE=/private/uiuc_exchange

action=
[[ $TEST -eq 1 ]] && action=echo

envs=()
for v in ${!VSL_*} ${!PYEXCH_*} ; do
    envs+=( '-e' "$v=${!v}" )
done

$action docker run \
    "${envs[@]}" \
    --mount type=bind,src="${MOUNTPOINT[0]}",dst="${MOUNTPOINT[1]}" \
    --rm -it "$IMAGE"
