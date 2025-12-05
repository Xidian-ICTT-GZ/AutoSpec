// from x509-parser
// https://github.com/ANSSI-FR/x509-parser/blob/6f3bae3c52989180df6af46da1acb0329315b82a/src/x509-common.c#L7231-L7279

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t	  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;

#define X509_FILE_NUM 0 /* See x509-utils.h for rationale */

#define X509_FILE_LINE_NUM_ERR ((X509_FILE_NUM * 100000) + __LINE__)

#define MAX_UINT32 (0xffffffffUL)
#define ASN1_MAX_BUFFER_SIZE (MAX_UINT32)

int bufs_differ(const u8 *b1, const u8 *b2, u32 n)
{
	int ret = 0;
	u32 i = 0;

	for (i = 0; i < n; i++) {
		if(b1[i] != b2[i]) {
			ret = 1;
			break;
		}
	}

	return ret;
}

static const u8 null_encoded_val[] = { 0x05, 0x00 };

/*
 * Implements a function for parsing ASN1. NULL object. On success, the function
 * returns 0 and set 'parsed' parameters to the amount of bytes parsed (i.e. 2).
 * -1 is returned on error.
 */

int parse_null(const u8 *buf, u32 len, u32 *parsed)
{
	int ret;

	if ((len == 0) || (buf == NULL) || (parsed == NULL)) {
		ret = -X509_FILE_LINE_NUM_ERR;
		//ERROR_TRACE_APPEND(X509_FILE_LINE_NUM_ERR);
		goto out;
	}

	if (len != sizeof(null_encoded_val)) {
		ret = -X509_FILE_LINE_NUM_ERR;
		//ERROR_TRACE_APPEND(X509_FILE_LINE_NUM_ERR);
		goto out;
	}

	ret = bufs_differ(buf, null_encoded_val, sizeof(null_encoded_val));
	if (ret) {
		ret = -X509_FILE_LINE_NUM_ERR;
		//ERROR_TRACE_APPEND(X509_FILE_LINE_NUM_ERR);
		goto out;
	}

	ret = 0;
	*parsed = sizeof(null_encoded_val);

out:
	return ret;
}

/*
 * Handles expected lack of optinal parameters associated with sig and pubkey
 * OID. The function also support the case where lack of parames has been
 * implemented by some software by a adding a NULL instead of nothing.
 * We define specific sig and pubky function from that one below.
 */

int parse_algoid_params_none(const u8 *cert, u32 off, u32 len)
{
	const u8 *buf = cert + off;
	u32 parsed = 0;
	int ret;

	if (cert == NULL) {
		ret = -X509_FILE_LINE_NUM_ERR;
		//ERROR_TRACE_APPEND(X509_FILE_LINE_NUM_ERR);
		goto out;
	}

	/*@ assert (len > 0) ==> \valid_read(buf + (0 .. len - 1)); */

	switch (len) {
	case 0: /* Nice ! */
		ret = 0;
		break;
	case 2: /* Null ? */
		ret = parse_null(buf, len, &parsed);
		if (ret) {
			//ERROR_TRACE_APPEND(X509_FILE_LINE_NUM_ERR);
		}
		break;
	default: /* Crap ! */
		ret = -1;
		//ERROR_TRACE_APPEND(X509_FILE_LINE_NUM_ERR);
		break;
	}

out:
	return ret;
}


int main() {
	u8 buf[2] = { 0x05, 0x00 };
	u32 len = 2;
	u32 off = 0;

	int ret = parse_algoid_params_none(buf, off, len);
	//@ assert ret == 0;

	return ret;
}