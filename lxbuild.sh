#!/bin/bash

set -x

USER="andylytical"
IMAGE="ncsa-vsl-reporter"
TAG=$( date "+%Y%m%d" )

# BUILD IMAGE
docker build . -t $IMAGE:$TAG
docker tag $IMAGE:$TAG $USER/$IMAGE:$TAG
docker push $USER/$IMAGE:$TAG
