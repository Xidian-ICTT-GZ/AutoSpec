void foo(int y) {
  int x = 1;
  
  while (x < y) {
    x = x + x;
  }
  // post-condition
  //@ assert(x >= 1);
}
