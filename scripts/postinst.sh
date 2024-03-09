#!/bin/bash

# exit when any command fails
set -e
# keep track of the last executed command
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
# echo an error message before exiting
trap 'echo "\"${last_command}\" command failed with exit code $?."' ERR

# reverse-geocode has numpy dependency without version specified. Latest numpy (today 1.26) is not compatible with python3.9
# so we need to force numpy version according to this numpy compatibility matrix  https://numpy.org/neps/nep-0029-deprecation_policy.html
python3 -m pip install --trusted-host pypi.org "workalendar==17.0.0" "pycountry-convert>=0.7.2,<0.8.0" "pytz==2024.1" "reverse-geocode==1.4.1" "timezonefinder==5.2.0" "tzlocal==2.1" "numpy>=1.22,<1.23"

# numpy system dependencies
apt-get update
apt-get install libopenblas-base libatlas3-base -y
