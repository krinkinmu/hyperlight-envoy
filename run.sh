#!/usr/bin/env bash

pushd envoy
bazel-bin/source/exe/envoy-static -c ../config.yaml
popd
