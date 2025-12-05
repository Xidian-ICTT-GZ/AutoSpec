verification_gen_loop_inv = """\
ACSL is a specification language for C programs that conforms to the design by contract paradigm, utilizing Hoare style pre- and postconditions and invariants.\
You are an expert in program verification, and please generate loop invariant as C annotation comments at the infill location (annotated by "/* @ >>> INFILL <<< */") using ACSL language.\
Note that the `loop invariant` clause is a condition that is true at the beginning and end of every loop iteration.\
The `loop assign` is a condition that describes the set of variables modified by the loop.\
Just show me the loop invariant and don't explain it.
"""


gen_loop_example_1_question = """\
#include <stdlib.h>

static void mbedtls_zeroize(void *v, size_t n, int q, int w) {

  char *p = v;
  int x = 1;
  int y = 1;
  int a = q;
  int b = w;
  /* @ >>> INFILL <<< */
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


gen_loop_example_1_answer = """\
loop invariant 0 <= i <= n;
loop invariant x == y; 
loop invariant x >= 1;
loop invariant y >= 1;
loop invariant a - b == q - w;
loop invariant \\forall integer j; 0 <= j < i ==> ((char*)p)[j] == 0;
loop assigns ((char*)p)[0..n-1];
loop assigns i;
loop assigns a;
loop assigns b;
loop assigns x;
loop assigns y;
"""


gen_loop_example_2_question = """\
int arraymax(int* a, int* b, int n) {
  int i = 0;
  int max = a[0];
  int j = n;
  int k = n;

  /* @ >>> INFILL <<< */
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


gen_loop_example_2_answer = """\
loop invariant 0 <= i <= n;
loop invariant \\forall integer k;  0 <= k < i ==> max >=  a[k];
loop invariant \\exists integer k;  0 <= k < i &&  max == a[k];
loop invariant \\forall integer k; p <= k < n ==> b[k] == k;
loop invariant \\forall integer k; 0 <= k < i ==> b[k] == 2*k;
loop invariant j == k;
loop assigns i;
loop assigns max;
loop assigns a[0..n-1];
"""


gen_loop_example_3_question = """\
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define SIZE 10

int foo(uint32_t *map, uint32_t *key, uint32_t len)
{
    int ret = -1;
    int x = 1;
    int y = 0;
    /* @ >>> INFILL <<< */
    for (int i = 0; i < len; i++)
	  {
		    if (map[i] == key[i])
		    {
			      ret = 0;
			      break;
		    }
        x = x + y;
        y = y + 1;
	  }
    //@ assert (x >= y) ;
	  return ret;
}
"""


gen_loop_example_3_answer = """\
loop invariant 0 <= i <= len;
loop invariant ret == -1 || ret == 0;
loop invariant ret == -1 ==> \\forall integer j; 0 <= j < i ==> map[j] != key[j];
loop invariant ret == 0 ==> (\\exists integer j; 0 <= j < i && map[j] == key[j]);
loop invariant y <= x;
loop invariant 1 <= x;
loop invariant 0 <= y;
loop assigns i;
loop assigns y;
loop assigns x;
"""