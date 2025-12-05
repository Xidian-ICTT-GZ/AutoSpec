#include <stdlib.h>

int sum(int n) {
    int s = 0;
    int k = 0;

    while(k <= n) {    
        s = s + k;
        k = k + 1;
    }
    return s;
}

int main() {
    int s = sum(5);
    //@ assert s == 15;
}