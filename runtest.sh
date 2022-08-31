#!/bin/bash

[[ -f /tmp/firstrun ]] || {
  pip install --upgrade pip
  pip install -r requirements.txt
  touch /tmp/firstrun
  apt update && apt -y install vim less
}


export NETRC=/home/.ssh/netrc
export OAUTH_CONFIG_FILE='/home/.ssh/exchange_oauth.yaml'
export OAUTH_TOKEN_FILE='/home/.ssh/exchange_token'
export PYEXCH_REGEX_JSON='{"SICK":"(sick|doctor|dr.appt)","VACATION":"(vacation|PTO|paid time off|personal day)"}'

./run.sh "$@"
