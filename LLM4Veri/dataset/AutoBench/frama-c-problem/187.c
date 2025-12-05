#include <stdio.h>

int fun(int n) {
    int i = 7;
    int x = 1;

    while(i <= n) {
        x += 1;
        i += 3;
    }
    return x;
}

int main() {
    int a = fun(10);
    //@ assert a == 3;
}