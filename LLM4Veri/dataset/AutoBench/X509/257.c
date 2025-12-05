// from x509-parser
// https://github.com/ANSSI-FR/x509-parser/blob/6f3bae3c52989180df6af46da1acb0329315b82a/src/x509-common.c#L2049-L2093

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t	  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;

typedef enum {
	CLASS_UNIVERSAL        = 0x00,
	CLASS_APPLICATION      = 0x01,
	CLASS_CONTEXT_SPECIFIC = 0x02,
	CLASS_PRIVATE          = 0x03
} tag_class;

typedef enum {
	ASN1_TYPE_BOOLEAN         = 0x01,
	ASN1_TYPE_INTEGER         = 0x02,
	ASN1_TYPE_BIT_STRING      = 0x03,
	ASN1_TYPE_OCTET_STRING    = 0x04,
	ASN1_TYPE_NULL            = 0x05,
	ASN1_TYPE_OID             = 0x06,
	ASN1_TYPE_ENUMERATED      = 0x0a,
	ASN1_TYPE_SEQUENCE        = 0x10,
	ASN1_TYPE_SET             = 0x11,
	ASN1_TYPE_PrintableString = 0x13,
	ASN1_TYPE_T61String       = 0x14,
	ASN1_TYPE_IA5String       = 0x16,
	ASN1_TYPE_UTCTime         = 0x17,
	ASN1_TYPE_GeneralizedTime = 0x18,
} asn1_type;

#define X509_FILE_NUM 3 /* See x509-utils.h for rationale */

#define X509_FILE_LINE_NUM_ERR ((X509_FILE_NUM * 100000) + __LINE__)


int verify_correct_time_use(u8 time_type, u16 yyyy)
{
	int ret;

	switch (time_type) {
	case ASN1_TYPE_UTCTime:
		ret = (yyyy <= 2049) ? 0 : -X509_FILE_LINE_NUM_ERR;
		break;
	case ASN1_TYPE_GeneralizedTime:
		ret = (yyyy >= 2050) ? 0 : -X509_FILE_LINE_NUM_ERR;
		break;
	default:
		ret = -1;
		break;
	}

	return ret;

}


int main() {
	u8 time_type = ASN1_TYPE_IA5String;
	u16 yyyy;

	int result = verify_correct_time_use(time_type, yyyy);
	//@ assert result == -1;

	time_type = ASN1_TYPE_UTCTime;
	result = verify_correct_time_use(time_type, yyyy);
	//@ assert result < 0 || result == 0;

	return 0;
}