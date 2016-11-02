#!/usr/bin/env bash

if [ ! -d ./mgen-env ]
  then
    echo "Virtual environment was not found. Running deployment first..."
    bash -c ./deploy.sh
fi

source ./mgen-env/bin/activate
export MGEN_DEBUG=1
python -m mgen.app run --debug --host=0.0.0.0 --port 8080 --public-base-uri "https://mgen-stan1y.c9users.io"