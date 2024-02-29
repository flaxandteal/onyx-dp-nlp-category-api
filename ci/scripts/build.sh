#!/bin/bash -eux

cwd=$(pwd)

pushd dp-nlp-category-api
  make build-bin
  mv dist/ $cwd/build
  mv test_data $cwd/build
  cp gunicorn_config.py $cwd/build
  cp Dockerfile.concourse $cwd/build
popd
