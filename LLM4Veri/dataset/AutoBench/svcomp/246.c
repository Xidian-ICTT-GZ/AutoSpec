#include <limits.h>
/*@
    ensures \result >= INT_MIN && \result <= INT_MAX;
*/
int unknown_int();

int main() {
    int i,j,k,n;

    k = unknown_int();
    n = unknown_int();
    if( k == n) {
    }
    else {
        goto END;
    }

    for (i = 0; i < n; i++) {
        for (j= 2 * i; j < n; j++) {
            if( unknown_int()) {
                for (k = j; k < n; k++) {
                    //@ assert(k >= 2*i);
                }
            }
            else {
                //@ assert( k >= n );
                //@ assert( k <= n );
            }
        }
    }
END:
    return 0;
}