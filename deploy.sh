#!/usr/bin/env bash

if [ -d ./mgen-env ]
  then
    echo "Virtual environment already exists."
  else
    virtualenv ./mgen-env
fi

source ./mgen-env/bin/activate
pip3 install -r requirements.txt
python setup.py develop