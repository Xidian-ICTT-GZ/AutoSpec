#include <limits.h>
/*@
    ensures \result > 0 && \result <= INT_MAX;
*/
int unknown_int();

int main() {
  int i,k,n,l;

  n = unknown_int();
  l = unknown_int();
  for (k=1;k<n;k++){
    for (i=l;i<n;i++){  
      //@ assert(1<=i);
    }
    if(unknown_int())
      l = l + 1;
  }
 }