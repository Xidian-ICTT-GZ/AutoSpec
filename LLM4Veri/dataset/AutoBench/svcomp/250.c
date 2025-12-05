//terminator_03_true-unreach-call_true-termination.c
int main() {
	int x;
	int y;
	if (y > 0) {
		while (x < 100) {
			x = x + y;
		}
	}
	

	//@ assert(y <= 0 || (y > 0 && x >= 100));

	return 0;
}
