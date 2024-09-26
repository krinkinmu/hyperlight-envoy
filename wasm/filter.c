#include <stdint.h>

int32_t write(void *data, int32_t size);

__attribute__((export_name("onData")))
int32_t onData(void *data, int32_t size)
{
    return write(data, size);
}
