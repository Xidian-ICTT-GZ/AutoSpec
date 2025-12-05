verification_gen_contract = """\
ACSL is a specification language for C programs that conforms to the design by contract paradigm, utilizing Hoare style pre- and postconditions and invariants.\
You are an expert in program verification, and please generate function contract as C annotation comments at the infill location (annotated by "/* @ >>> INFILL <<< */") using ACSL language.\
The pre- and post-conditions of functions are written as `requires` and `ensures` clauses, respectively.\
The memory locations that can be modified within a function call can be specified with an `assigns` annotation (usually known as frame condition)\
The return value of a function can be accessed (in particular in the function's post-condition) with the `\\result` clause.
Just show me the code and don't explain it.
"""

gen_contract_example_1_question = """\
#include <limits.h>

/* @ >>> INFILL <<< */
int abs(int val) {
    if(val < 0) return -val;
    return val;
}

void foo(int a) {
    int b = abs(-42);
    //@ assert b == 42;
    int c = abs(42);
    //@ assert c == 42;
    int d = abs(a);
    int e = abs(INT_MIN);
}
"""


gen_contract_example_1_answer = """\
requires INT_MIN < val <= INT_MAX;    
ensures \\result >= 0;
ensures val >= 0 ==> \\result == val;
ensures val < 0 ==> \\result == -val;
"""


gen_contract_example_2_question = """\
/* @ >>> INFILL <<< */
void bubbleSort(int *a, int n) {
    if (n <= 0) {return;}
    int i, j, temp;

    /*@
    loop invariant 0 <= i < n;
    loop invariant \\forall integer k; i <= k < n-1 ==> a[k] <= a[k+1];
    loop invariant \\forall integer k; 0 <= k < i+1 <= n-1 ==> a[k] <= a[i+1];
    loop assigns temp;
    loop assigns j;
    loop assigns i;
    loop assigns a[0..n-1];
    */
    for(i=n-1; i>0; i--) {
        /*@
        loop invariant 0 <= j <= i < n;
        loop invariant \\forall integer k; 0 <= k <= j ==> a[k] <= a[j];
        loop invariant \\forall integer k; 0 <= k < i+1 <= n-1 ==> a[k] <= a[i+1];
        loop invariant \\forall integer k; 0 <= k <= j ==> a[k] <= a[j];
        loop invariant \\forall integer p, q; 0 <= p < i+1 == q <= n-1 ==> a[p] <= a[q];
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
"""


gen_contract_example_2_answer = """\
requires \\valid(a+(0..n-1));
requires n > 0;
ensures \\forall integer i; 0 <= i < n-1 ==> a[i] <= a[i+1];
"""


gen_contract_example_3_question = """\
#include <string.h>
#include <stdint.h>
#include <assert.h>

#define SIZE 10

/* @ >>> INFILL <<< */
int foo(uint32_t *map, uint32_t *key, uint32_t len)
{
	int ret = -1;
    /*@
    loop invariant 0 <= i <= len;
    loop invariant ret == -1 || ret == 0;
	loop invariant ret == -1 ==> \\forall integer j; 0 <= j < len ==> (j < i ==> map[j] != key[j]);
	loop invariant ret == 0 ==> map[i] == key[i];
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
    uint32_t *map = malloc(sizeof(uint32_t)*SIZE);
	uint32_t *key = malloc(sizeof(uint32_t)*SIZE);
    memset(map, 0, sizeof(uint32_t)*SIZE);
	memset(key, 0, sizeof(uint32_t)*SIZE);
    key[0] = 1;
	map[0] = 2;

    int ret;
    for (int i = 1; i < SIZE; i++) {
        ret = foo(map, key, i);
    }
    //@ assert ret == 0;
    //@ assert ret == -1;
}
"""


gen_contract_example_3_answer = """\
requires \\valid((uint32_t *)(map+(0..len-1)));
requires \\valid((uint32_t *)(key+(0..len-1)));
requires len <= SIZE;
ensures \\result == -1 ==> \\forall integer i; 0 <= i < len ==> map[i] != key[i];
ensures \\result == 0 ==> \\exists integer i; 0 <= i < len && map[i] == key[i];
assigns \\nothing;
"""


gen_contract_example_4_question = """\
#include <stdint.h>
#include <stddef.h>

/* @ >>> INFILL <<< */
int sep(char* dest, const char* src, size_t count) {
    /*@
    loop invariant 0 <= i <= count;
    loop invariant \\separated(dest + (0..i-1), src + (0..count-1));
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


gen_contract_example_4_answer = """\
ensures \\result <==> \\separated(dest + (0..count-1), src + (0..count-1));
assigns \\nothing;
"""


gen_contract_example_5_question = """\
#include <stdio.h>

/* @ >>> INFILL <<< */
int fun(int n) {
    int i = 7;
    int x = 1;

    /*@
        loop invariant i == 4 + 3*x;
        loop invariant i <= n +3;
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


gen_contract_example_5_answer = """\
requires n >= 7;
ensures \\result == (n-1)/3;
assigns \\nothing;
"""


gen_contract_example_6_question = """\
#include <stdio.h>

/* @ >>> INFILL <<< */
int func(int c) {
    int x = c;
    int y = 0;
    /*@
    loop invariant c == x + y;
	loop invariant c < 0 ==> x < 0;
	loop invariant x >= 0 || x == c;
    loop assigns x, y;
    */
    while(x > 0) {
        x = x - 1;
        y = y + 1;
    }
    return y;
}

void main() {
    int t = func(5);
    //@ assert t == 5;
    int b = func(-1);
    //@ assert b == 0;
}
"""


gen_contract_example_6_answer = """\
ensures c > 0 ==> \\result == c;
ensures c == 0 ==> \\result == 0;
ensures c < 0 ==> \\result == 0;
ensures \\result == 0 ==> c <= 0;
assigns \\nothing;
"""