/*@
requires x == n;
requires x != 1;
*/
void foo(int x, int n) {
  // loop body
  while (x > 1) {
    x  = x - 1;
  }
  // post-condition
  if (x != 1) {
    //@ assert(n < 1);
  }
}
