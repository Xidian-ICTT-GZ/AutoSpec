#ifndef X509_COMMON_H
#define X509_COMMON_H

#include <stdint.h>
#include <stddef.h> // for NULL

typedef uint8_t  u8;
typedef uint32_t u32;

#define X509_FILE_NUM 1
#define X509_FILE_LINE_NUM_ERR ((X509_FILE_NUM * 100000))


int check_ia5_string(const u8 *buf, u32 len);

#endif
