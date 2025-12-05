#include <limits.h>
/*@
    ensures 0 <= \result <= 1;
*/
int unknown_int();
int main() {
    int i,j,k;
    i = 1;
    j = 1;
    k = unknown_int();
    while (i < INT_MAX) {
	i = i + 1;
	j = j + k;
	k = k - 1;
	//@ assert(1 <= i + k && i + k <= 2 && i >= 1);
    }
    return 0;
}