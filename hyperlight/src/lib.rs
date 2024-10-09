use hyperlight_wasm::is_hypervisor_present as hypervisor_present;
use hyperlight_wasm::{SandboxBuilder, LoadedWasmSandbox, ParameterValue, ReturnType, ReturnValue};
use hyperlight_wasm::Result;

use std::ffi::{CStr, c_char};
use std::sync::{Arc, Mutex};
use std::slice;

trait Callback: FnMut(Vec<u8>, i32) -> Result<i32> + Send + 'static {}

impl<T: FnMut(Vec<u8>, i32) -> Result<i32> + Send + 'static> Callback for T {}

#[derive(Clone)]
struct HostFunction {
    name: String,
    callback: Arc<Mutex<Box<dyn Callback>>>,
}

#[derive(Clone)]
pub struct Builder<'a> {
    builder: SandboxBuilder<'a>,
    host_functions: Vec<HostFunction>,
    module_path: Option<String>,
}

impl<'a> Builder<'a> {
    fn new() -> Self {
       Builder {
            builder: SandboxBuilder::new(),
            host_functions: Vec::new(),
            module_path: None,
        }
    }

    fn set_module_path(&mut self, module_path: String) {
        self.module_path = Some(module_path.to_string());
    }

    fn register_host_function<F>(&mut self, name: String, f: F)
            where F: Callback {
        self.host_functions.push(HostFunction {
            name: name.to_string(),
            callback: Arc::new(Mutex::new(Box::new(f))),
        });
    }

    fn build(&self) -> LoadedWasmSandbox<'static> {
        let module_path = self.module_path.as_ref().unwrap().clone();
        let mut proto_sandbox = self.builder
            .clone()
            .with_guest_heap_size(1024*1024)
            .with_guest_stack_size(4*1024)
            .with_host_function_buffer_size(16*1024)
            .with_guest_output_buffer_size(16*1024)
            .with_guest_input_buffer_size(16*1024)
            .with_wasm_heap_size(7*1024)
            .with_wasm_stack_size(1*1024)
            .with_guest_function_call_max_execution_time_millis(65535)
            .with_guest_function_call_max_cancel_wait_millis(255)
            .build()
            .unwrap();
        for hf in &self.host_functions {
            proto_sandbox.register_host_func_2(
                &hf.name, &hf.callback).unwrap();
        }
        let wasm_sandbox = proto_sandbox.load_runtime().unwrap();

        wasm_sandbox.load_module(module_path).unwrap()
    }
}


#[no_mangle]
pub extern "C" fn is_hypervisor_present() -> bool {
    return hypervisor_present();
}

#[no_mangle]
pub extern "C" fn sandbox_builder_new() -> *mut Builder<'static> {
    return Box::into_raw(Box::new(Builder::new()));
}

#[no_mangle]
pub extern "C" fn sandbox_builder_free(builder: *mut Builder) {
    if !builder.is_null() {
        unsafe {
            drop(Box::from_raw(builder));
        }
    }
}

fn to_string(s: *const c_char) -> Option<String> {
    let cstr = unsafe { CStr::from_ptr(s) };
    cstr.to_str().map(|s| s.to_string()).ok()
}

#[no_mangle]
pub extern "C" fn sandbox_builder_set_module_path(
        builder: *mut Builder,
        module_path: *const c_char) -> u32 {
    if builder.is_null() {
        return 2;
    }

    let module_path = to_string(module_path);
    if module_path.is_none() {
        return 3;
    }

    unsafe { (*builder).set_module_path(module_path.unwrap()) };
    0
}

#[no_mangle]
pub extern "C" fn sandbox_builder_register_host_function(
        builder: *mut Builder,
        cookie: u64, 
        name: *const c_char,
        // Currently we only support a single host function type:
        //   1. takes a buffer of bytes as the input
        //   2. and returns success status
        // Additionally, as a form of context for the host function we provide
        // it a cookie passed in during registration. Basically the expectation
        // is that this cookie will contain a pointer to the filter.
        host_function: unsafe extern "C" fn(u64, *mut u8, u64) -> i32) -> u32 {
    if builder.is_null() {
        return 4;
    }

    let name = to_string(name);
    if name.is_none() {
        return 5;
    }

    let callback = move |mut a: Vec<u8>, _len: i32| -> Result<i32> {
        let status = unsafe {
            (host_function)(cookie, a.as_mut_ptr(), a.len() as u64)
        };
        Ok(status)
    };

    unsafe { (*builder).register_host_function(name.unwrap(), callback) };
    0
}

#[no_mangle]
pub extern "C" fn sandbox_builder_build(
        builder: *mut Builder,
        sandbox: *mut *mut LoadedWasmSandbox<'static>) -> u32 {
    if builder.is_null() {
        return 6;
    }


    unsafe {
        *sandbox = std::ptr::null_mut();
        *sandbox = Box::into_raw(Box::new((*builder).build()));
    }
    0
}

#[no_mangle]
pub extern "C" fn sandbox_run(
        sandbox: *mut LoadedWasmSandbox,
        data: *const u8,
        size: u64) -> i32 {
    if sandbox.is_null() || data.is_null() {
        return 7;
    }

    unsafe {
        let v = slice::from_raw_parts(data, size as usize).to_vec();
        if let ReturnValue::Int(result) = (*sandbox).call_guest_function(
                "onData",
                Some(vec![ParameterValue::VecBytes(v), ParameterValue::Int(size as i32)]),
                ReturnType::Int).unwrap() {
            result
        } else {
            8
        }
    }
}

#[no_mangle]
pub extern "C" fn sandbox_free(sandbox: *mut LoadedWasmSandbox) {
    if !sandbox.is_null() {
        unsafe {
            drop(Box::from_raw(sandbox));
        }
    }
}
