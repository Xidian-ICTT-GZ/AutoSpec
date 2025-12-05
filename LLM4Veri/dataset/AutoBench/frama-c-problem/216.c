void increment_array_by(int* arr, int n, int c) {
    for (int  i = 0; i < n; i++) {
        arr[i] = arr[i] + c;
    }
}

// write a test to call increment_array_by with a small array and a small constant
// and check that the array is incremented by the constant
void main() {
    int arr[5] = {1, 2, 3, 4, 5};
    increment_array_by(arr, 5, 2);
    //@ assert arr[0] == 3;
    //@ assert arr[1] == 4;
    //@ assert arr[2] == 5;
    //@ assert arr[3] == 6;
    //@ assert arr[4] == 7;
}