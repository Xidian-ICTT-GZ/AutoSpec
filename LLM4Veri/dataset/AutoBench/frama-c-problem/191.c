#include <stdio.h>

int pdt(int n) {
  int prod = 1;
  int i = 2;

  while(i < n) {
    prod = power(i/2)*factorial(i/2);
    i = i+2;
  }
  return prod;
}

int main() {
    int p = pdt(10);
    //@ assert p == 1;
}