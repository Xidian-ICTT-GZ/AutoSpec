/*@
requires (x == 100);
*/
void foo(int x) { 
  // loop body
  while (x > 0) {
    x  = x - 1;
  }
  // post-condition
  //@ assert(x == 0);
}
