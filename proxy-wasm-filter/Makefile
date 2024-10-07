PROXY_WASM_CPP_SDK=/sdk
CPP_API:=${PROXY_WASM_CPP_SDK}
CPP_CONTEXT_LIB = ${CPP_API}/proxy_wasm_intrinsics.cc

all: filter.wasm

respond.pb.cc respond.pb.h: respond.intermediate ;
.INTERMEDIATE: respond.intermediate
respond.intermediate: respond.proto
	protoc respond.proto --cpp_out=.

%.wasm %.wat: %.cc ${CPP_API}/proxy_wasm_intrinsics.h ${CPP_API}/proxy_wasm_enums.h ${CPP_API}/proxy_wasm_externs.h ${CPP_API}/proxy_wasm_api.h ${CPP_API}/proxy_wasm_intrinsics.js ${CPP_CONTEXT_LIB} respond.pb.cc respond.pb.h
	em++ --no-entry -s LLD_REPORT_UNDEFINED=1 -s EXPORTED_FUNCTIONS=['_malloc'] --std=c++17 -O3 -flto -I${CPP_API} -I${CPP_API}/google/protobuf -I/usr/local/include --js-library ${CPP_API}/proxy_wasm_intrinsics.js filter.cc ${CPP_API}/proxy_wasm_intrinsics.pb.cc respond.pb.cc ${CPP_CONTEXT_LIB} ${CPP_API}/libprotobuf.a -o $*.wasm

