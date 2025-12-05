void func(int *a, int n) {
    for (int i = 0; i < n; i++) {
        if (i%2==0) 
            a[i] = 0;
    }
}

// write a test
void main() {
    int arr[5] = {1, 2, 3, 4, 5};
    func(arr, 5);
    //@ assert arr[0] == 0;
    //@ assert arr[2] == 0;
    //@ assert arr[4] == 0;
}