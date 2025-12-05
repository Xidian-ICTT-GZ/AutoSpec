// hhk2008_true-unreach-call.c
int main() {
    int a;
    int b;
    
    int res, cnt;

    res = a;
    cnt = b;
    
    while (cnt > 0) {
    	cnt = cnt - 1;
        res = res + 1;
    }

    //@ assert(res == a + b);
    
    return 0;
}
