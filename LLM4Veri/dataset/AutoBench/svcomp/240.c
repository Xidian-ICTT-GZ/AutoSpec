#include <limits.h>
/*@
    ensures \result >= INT_MIN && \result <= INT_MAX;
*/
int unknown_int();

int main() {
  int n,i,k;
  n = unknown_int();
  k = n;
  i = 0;

  while( i < n ) {
    k--;
    i = i + 2;
  }

  int j = 0;
 
  while( j < n/2 ) {
    //@ assert(k > 0);
    k--;
    j++;
  }
  return 0;
}