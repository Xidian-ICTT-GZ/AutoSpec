void reverse(int *a, int n) {
    int i = 0;
    int j = n-1;

    while (i < n/2) {
        int temp = a[i];
        a[i] = a[j];
        a[j] = temp;
        i++;
        j--;
    }
}

// write a test
void main() {
    int arr[5] = {1, 2, 3, 4, 5};
    reverse(arr, 5);
    //@ assert arr[4] == 1;
}