# Envoy with Hyperlight PoC

This repository contains a wrapper/glue code for Hyperlight and
also a reference (as git submodule) to the Envoy repository with
a filter that runs WASM modules inside Hyperlight sandbox.

The `prepare.sh` script will build all the parts relevant for the
demo. The `run.sh` scripts starts Envoy with the echo-like
hyperlight filter in it listening on port `5678`.

Echo filter in Envoy just sends all the data it receives back to
the sender. You can test that the Hyperlight filter does the same
by, for example, connecting to it with `telnet`:

```sh
telnet 127.0.0.1 5678
```

## Prerequisites

### Docker

Docker should be installed and configured to not require super
user priveleges. You can verify that it's the case on a Linux
system by running this command:

```sh
docker run hello-world
```

If you don't have Docker installed, check out instructions for
your system in  https://docs.docker.com/engine/install.

If Docker is installed, but requires `sudo` to run, check out
instruction in
https://docs.docker.com/engine/install/linux-postinstall

### Hypervisor

Hyperlight relies on a hypervisor like KVM or Hyper-V to create
a sandbox. Thefore for the demo to work you should have one.

This particular demo was only tested with KVM, so I will provide
instructions on how to set it up for Debian-like distributions.

You can start by installing the following packages if they are
not installed already:

```sh
sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils 
```

You can then check that you can use KVM by running the following
command:

```sh
kvm-ok
```

If you can use KVM, the output should look like this:

```
INFO: /dev/kvm exists
KVM acceleration can be used
```

We also need to grant access to KVM to non-super users, so that
we don't have to run Envoy with super user privileges. It can
be done by setting appropriate permissions for the `/dev/kvm`
file.

For example, if access to KVM requires super user permissions on
your system you may try to do something like this:

```sh
# Create a group named kvm if it does not exist already.
# Commands below will setup KVM, so that members of the
# group kvm will have access to it.
groupadd -f kvm
# Add yourself to the group kvm
usermod -a -G kvm $USER
# Transfer group owenership of the /dev/kvm to the group kvm
sudo chgrp kvm /dev/kvm
sudo chmod 0660 /dev/kvm
```

> NOTE: For the changes to take effects you need to restart the
> system, so check before that if you really need to do it.

### Bazel

We need Bazel to build Envoy. Envoy documentation suggests to
install Bazelisk instead of installing Bazel directly. Refer to
the instructions in
https://github.com/envoyproxy/envoy/blob/main/bazel/README.md#installing-bazelisk-as-bazel.

## Build

Once you have all the required tools, you need to build a few
things:

1. Wrapper for Hyperlight, that's the code in the hyperlight directory
2. Envoy itself with the relevant changes
3. WASM module that will be used by Hyperlight

To do all of that in the right order run the following:

```sh
az login
bash ./prepare.sh
```

> NOTE: Some of the Hyperlight dependencies currently lives in
> private crate repositories, `az login` is used to generate
> an authorization token to access those.

`config.yaml` is an example static configuration for Envoy that
configures Hyperlight filter. To start Envoy using this
configuration run:

```sh
bash ./run.sh
```
