#!/bin/bash

###
# BEGIN CUSTOMIZATIONS
###

# Uncomment to turn on debugging
DEBUG=1

# Uncomment to enable test mode (show what would be run)
#TEST=1

# Set Image Name
# (don't need docker image tag, it will be queried at runtime)
DK_USER=andylytical
DK_IMAGE=ncsa-vsl-reporter

# Set volume mount (to provide .netrc file)
# Format is 2-tuple of (local source, mount point inside container)
MOUNTPOINT=( "j:\\aloftus\\private" "/private" ) # WINDOWS
MOUNTPOINT=( "$HOME" "/private" ) # LINUX

# Set Environment Variable(s) for Container
# Possible environment vars are:
#   NETRC                ( default: ~/.netrc )
#   PYEXCH_REGEX_JSON    ( No Default, This Is Required )
NETRC=/private/.netrc
NETRC=/private/.ssh/netrc
#PYEXCH_REGEX_JSON=

###
# END OF CUSTOMIZATIONS
###

function die() {
    echo "ERR: $*"
    exit 99
}

function latest_docker_tag() {
    # Based on code from:
    # https://stackoverflow.com/questions/28320134/how-to-list-all-tags-for-a-docker-image-on-a-remote-registry
    [[ $DEBUG -eq 1 ]] && set -x
    [[ $# -ne 1 ]] && die "latest_docker_tag: must have exactly 1 parameter, got '$#'"
    image="$1"
    wget -q https://registry.hub.docker.com/v1/repositories/${image}/tags -O - \
    | sed -e 's/[][]//g' \
          -e 's/"//g' \
          -e 's/ //g' \
    | tr '}' '\n' \
    | awk -F: '{print $3}' \
    | sort -r \
    | head -1
}

[[ $DEBUG -eq 1 ]] && set -x

action=
[[ $TEST -eq 1 ]] && action=echo

# Get most recent docker image tag
DK_TAG=$( latest_docker_tag "$DK_USER/$DK_IMAGE" )
[[ -z "$DK_TAG" ]] && die "No tags found for docker image: '$DK_USER/$DK_IMAGE'"
IMAGE="$DK_USER/$DK_IMAGE:$DK_TAG"
# IMAGE="$DK_USER/$DK_IMAGE"
# IMAGE=$(docker images "$DK_IMAGE" -q | head -1)

envs=()
for v in NETRC ${!PYEXCH_*} ; do
    envs+=( '-e' "$v=${!v}" )
done

set -x
docker images -q --filter=reference="$DK_IMAGE" | xargs -r $action docker rmi -f
$action docker run \
    "${envs[@]}" \
    --mount type=bind,src="${MOUNTPOINT[0]}",dst="${MOUNTPOINT[1]}" \
    --rm -it "$IMAGE"
