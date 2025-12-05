/*@
	requires n >= 0;
*/
void foo(int n){
	int x = n;
	int y = 0;

	while (x > 0) {
		x--;
		y++;
	}

	//@ assert(y == n);
}
