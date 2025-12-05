#include <assert.h>

/*
 * "nested4.c" from InvGen benchmark suite
 */

/*@
requires l > 0;
requires n > l;
*/
void foo(int n, int l) {
  int i,k;


  for (k=1; k<n; k++){
    for (i=l; i<n; i++) {
    }
    for (i=l; i<n; i++) {
      //@ assert(1<=i);
    }
  }

}
