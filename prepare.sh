#!/usr/bin/env bash

export CARGO_REGISTRIES_HYPERLIGHT_PACKAGES_INDEX="sparse+https://pkgs.dev.azure.com/AzureContainerUpstream/hyperlight/_packaging/hyperlight_packages/Cargo/index/"
export CARGO_REGISTRIES_HYPERLIGHT_REDIST_INDEX="sparse+https://pkgs.dev.azure.com/AzureContainerUpstream/hyperlight/_packaging/redist/Cargo/index/"

# You should run the az login before calling this script. The reason
# why `az login` is not included into this script by default is because
# even if you recently logged in and have a valid tokin that you can
# just use, `az login` will still make you go through the full 2FA.
#
# That's just not needed and it's annoying. So instead I didn't add
# `az login` to this script, so this script could be run repeatedly
# as long as `az login` was executed successfully "recently".
az account get-access-token --query "join(' ', ['Bearer', accessToken])" --output tsv | cargo login --registry hyperlight_redist
az account get-access-token --query "join(' ', ['Bearer', accessToken])" --output tsv | cargo login --registry hyperlight_packages

pushd hyperlight
cargo build
cargo build --release
popd

pushd envoy
bazel build -c opt envoy --config=docker-clang
popd

pushd wasm
docker build -t wasm-builder:latest -f Dockerfile .
docker run -v $(pwd):/tmp/host wasm-builder /opt/wasi-sdk/bin/clang \
	-O3 -z stack-size=4096 -nostdlib \
	-Wl,--initial-memory=65536 \
	-Wl,--export=__data_end \
	-Wl,--export=__heap_base,--export=malloc,--export=free,--export=__wasm_call_ctors \
	-Wl,--strip-all,--no-entry \
	-Wl,--allow-undefined \
	-o /tmp/host/filter.wasm \
    /tmp/host/filter.c
docker run -v $(pwd):/tmp/host wasm-builder /wasm-micro-runtime/wamr-compiler/build/wamrc \
    --disable-simd \
    --target=x86_64 \
    --target-abi=msvc \
    -o /tmp/host/filter.aot \
	/tmp/host/filter.wasm
popd
