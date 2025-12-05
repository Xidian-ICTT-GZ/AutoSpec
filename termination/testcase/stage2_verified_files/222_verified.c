void bubbleSort(int *a, int n) {
    if (n <= 0) {return;}
    int i, j, temp;

    /*@
    loop invariant 0 <= i < n;
    loop invariant \forall integer k; i <= k < n-1 ==> a[k] <= a[k+1];
    loop invariant \forall integer k; 0 <= k < i+1 <= n-1 ==> a[k] <= a[i+1];
    loop assigns temp;
    loop assigns j;
    loop assigns i;
    loop assigns a[0..n-1];
    loop variant i;
    */for(i=n-1; i>0; i--) {
        /*@
        loop invariant 0 <= j <= i < n;
        loop invariant \forall integer k; 0 <= k <= j ==> a[k] <= a[j];
        loop invariant \forall integer k; 0 <= k < i+1 <= n-1 ==> a[k] <= a[i+1];
        loop invariant \forall integer k; 0 <= k <= j ==> a[k] <= a[j];
        loop invariant \forall integer p, q; 0 <= p < i+1 == q <= n-1 ==> a[p] <= a[q];
        loop assigns temp;
        loop assigns j;
        loop assigns a[0..i];
        loop variant i - j;
        */for(j=0; j<i; j++) {
            if (a[j] > a[j+1]) {
                temp = a[j];
                a[j] = a[j+1];
                a[j+1] = temp;
            }
        }
    }
    //@ assert \forall int i; 0 <= i < n-1 ==> a[i] <= a[i+1];
}