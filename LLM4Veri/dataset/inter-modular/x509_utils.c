#include "x509_utils.h"

static int validate_ia5_char(u8 c)
{
    if (c > 0x7f) {
        return 0; // Invalid
    }
    return 1; // Valid
}

int check_ia5_string(const u8 *buf, u32 len)
{
    int ret = 0;
    u32 i;
    if ((buf == NULL) || (len == 0)) {
        ret = -X509_FILE_LINE_NUM_ERR;
        goto out;
    }
    for (i = 0; i < len; i++) {
        if (validate_ia5_char(buf[i]) == 0) {
            ret = -X509_FILE_LINE_NUM_ERR;
            goto out;
        }
    }
    ret = 0;
out:
    return ret;
}