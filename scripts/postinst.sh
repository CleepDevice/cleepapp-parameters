#!/bin/bash

# exit when any command fails
set -e
# keep track of the last executed command
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
# echo an error message before exiting
trap 'echo "\"${last_command}\" command failed with exit code $?."' ERR

python3 -m pip install --trusted-host pypi.org "workalendar==17.0.0" "pycountry-convert>=0.7.2,<0.8.0" "pytz==2021.3" "reverse-geocode==1.4.1" "timezonefinder==5.2.0" "tzlocal==2.1"
