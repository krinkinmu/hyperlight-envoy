#include <string>
#include <unordered_map>

#include "proxy_wasm_intrinsics.h"

#include "respond.pb.h"

class EchoContext : public Context {
public:
  explicit EchoContext(uint32_t id, RootContext* root) : Context(id, root) {}

  FilterStatus onDownstreamData(size_t data_size, bool end_of_stream) override;
};
static RegisterContextFactory
  register_EchoContext(CONTEXT_FACTORY(EchoContext));
 
FilterStatus EchoContext::onDownstreamData(
    size_t data_size, bool end_of_stream) {
  using ::envoy::source::extensions::common::wasm::RespondArguments;

  logInfo("recieved data from downstream, sending it back...");

  auto buffer = getBufferBytes(
    WasmBufferType::NetworkDownstreamData, /*start*/0, data_size);
  if (!buffer) {
    logAbort("failed to access data in the downstream buffer");
  }
  auto status = setBuffer(
    WasmBufferType::NetworkDownstreamData, 0, data_size, "");
  if (status != WasmResult::Ok) {
    logAbort("failed to drain data from the buffer");
  }

  std::string function = "respond";
  RespondArguments args;
  args.set_data(buffer->data(), buffer->size());
  std::string bytes;
  args.SerializeToString(&bytes);
  char *out = nullptr;
  size_t out_size = 0;
  auto result = proxy_call_foreign_function(
    function.data(), function.size(),
    bytes.data(), bytes.size(),
    &out, &out_size);
  if (result != WasmResult::Ok) {
    logAbort("respond call returned an error");
  }
  if (out != nullptr) {
    free(out);
  }

  return FilterStatus::StopIteration;
}

