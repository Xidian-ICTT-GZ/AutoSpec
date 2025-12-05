#include <stdio.h>

int func(int c) {
    int x = c;
    int y = 0;

    while(x > 0) {
        x = x - 1;
        y = y + 1;
    }
    return y;
}

// write a test
void main() {
    int t = func(5);
    //@ assert t == 5;
}