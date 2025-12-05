/*@
requires n > 0;
*/
void foo(int n) {
    int c = 0;

    while (unknown()) {
        if(c == n) {
            c = 1;
        }
        else {
            c = c + 1;
        }
    }

    //post-condition
    if(c == n) {
        //@ assert( c >= 0);
        ////@ assert( c <= n);
    }
}
