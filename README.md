# vsl_reporting
A tool to automate reporting personal time to NCSA's VSL calendar using data from Exchange calendar.

# Dependencies
* Python 3.x (tested with Python v3.6)

# Installation and Usage
There are two ways to use this tool: Docker and Python Virtual Environment

## Docker
1. `docker run --rm -it --name vsl-reporter andylytical/ncsa-vsl-reporter`
1. `run.sh --help`

## Python Virtual Environment
1. `git clone https://github.com/ncsa/vsl_reporting.git`
1. `cd vsl_reporting`
1. `./setup.sh`
1. `run.sh --help`
