#!/bin/bash
py3=$( which python3 )
if [[ -z "$py3" ]] ; then
    echo "Python3 Required"
    exit 1
fi
$py3 -m venv env
./env/bin/pip install -r requirements.txt

# Update git submodules
git submodule update --init
