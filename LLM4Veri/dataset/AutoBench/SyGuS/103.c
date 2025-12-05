int main() {
  int x = 0;
  
  while (x < 100) {
    x = x + 1;
  }
  // post-condition
  //@ assert(x == 100);
}