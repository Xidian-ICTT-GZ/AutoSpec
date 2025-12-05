#include <stdio.h>

int mul(int a, int b) {
    int x = a, y = b, prod = 0;

    while(x >= 0) {
        prod = prod + y;
        x--;
    }
    return prod;
}

int main() {
    int pdt = mul(2, 5);
    //@ assert pdt == 15;
}