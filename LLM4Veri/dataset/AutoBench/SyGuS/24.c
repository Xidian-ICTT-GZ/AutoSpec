/*@
requires i == 1;
requires j == 10;
*/
void foo(int i, int j) {
  // loop body
  while (j >= i) {
    i  = i + 2;
    j  = j - 1;
  }
  // post-condition
  //@ assert(j == 6);
}
