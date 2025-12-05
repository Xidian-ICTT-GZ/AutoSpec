#include "x509_utils.h"

int main(void) {
    u8 buf[5];
    u32 len = 5;

    int ret = check_ia5_string(buf, len);

    //@ assert ret == 0 ==> \forall integer i; 0 <= i < len ==> (buf[i] <= 0x7f); 
    //@ assert ret == -X509_FILE_LINE_NUM_ERR ==> \exists integer i; 0 <= i < len && buf[i] > 0x7f;

    return ret;
}
