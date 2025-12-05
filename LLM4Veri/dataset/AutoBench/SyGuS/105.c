/*@
requires n >= 0;
*/
void foo(int n) {
  int x = 0;
  
  while (x < n) {
    x = x + 1;
  }
  // post-condition
  if (n >= 0) {
    //@ assert(x == n);
  }
}
