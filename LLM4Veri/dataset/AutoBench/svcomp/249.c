// sum01_true-unreach-call_true-termination.c
int main() {
    int n;
    int i=0;
    int sn=0;
    
    for (i = 1; i <= n; i++) {
        sn = sn + (2);
    }
    
    //@ assert(sn == n * (2) || sn == 0);
    
    return 0;
}
