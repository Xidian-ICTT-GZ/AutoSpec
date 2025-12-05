/*@
requires n > 0;
*/
void foo(int n)
{
    int x = 0;
    int m = 0;

    while (x < n) {
        if (unknown()) {
            m = x;
        }
        x = x + 1;
    }

    //post-condition
    if(n > 0) {
       ////@ assert (m < n);
       //@ assert (m >= 0);
    }
}
