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
popd
