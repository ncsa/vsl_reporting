#!/bin/bash

# Get Python
read pycmd < <( ./get_py_assert_min_version.sh 3 )
rc=$?
if [[ $rc -ne 0 ]] ; then
    echo "Fatal Error: while finding python"
    exit $rc
fi
if [[ -z "$pycmd" ]] ; then
    echo "Oops, where's python?"
    exit 99
fi

# Setup Virtual Environment
$pycmd -m venv env
./env/bin/pip install -r requirements.txt

# Update Git Submodules
git submodule update --init
