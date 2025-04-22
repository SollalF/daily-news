#!/bin/bash

set -e

virtualenv --without-pip virtualenv
#source virtualenv/bin/activate
pip install -r requirements.txt --target virtualenv/lib/python3.11/site-packages
#deactivate