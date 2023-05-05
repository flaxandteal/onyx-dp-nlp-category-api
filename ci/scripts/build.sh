#!/bin/bash -eux

pushd dp-nlp-category-api
  make build
  mkdir -p build
  cp ff_fasttext_api-*-py3-none-any.whl $cwd/build
  cp Dockerfile.concourse $cwd/build
popd
