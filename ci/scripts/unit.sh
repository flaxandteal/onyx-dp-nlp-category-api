#!/bin/bash -eux

pushd dp-nlp-category-api
  make test-unit
popd
