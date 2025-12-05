/*@
requires x >= 0;
requires y >= 0;
requires x >= y;
*/
void foo(int x, int y) {
  int i = 0;

  while (unknown()) {
    if ( (i < y) )
    {
    (i  = (i + 1));
    }
  }
  // post-condition
  if (i < y) {
    //@ assert(0 <= i);
  }
}
