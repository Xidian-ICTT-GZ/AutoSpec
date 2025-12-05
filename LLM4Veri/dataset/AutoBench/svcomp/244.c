#include <limits.h>
/*@
    ensures \result >= 0 && \result <= 10;
*/
int unknown_int();

/*@
    ensures \result >= 0 && \result < 2;
*/
int unknown_int1();

int main(int argc, char* argv[]) {
  int c1 = 4000;
  int c2 = 2000;
  int c3 = 10000;
  int n, v;
  int i, k, j;

  n = unknown_int();

  k = 0;
  i = 0;
  while( i < n ) {
    i++;
    v = unknown_int1();
    if( v == 0 )
      k += c1;
    else if( v == 1 )
      k += c2;
    else
      k += c3;
  }

  j = 0;
  while( j < n ) {
    //@ assert(k > 0);
    j++;
    k--;
  }

  return 0;
}