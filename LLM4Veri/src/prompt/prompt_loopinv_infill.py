verification_infill_loop_inv = """\
You are an expert in program verification, and please generate loop invariant as C annotation comments at the infill location (annotated by ">>> INFILL <<<") using ACSL language.\
Note that the `loop invariant` clause is a condition that is true at the beginning and end of every loop iteration.\
I aim to generate a wider range of diverse loop invariants that differ from the ones already provided in the code.\
There are some annotations present below the infill location. Please provide additional annotations that differ from the existing ones.\

Attempt to utilize these formulas template to infer invariants for each variable, if applicable. For instance:
```
loop invariant 1 <= x;
loop invariant x == y;
loop invariant w == 2*x;
loop invariant 0 < x == > y <= z;
loop invariant z % 2 == 1 || x == y;
loop invariant 1 <= x || 1 <= y; 
loop invariant z % 2 == 1 && x <= y;
loop invariant w == 2 * y;
loop invariant c == (i*(i-1))/2;
loop invariant \\forall integer k;  0 <= k < i ==> max >=  a[k];
loop invariant \\exists integer k;  0 <= k < i &&  max == a[k];
loop invariant ret == 1 ==> \\forall integer k; 0<= k < BYTE_COUNT ==> ( k < j ==> a[k] == b[k] ); 
loop invariant ret == 0 ==>  a[j] != b[j];
loop invariant \\separated(dest + (0..i-1), src + (0..count-1));
```

Just show me the loop invariant and don't explain it.
"""


infill_loop_example_1_question = """\
#include <stdlib.h>

static void mbedtls_zeroize(void *v, size_t n, int q, int w) {

  char *p = v;
  int x = 1;
  int y = 1;
  int a = q;
  int b = w;
  /*@
  >>> INFILL <<<
  loop invariant 0 <= i <= n;
  loop assigns i;
  loop assigns a;
  loop assigns b;
  loop assigns x;
  loop assigns y;
  */
  for(int i=0; i<n ; i++) {
    p[i] = 0;
    
    int t1 = x;
    int t2 = y;
    x = t1 + t2;
    y = t1 + t2;

    a--;
    b--;
  }
}
"""


infill_loop_example_1_answer = """\
loop invariant x == y; 
loop invariant x >= 1;
loop invariant y >= 1;
loop invariant a - b == q - w;
loop invariant \\forall integer j; 0 <= j < i ==> ((char*)p)[j] == 0;
loop assigns ((char*)p)[0..n-1];
"""


infill_loop_example_2_question = """\
int arraymax(int* a, int* b, int n) {
  int i = 0;
  int max = a[0];
  int j = n;
  int k = n;

  /*@
  >>> INFILL <<<
  loop assigns i;
  loop assigns max;
  loop assigns a[0..n-1];
  */
  while (i < n) {
    b[i] = b[i] * 2;

    if (max < a[i])
      max = a[i];
    i = i + 1;

    j--;
    k--;
  }
  return max;
}
"""

infill_loop_example_2_answer = """\
loop invariant 0 <= i <= n;
loop invariant \\forall integer k;  0 <= k < i ==> max >=  a[k];
loop invariant \\exists integer k;  0 <= k < i &&  max == a[k];
loop invariant \\forall integer k; p <= k < n ==> b[k] == k;
loop invariant \\forall integer k; 0 <= k < i ==> b[k] == 2*k;
loop invariant j == k;
"""


infill_loop_example_3_question = """\
int fun(int n) {
    int i = 7;
    int x = 1;

    /*@
    >>> INFILL <<<
    loop assigns i, x;
    */
    while(i <= n) {
        x += 1;
        i += 3;
    }
    return x;
}
int main() {
    int a = fun(10);
    //@ assert a == 3;
}
"""


infill_loop_example_3_answer = """\
loop invariant i == 4 + 3*x;
loop invariant i <= n +3;
"""


infill_loop_example_4_question = """\
typedef unsigned int U32;

#define ONE_BYTE 16
#define BYTE_COUNT 1

int isMatch(const U32 *pTmpbits, const U32 *bits)
{
    int ret = 1;

    /*@
    >>> INFILL <<<
    loop invariant 0 <= j <= BYTE_COUNT;
    loop invariant ret == 1 || ret == 0;
    loop assigns j;
    */
    for (int j = 0; j < BYTE_COUNT; ++j) 
    {
        if (pTmpbits[j] != bits[j])
        {
            ret = 0;
            break;
        }
    }
    return ret;
}
"""


infill_loop_example_4_answer = """\
loop invariant ret == 1 ==> \\forall integer k; 0<= k < BYTE_COUNT ==> ( k < j ==> pTmpbits[k] == bits[k] ); 
loop invariant ret == 0 ==>  pTmpbits[j] != bits[j];
"""


infill_loop_example_5_question = """\
#include <assert.h>
int unknown();

int main()
{
	int i = 1;
	int j = 0;
	int z = i - j;
	int x = 0;
	int y = 0;
	int w = 0;

  /*@
  >>> INFILL <<<
  loop assigns x;
  loop assigns y;
  loop assigns w;
  loop assigns z;
  */
	while(unknown()) 
	{
		z += x + y + w;
		y++;
		if (z % 2 == 1) 
		  x++;
		w += 2; 
	}

	// @ assert x==y;
}
"""


infill_loop_example_5_answer = """\
loop invariant x == y;
loop invariant z % 2 == 1;
loop invariant w == 2*y;
loop invariant 0 <= y <= x;
"""


infill_loop_example_6_question = """\
void Order(int *a, int n) {
    if (n <= 0) {return;}
    int i, j, temp;

    /* @ 
    >>> INFILL <<< 
    loop assigns temp;
    loop assigns j;
    loop assigns i;
    loop assigns a[0..n-1];
    */
    for(i = n-1; i > 0; i--) {
        /*@
        loop invariant 0 <= j <= i < n;
        loop invariant \\forall integer k; 0 <= k <= j ==> a[k] <= a[j];
        loop invariant \\forall integer k; 0 <= k < i+1 <= n-1 ==> a[k] <= a[i+1];
        loop invariant \\forall integer k; 0 <= k < i+1 <= n-1 ==> a[k] <= a[i+1];
        loop assigns temp;
        loop assigns j;
        loop assigns a[0..i];
        */
        for(j=0; j<i; j++) {
            if (a[j] > a[j+1]) {
                temp = a[j];
                a[j] = a[j+1];
                a[j+1] = temp;
            }
        }
    }
}

void main() {
    int a[5] = {10, 9, 8, 7, 6};
    Order(a, 5);
    //@ assert \\forall int i; 0 <= i < 4 ==> a[i] <= a[i+1];
}
"""

infill_loop_example_6_answer = """\
loop invariant 0 <= i < n;
loop invariant 0 <= i;
loop invariant i < n;
loop invariant \\forall integer k; 0 <= k < i+1 <= n-1 ==> a[k] <= a[i+1];
loop invariant \\forall integer k; 0 <= k < i+1 <= n-1 ==> a[k] <= a[i+1];
loop invariant \\forall integer k; 0 <= k < i+1 <= n-1 ==> a[k] <= a[i+1];
loop invariant \\forall integer k; i <= k < n-1 ==> a[k] <= a[k+1];
loop invariant \\forall integer k; i <= k < n-1 ==> a[k] <= a[k+1];
"""


infill_outter_loop_1_question = """\
#include <stdint.h>
#include <stddef.h>

int sep(char* dest, const char* src, size_t count) {
    /*@
    >>> INFILL <<<
    loop assigns i;
    */
    for (size_t i = 0; i < count; ++i) {
        /*@
        loop invariant 0 <= j <= count;
        loop invariant \\separated(dest + i, src + (0..j-1));
        loop assigns j;
        */
        for (size_t j = 0; j < count; ++j) {
            if (dest + i == (char*)(src+j)) return 0;
        }
    }
    return 1;
}
"""


infill_outter_loop_1_answer = """\
loop invariant 0 <= i <= count;
loop invariant \\separated(dest + (0..i-1), src + (0..count-1));
"""


infill_outter_loop_2_question = """\
#include <limits.h>

int test(const char*s, unsigned int len) {
	int ret = 0;
	unsigned int i, j;
	char c[2] = {'<','>'};
    
  /*@
  >>> INFILL <<<
  loop invariant 0 <= i <= len;
  loop assigns i;
  loop assigns j;
  loop assigns ret;
  */
	for(i = 0; i < len; i++) {
		/*@
    loop invariant 0 <= j <= 2;
    loop invariant ret == -1 || ret == 0;
    loop invariant (ret == 0) ==> \\forall integer m; 0 <= m < i ==> s[m] != '<' && s[m] != '>';
    loop invariant (ret == 0) ==> \\forall integer m; 0 <= m < j ==> s[i] != c[m];
    loop invariant (ret == -1) ==> \\exists integer m; 0 <= m <= i && (s[m] == '<' || s[m] == '>');
    loop assigns j;
    loop assigns ret;
	  */
		for(j = 0; j < 2; j++) {
			if (s[i] == c[j]) {
				ret = -1;
			}
		}
	}
	return ret;
}

int main() {
	int len = 15;
	char s1[16] = "192.168.0.1";
	int  r1     = test(s1, len);
	//@ assert r1 == 0;
	char s2[16] = "192.168.0<1";
	int  r2     = test(s2, len);
	//@ assert r2 == -1;
}
"""


infill_outter_loop_2_answer = """\
loop invariant ret == -1 || ret == 0;
loop invariant (ret == 0)  ==> \\forall integer m; 0 <= m < i ==> s[m] != '<' && s[m] != '>';
loop invariant (ret == -1) ==> \\exists integer m; 0 <= m < i && (s[m] == '<' || s[m] == '>');
"""