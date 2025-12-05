// from x509-parser
// https://github.com/ANSSI-FR/x509-parser/blob/6f3bae3c52989180df6af46da1acb0329315b82a/src/x509-common.c#L7377-L7423

#include <stdint.h>
#include <unistd.h>
#include <string.h>

typedef uint8_t	  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;

u64 time_components_to_comparable_u64(u16 na_year, u8 na_month, u8 na_day,
				      u8 na_hour, u8 na_min, u8 na_sec)
{
	u64 res, tmp;

	res = ((u64)na_sec);                        /* start with seconds */
	/*@ assert res < (1ULL << 6); */

	tmp = ((u64)na_min) * (1ULL << 8);          /* add shifted minutes */
	/*@ assert tmp < (1ULL << 14); */
	res += tmp;
	/*@ assert res < (1ULL << 15); */

	tmp = (((u64)na_hour) * (1ULL << 16));      /* add shifted hours */
	/*@ assert tmp < (1ULL << 21); */
	res += tmp;
	/*@ assert res < (1ULL << 22); */

	tmp = ((u64)na_day) * (1ULL << 24);         /* add shifted days */
	/*@ assert tmp < (1ULL << 29); */
	res += tmp;
	/*@ assert res < (1ULL << 30); */

	tmp = ((u64)na_month) * (1ULL << 32);       /* add shifted days */
	/*@ assert tmp < (1ULL << 36); */
	res += tmp;
	/*@ assert res < (1ULL << 37); */

	tmp = ((u64)na_year) * (1ULL << 40);         /* add shifted years */
	/*@ assert tmp < (1ULL << 54); */
	res += tmp;
	/*@ assert res < (1ULL << 55); */

	return res;
}


int main(void)
{
  u16 na_year = 2023; // Frama_C_unsigned_int_interval(0, 9999);
  u8 na_month = 12; // Frama_C_unsigned_int_interval(0, 12);
  u8 na_day = 20;// Frama_C_unsigned_int_interval(0, 31);
  u8 na_hour = 12; //Frama_C_unsigned_int_interval(0, 23);
  u8 na_min = 00; //Frama_C_unsigned_int_interval(0, 59);
  u8 na_sec = 00; //Frama_C_unsigned_int_interval(0, 59);
  u64 res;

  res = time_components_to_comparable_u64(na_year, na_month, na_day, na_hour, na_min, na_sec);
  //@ assert res < (1ULL << 55);
  return 0;
}