verification_positioning_only = """\
# Task Description
As an expert in program verification, you utilize ACSL (ANSI/ISO-C Specification Language) to verify C code.\
ACSL is a specification language for C programs that conforms to the design by contract paradigm, utilizing Hoare style pre- and postconditions and invariants.\
You only need to include ACSL contract as C annotation comments in the original C program that I will provide, except for the main function.\
Just show me the code and don't explain it.
"""



verification_prompt_template = """\
# Original C Code
```
<The code I give you>
```

# C Code with ASCL Contract
```
"""


first_shot_example_question = """\
#include <stdio.h>

void incrstar (int *p)
{
    (*p)++;
}

void main()
{
    int x = 0;
    incrstar(&x);
    //@ assert x == 1;
}
"""


first_shot_example_answer = """\
#include <stdio.h>

/*@ 
    requires \\valid(p);
    assigns *p;
    ensures *p == \\old(*p) + 1;
*/
void incrstar (int *p)
{
    (*p)++;
}

void main()
{
    int x = 0;
    incrstar(&x);
    //@ assert x == 1;
}
"""


second_shot_example_question = """\
#include <stdlib.h>

int f(int n, int *p, int *q) {
    if (n > 0)
        *p = n;
    else
        *q = n;
    return n;
}

int main() {
    int a = 0;
    int b = 0;
    int ret = f(1, &a, &b);
    //@ assert a == 1;
    //@ assert ret == 1;
    ret = f(-1, &a, &b);
    //@ assert b == -1;
    //@ assert ret == -1;
    return 0;
}
"""


second_shot_example_answer = """\
#include <stdlib.h>

/*@
    requires \\valid(q);
    requires \\valid(p);
    ensures \\result == \\old(n);
    behavior p_changed:
        assumes n > 0;
        ensures *p == n;
        assigns *p;
    behavior q_changed:
        assumes n <= 0;
        ensures *q == n;
        assigns *q;
    complete behaviors p_changed, q_changed;
    disjoint behaviors p_changed, q_changed;
*/
int f(int n, int *p, int *q) {
    if (n > 0)
        *p = n;
    else
        *q = n;
    return n;
}

/*@
    ensures \\result == 0;
*/
int main() {
    int a = 0;
    int b = 0;
    int ret = f(1, &a, &b);
    //@ assert a == 1;
    //@ assert ret == 1;
    ret = f(-1, &a, &b);
    //@ assert b == -1;
    //@ assert ret == -1;
    return 0;
}
"""


third_shot_example_question = """\
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define SIZE 10

int foo(uint32_t *map, uint32_t *key, uint32_t len)
{
    int ret = -1;

    for (int i = 0; i < len; i++)
	  {
		    if (map[i] == key[i])
		    {
			      ret = 0;
			      break;
		    }
	  }
	  return ret;
}

int main()
{
    uint32_t key1[SIZE] = {0, 0};
    uint32_t map1[SIZE] = {1, 1};

    int ret = foo(map1, key1, 1);
    //@ assert ret == -1;

    ret = foo(map1, key1, 2);
    //@ assert ret == -1;

    return 0;
}
"""


third_shot_example_answer = """\
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define SIZE 10

/*@ 
    requires \\valid_read(map+(0..len-1));
    requires \\valid_read(key+(0..len-1));
    ensures \\result == -1 || \\result == 0;
    ensures \\result == -1 ==> \\forall integer i; 0 <= i < len ==> map[i] != key[i];
    ensures \\result == 0 ==> \exists integer i; 0 <= i < len && map[i] == key[i];
    assigns \\nothing;
*/
int foo(uint32_t *map, uint32_t *key, uint32_t len)
{
    int ret = -1;
    /*@
    loop invariant 0 <= i <= len;
    loop invariant ret == -1 || ret == 0;
    loop invariant ret == -1 ==> \\forall integer j; 0 <= j < i ==> map[j] != key[j];
    loop invariant ret == 0 ==> (\\exists integer j; 0 <= j < i && map[j] == key[j]);
    loop assigns i;
    */
    for (int i = 0; i < len; i++)
	  {
		    if (map[i] == key[i])
		    {
			      ret = 0;
			      break;
		    }
	  }
	  return ret;
}

int main()
{
    uint32_t key1[SIZE] = {0, 0};
    uint32_t map1[SIZE] = {1, 1};

    int ret = foo(map1, key1, 1);
    //@ assert ret == -1;

    ret = foo(map1, key1, 2);
    //@ assert ret == -1;

    return 0;
}
"""


loop_example_1_question = """\
#include <stdlib.h>

static void mbedtls_zeroize(void *v, size_t n) {

  char *p = v;
  for(int i=0; i<n ; i++)
    p[i] = 0;
}
"""


loop_example_1_answer = """\
#include <stdlib.h>
/*@ 
  requires \valid((char *)(v+(0..n-1)));
  requires n > 0;
  assigns ((char*)v)[0..n - 1];
  ensures \forall integer i; 0 <= i < n ==> ((char*)v)[i] == 0;
@*/
static void mbedtls_zeroize(void *v, size_t n) {

  char *p = v;
  /*@
    loop invariant 0 <= i <= n;
    loop invariant \forall integer j; 0 <= j < i ==> ((char*)p)[j] == 0;
    loop assigns ((char*)p)[0..n-1];
    loop assigns i;
  */
  for(int i=0; i<n ; i++)
    p[i] = 0;
}
"""


loop_example_2_question = """\
/*@ 
    requires \valid_read(a + (0..n-1));
    requires n > 0;

    ensures \forall integer k;  0 <= k < n ==> \result >=  a[k];
    ensures \exists integer k;  0 <= k < n && \result == a[k];

    assigns \nothing;
*/
int arraymax(int* a, int n) {
  int i = 1;
  int max = a[0];

  /*@ 
     loop invariant \forall integer k;  0 <= k < i ==> max >=  a[k];
     loop invariant \exists integer k;  0 <= k < i &&  max == a[k];
     loop invariant 0 <= i <= n;
     loop assigns max;
     loop assigns i;
 */
  while (i < n) {
    if (max < a[i])
      max = a[i];
    i = i + 1;
  }
  return max;
}
"""


loop_example_2_answer = """\
int arraymax(int* a, int n) {
  int i = 1;
  int max = a[0];

  while (i < n) {
    if (max < a[i])
      max = a[i];
    i = i + 1;
  }
  return max;
}
"""


verification_positioning_one_shot = """\
\
# Task Description
As an expert in program verification, you utilize ACSL language to verify C code.\
ACSL is a specification language for C programs that conforms to the design by contract paradigm, utilizing Hoare style pre- and postconditions and invariants.\
You only need to include ACSL contract as C annotation comments in the original C program that I will provide.\
Just show me the code and don't explain it.

# Original C Code
```
void incrstar (int *p) 
{
    (*p)++;
}
```

# C Code with ASCL Contract
```
/* @ 
  requires \valid(p);
  assigns *p;
  ensures *p == \old(*p) + 1;
*/
void incrstar (int *p);
{
    (*p)++;
}
```

"""


verification_positioning_detail = """\
\
# Task Description
As an expert in program verification, you utilize ACSL language to verify C code.\
ACSL is a specification language for C programs that conforms to the design by contract paradigm, utilizing Hoare style pre- and postconditions and invariants.\
You only need to include ACSL contract as C annotation comments in the original C program that I will provide.\
Just show me the code and don't explain it.

Consider the following example for the prototype of a function named incrstar.\
The contract is given by the comment which starts with /*@. Its meaning is as follows:\
the first line is a precondition: it states that function incrstar must be called with a pointer p that points to a safely allocated memory location.\
Second line is a frame clause, stating that function incrstar does not modify any memory location but the one pointed to by p.\
Finally, the ensures clause is a postcondition, which specifies that the value *p is incremented by one.

Note that:
  1. assigns \nothing
    - Says that do not assign anything to the inputs, only read them.
    - It means that we make sure that the inputs are immutable.
    - The program must not be able to change any of the inputs.
  2. \result
    - The value returned from a function
  3. \old(a)
    - If a is passed to a function
    - It has two versions. 
        - The version before passing into the array
        - The version after the function has returned
    - \old(a) fetches the value of a variable a before passing it into the array.

# Original C Code
```
void incrstar (int *p) 
{
    (*p)++;
}
```

# C Code with ASCL Contract
```
/* @ 
  requires \valid(p);
  assigns *p;
  ensures *p == \old(*p) + 1;
*/
void incrstar (int *p);
{
    (*p)++;
}
```

You only need to include ACSL contract as C annotation comments in the original C program that I will provide.\
Just show me the code and don't explain it.
"""