#!/bin/bash

# Uncomment to turn on debugging
DEBUG=1

# Uncomment to enable test mode (show what would be run)
TEST=1

# Set Image Name
IMAGE="andylytical/ncsa-vsl-reporter:20171028"

# Set volume mount (to provide .netrc file)
# Format is 2-tuple of (local source, mount point inside container)
MOUNTPOINT=( "j:\\aloftus\\private" "/private" )

# Set Environment Variable(s) for Container
# Possible environment vars are:
#   NETRC                ( default: ~/.netrc )
#   PYEXCH_REGEX_JSON    ( default: pyexch.PyExch.DEFAULT_REGEX_MAP )
NETRC=/private/.netrc
#PYEXCH_REGEX_JSON=

###
# END OF CUSTOMIZATIONS
###

[[ $DEBUG -eq 1 ]] && set -x

action=
[[ $TEST -eq 1 ]] && action=echo

envs=()
for v in NETRC ${!PYEXCH_*} ; do
    envs+=( '-e' "$v=${!v}" )
done

$action docker run \
    "${envs[@]}" \
    --mount type=bind,src="${MOUNTPOINT[0]}",dst="${MOUNTPOINT[1]}" \
    --rm -it "$IMAGE"
