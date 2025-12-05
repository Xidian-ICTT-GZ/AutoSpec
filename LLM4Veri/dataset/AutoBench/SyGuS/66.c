
int main() {
    int x = 1;
    int y = 0;

    while (x <= 100) {
        y = 100 - x;
        x = x +1;
    }

    //post-condition
    ////@ assert (y >= 0);
    //@ assert (y < 100);
}
