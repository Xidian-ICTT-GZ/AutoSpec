#include <limits.h>
/*@
    ensures \result >= INT_MIN && \result <= INT_MAX;
*/
int unknown_int();


int __BLAST_NONDET;

int main() {
    int i,j,k,n,l,m;

    n = unknown_int();
    m = unknown_int();
    l = unknown_int();
    if(3*n<=m+l); else goto END;
    for (i=0;i<n;i++)
        for (j = 2*i;j<3*i;j++)
            for (k = i; k< j; k++)
                //@ assert( k-i <= 2*n );
END:
    return 0;
}