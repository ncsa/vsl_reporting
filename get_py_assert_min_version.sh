#!/bin/bash

# Min Allowed Python Version
[[ $# -ne 1 ]] && {
    echo "Min version param required"
    exit 99
}
min_allowed_version=$1

# Find max python version available
max_py_version=0
max_py_path=
for p in python3 python ; do
    py=$( which $p )
    if [[ -n "$py" ]] ; then
        py_major_version=$( $py -c 'import sys; print(sys.version_info[0])' )
        if [[ $py_major_version -gt $max_py_version ]] ; then
            max_py_version=$py_major_version
            max_py_path=$py
        fi
    fi
done

# Check for python > min
if [[ $max_py_version -lt $min_allowed_version ]] ; then
    echo "Fatal Error: Python version $min_allowed_version required"
    exit 99
fi

# Check python found
if [[ -z "$max_py_path" ]] ; then
    echo "Fatal Error: Python not found"
    exit 99
fi

echo $max_py_path
