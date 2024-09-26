FROM ubuntu
ENV DEBIAN_FRONTEND=noninteractive
LABEL org.opencontainers.image.source https://github.com/deislabs/hyperlight-wasm
RUN apt-get update \
 && apt-get upgrade -y
RUN apt-get install -y git-all \
 && apt-get install -y  wget  \
 && apt-get install -y build-essential \
 && apt-get install -y g++-multilib \
 && apt-get install -y libgcc-9-dev \
 && apt-get install -y lib32gcc-9-dev 
RUN wget https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-20/wasi-sdk-20.0-linux.tar.gz \
 && tar xvf wasi-sdk-20.0-linux.tar.gz \
 && rm wasi-sdk-20.0-linux.tar.gz \
 && mv /wasi-sdk-20.0  /opt/wasi-sdk
RUN git clone https://github.com/bytecodealliance/wasm-micro-runtime.git
RUN apt-get install -y cmake 
RUN apt-get install -y python3 
RUN apt-get install -y python3-pip
# Work around https://peps.python.org/pep-0668/ by setting
# break-system-packages globally.
# TODO: look into using venv's but that would require updates
# in build_llvm.sh.
RUN mkdir -p ~/.config/pip \
 && echo "[global]" >> ~/.config/pip/pip.conf \
 && echo "break-system-packages = true" >> ~/.config/pip/pip.conf
RUN python3 -m pip install pip
WORKDIR /wasm-micro-runtime
RUN git checkout WAMR-1.3.0 \
 && git submodule update --init --recursive 
WORKDIR /wasm-micro-runtime/wamr-compiler 
RUN apt-get install -y ninja-build
RUN apt-get install -y ccache
RUN ./build_llvm.sh \
 && mkdir build 
WORKDIR /wasm-micro-runtime/wamr-compiler/build
RUN cmake .. \
 && make
CMD ["/bin/sh"]
