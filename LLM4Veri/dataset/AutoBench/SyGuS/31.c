/*@
requires n < 0;
*/
void foo(int n) {
  int x = n;
  // loop body
  while (x > 1) {
    x  = x - 1;
  }
  // post-condition
  if (x != 1) {
    //@ assert(n < 0);
  }
}
